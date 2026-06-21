# A5 — Adversarial Code Review & Remediation: A3 Polyglot Fraud-Score System

> Principal-engineer / red-team review of the A3 PR (FastAPI ingestion + Node worker + Rust
> engine) **and** the close-out of every blocking defect.
> **Posture: every line is guilty until an exploit is reproduced or safety is proven by a test.**
> Date: **2026-06-21** (supersedes the 2026-06-17 v1 review).
> Scope: `fastapi-service/`, `node-worker/`, `rust-engine/`, `integration-tests/`, `CONTRACT.md`.
>
> **All Critical + High findings were reproduced live** (`artifacts/repro/`), fixed, and re-verified
> by re-running the *original* exploit against the patched code. Suites: Rust 7/7, pytest 18/18,
> Node 14/14, integration **4/4 PASS (exit 0)**.

---

## ⚠️ Correction to the v1 (2026-06-17) review

The v1 review claimed *"the 3 blocking issues were subsequently fixed in A3 and regression-tested …
end-to-end integration still 4/4 PASS."* An adversarial re-audit found that claim was **false on two
counts** — exactly the kind of overstated remediation this upgrade exists to eliminate:

| v1 claim | Reality on 2026-06-21 (reproduced) | Now |
|---|---|---|
| A5-2 "fixed: optional `X-Internal-Token`" | **Fail-OPEN** — with `A3_INTERNAL_TOKEN` unset (the default), `/internal/*` accepted *any* caller. Reproduced: forged `score=0/low` on a 999999/US/gambling txn → **HTTP 200**. | **Fail-CLOSED** in all environments (`AFTER_failclosed_default_config.txt`). |
| "end-to-end integration still 4/4 PASS" | **Broken** — `run_integration.sh` referenced `$polyglot-fraud-system`, an unbound variable under `set -u`; the script aborted on line 14 (`exit 1`) before starting anything. The E2E path was never exercised. | **4/4 PASS, exit 0** (`suites/AFTER_integration.txt`). |

The "optional token" design is itself the vulnerability (see **A5-17**): a security control that is
off by default is no control at all.

---

## Executive Summary

The A3 system is correct on the happy path (its own suites were green), but adversarial review found
**20 distinct issues across 8 attack categories**, including a **Critical arbitrary-file-write** and a
cluster of **score-integrity** defects that let an attacker neutralize the entire fraud system. This
deliverable closes the loop: **8 blocking issues fixed and re-verified, 0 open blocking issues**, plus
the High/Medium backlog either fixed-with-tests or explicitly deferred-with-tests.

| Severity | Count | Blocking | Status |
|---|---|---|---|
| Critical | 1 | 1 | ✅ fixed + verified |
| High | 8 | 7 | ✅ fixed + verified (1 deferred: A5-4) |
| Medium | 8 | 0 | 4 fixed / 4 deferred-with-rationale |
| Low | 3 | 0 | 1 fixed / 2 deferred |
| **Total** | **20** | **8** | **0 open blocking** |

**Recommendation:** the 8 blocking defects are fixed and each original exploit now fails. Ship-able
once the deferred backlog (esp. A5-4 money type) is scheduled.

---

## Attack categories covered

1. **Injection / path traversal** — A5-1
2. **AuthN / AuthZ** — A5-2, A5-17, A5-19
3. **Input validation** — A5-9, A5-15
4. **Business-logic / score integrity** — A5-13, A5-14
5. **Concurrency / races** — A5-6, A5-16
6. **Reliability / error handling** — A5-3, A5-5, A5-7, A5-8, A5-10, A5-11
7. **Financial correctness** — A5-4
8. **Contract fidelity / tooling** — A5-18, A5-20, A5-12

---

## Issue Inventory

Legend: 🔴 Critical · 🟠 High · 🟡 Medium · 🔵 Low · **[B]** blocking · **[NEW]** not in v1.

### A5-1 — Path traversal / arbitrary file write via `transaction_id` 🔴 **[B]** ✅ FIXED
* **Category:** Injection. **File:** `fastapi-service/app/queue.py`, `app/schemas.py`.
* **Exploit:** queue filename built from the client-supplied `transaction_id`; `"../A5_PWNED"` writes
  outside `QUEUE_DIR` → arbitrary file write.
* **Repro (before, v1):** `POST {"transaction_id":"../A5_PWNED"}` → 201, file at `…/A5_PWNED.json` outside `queue/`.
* **Fix:** strict `pattern=^[A-Za-z0-9_-]{1,64}$` on `TransactionIn.transaction_id` + basename + realpath
  containment assert in `enqueue()`. **Verified:** `artifacts/repro/AFTER_api_exploits.txt` → traversal id
  **422**, nothing escapes. Test `test_path_traversal_transaction_id_rejected`.

### A5-2 — Unauthenticated internal scoring endpoint (fraud bypass) 🟠 **[B]** ✅ FIXED
* **Category:** AuthZ. **File:** `fastapi-service/app/routes.py`.
* **Exploit:** `POST /internal/transactions/{id}/score` persisted an arbitrary score with no auth; any
  client could overwrite a high-risk score with `low`, defeating the fraud system.
* **Repro (before):** no `X-Internal-Token` → **HTTP 200**, victim forced to `score 0 / low`
  (`BEFORE_api_exploits.txt`).
* **Fix:** `_check_internal_auth()` requires a configured token and a matching `X-Internal-Token`.
  **Verified:** no/wrong token → **401**; correct token → 200. Tests `test_internal_score_requires_token`.
* See **A5-17** for the deeper fail-open root cause that v1 left open.

### A5-3 — Duplicate `transaction_id` → unhandled `IntegrityError` (HTTP 500) 🟠 **[B]** ✅ FIXED
* **Category:** Error handling. **File:** `app/routes.py`.
* **Exploit:** re-POST of an existing id violated the PK → uncaught `IntegrityError` → 500.
* **Fix:** idempotent pre-check returns **409**; *and* the commit is wrapped to catch the PK violation
  (see **A5-16** for the TOCTOU hardening). Test `test_duplicate_transaction_id_returns_409`.

### A5-4 — Money stored as floating point 🟠 ⏸️ DEFERRED (with test)
* **Category:** Financial correctness. **File:** `app/models.py` (`Float`), `app/schemas.py` (`float`), Rust `f64`.
* **Risk:** `0.1+0.2`-style drift; threshold edge behavior in a financial system.
* **Decision — DEFERRED:** a correct fix is integer **minor units** / `Decimal` end-to-end across three
  languages, which changes the **LOCKED** contract (`amount: number`) and the Rust engine's `f64`
  threshold. That is a contract-version bump (v1.1), not an in-place patch, so it is scheduled rather
  than rushed. **Guarded by a test** pinning the exact boundary the migration must preserve:
  `rust-engine/tests/scoring.rs::high_amount_threshold_boundary` (10000 → no `high_amount`; 10000.01 → fires).
* **Verification:** `cargo test` (7/7). Non-blocking: demo thresholds are integers.

### A5-5 — Non-atomic DB-commit-then-enqueue (lost/stuck work) 🟡 ⏸️ DEFERRED
* **Category:** Reliability. **File:** `app/routes.py`.
* **Risk:** row committed `pending`, then queue file written; a crash between leaves a permanently
  `pending`, never-scored txn with no reconciliation.
* **Decision — DEFERRED:** correct fix is an outbox/sweeper. Documented; non-blocking for single-node
  demo. Mitigation note: `enqueue()` raising now leaves a 500 to the client (visible failure) rather
  than a silent success, so the gap is observable.

### A5-6 — Worker has no queue claim → double-processing under concurrency 🟡 ⏸️ DEFERRED (mitigated)
* **Category:** Concurrency. **File:** `node-worker/src/worker.js` (`processQueueOnce`).
* **Risk:** two workers list+process the same file → duplicate engine calls + duplicate score POSTs.
* **Decision — DEFERRED but MITIGATED:** the data-corruption consequence (a duplicate POST overwriting
  a score) is now neutralized server-side by **A5-14** — a second, conflicting score is a 409 and an
  identical one is an idempotent no-op. The remaining duplicate *work* (wasted engine spawn) is a
  single-worker-today efficiency issue. Atomic `rename`-to-claim is the scheduled fix.

### A5-7 — `callEngine` has no timeout (hung engine stalls the worker) 🟡 ✅ FIXED
* **Category:** Reliability. **File:** `node-worker/src/worker.js`.
* **Risk:** a never-closing engine left the Promise pending forever, blocking the sequential loop.
* **Fix:** `ENGINE_TIMEOUT_MS` (default 5s) `SIGKILL`s the child and rejects. Test
  `A5-7: rejects (and kills child) when the engine never closes`.

### A5-8 — Transient failures silently dead-lettered, never retried 🟡 ⏸️ DEFERRED
* **Category:** Reliability/Observability. **File:** `worker.js`.
* **Risk:** a brief API outage permanently moves every in-flight txn to `failed/` with no redrive/alert.
* **Decision — DEFERRED:** needs a retryable-vs-permanent taxonomy + scheduled redrive + metric. Documented;
  non-blocking. (The Rust call already retries 3× w/ backoff per contract; only `postScore`/permanent
  paths dead-letter.)

### A5-9 — Input validation limits on transaction fields 🟡 ✅ FIXED
* **Category:** Input validation. **File:** `app/schemas.py`.
* **Fix (carried from A5-1 work):** `transaction_id` pattern; `user_id`/`merchant_category`/`timestamp`
  `max_length`; `country` `min/max_length`. Bounds storage and blocks the traversal vector. Verified by
  the path-traversal + happy-path tests. (ISO-2 strict country + amount upper-bound noted as nice-to-have.)

### A5-10 — Engine stdout parsed unbounded 🔵 ✅ FIXED
* **Category:** Robustness. **File:** `worker.js`.
* **Fix:** `MAX_OUTPUT_BYTES` (default 1 MiB) cap; exceeding it kills the child and rejects. Test
  `A5-10: rejects when engine stdout exceeds the output cap`.

### A5-11 — 500 paths not observable 🔵 ⏸️ DEFERRED (reduced)
* **Category:** Observability. **File:** `app/main.py`.
* **Status:** the headline 500 source (A5-3/A5-16) is now eliminated, so the unobservable-stack-trace
  symptom is largely gone. A dedicated structured exception handler + 5xx counter remains a documented
  nice-to-have. Non-blocking.

### A5-12 — Dependency drift risk 🔵 ⏸️ DEFERRED
* **Category:** Supply chain. **File:** `node-worker/package.json`, `requirements.txt`.
* **Status:** lockfiles exist (`package-lock.json`, `Cargo.lock`); Python has no hash lock. Documented;
  non-blocking nit.

### A5-13 — Score poisoning: out-of-range / band-inconsistent scores accepted 🟠 **[B]** ✅ FIXED **[NEW]**
* **Category:** Business-logic / score integrity. **File:** `app/routes.py`, `app/schemas.py`.
* **Exploit:** the callback persisted `payload.score` / `payload.risk_level` verbatim — `score=999`,
  `risk_level="banana"`, or `score=90 / risk_level=low` (band mismatch) were all stored.
* **Repro (before):** `POST score=999 risk_level=low` → **HTTP 200**, persisted (`BEFORE_api_exploits.txt`).
* **Fix:** server-side validation — `0 ≤ score ≤ 100` (also enforced at the Pydantic layer, `Field(ge=0,
  le=100)`), `risk_level ∈ {low,medium,high}`, and `risk_level == band(score)`; any violation → **422**.
  *Auth (A5-2) is the primary control; this is defense-in-depth against a buggy/compromised worker.*
  Tests `test_score_poisoning_out_of_range_rejected`, `…_invalid_risk_level_…`, `…_band_mismatch_…`.

### A5-14 — Callback overwrite of an already-scored transaction 🟠 **[B]** ✅ FIXED **[NEW]**
* **Category:** Business-logic / score integrity. **File:** `app/routes.py`.
* **Exploit:** an already-`scored` txn could be re-scored; a `90/high` decision was silently flipped to
  `0/low` by a second POST.
* **Repro (before):** 1st `90/high` → 200, 2nd `0/low` → **200**, GET shows `0/low` (`BEFORE_api_exploits.txt`).
* **Fix:** idempotent + overwrite-resistant — identical replay → **200 `{idempotent:true}`**; conflicting
  re-score → **409**, original score preserved. Tests `test_callback_idempotent_replay`,
  `test_callback_overwrite_rejected`.

### A5-15 — Path/body `transaction_id` mismatch silently accepted 🟡 ✅ FIXED **[NEW]**
* **Category:** Input validation / confused deputy. **File:** `app/routes.py`.
* **Exploit:** `POST /internal/transactions/realA/score` with body `transaction_id:"totally_different"`
  was accepted — the body id was ignored, scoring `realA` with mismatched data.
* **Repro (before):** → **HTTP 200** (`BEFORE_api_exploits.txt`).
* **Fix:** reject path≠body id with **422**. Test `test_score_path_body_id_mismatch_rejected`.

### A5-16 — Concurrent duplicate create → TOCTOU `IntegrityError` (HTTP 500) 🟠 **[B]** ✅ FIXED **[NEW]**
* **Category:** Concurrency / races. **File:** `app/routes.py`.
* **Exploit:** A5-3's `db.get()` pre-check is a TOCTOU window — two concurrent identical creates both
  see "not found", race to INSERT, the loser's PK violation surfaces as **500**.
* **Repro (before):** pre-check forced to miss → uncaught `IntegrityError` → **500** (`BEFORE_api_exploits.txt`).
* **Fix:** wrap `commit()` in `try/except IntegrityError` → `rollback()` → **409**. The PK constraint, not
  the pre-check, is the real guard. Test `test_concurrent_duplicate_create_no_500`.

### A5-17 — Internal auth FAIL-OPEN when `A3_INTERNAL_TOKEN` unset (v1-fix regression) 🟠 **[B]** ✅ FIXED **[NEW]**
* **Category:** AuthZ. **File:** `app/routes.py`.
* **Exploit:** v1 made the token *optional* (`if _INTERNAL_TOKEN is not None and …`). In the default
  config (no env var) the guard was skipped entirely → `/internal/*` open to anyone. This is the actual
  root cause behind A5-2 and the reason the v1 "fix" did not close the loop.
* **Repro (before):** default config, no token → forged callback **HTTP 200** (`BEFORE_api_exploits.txt`).
* **Fix:** **fail-closed** — `_check_internal_auth()` returns **503 "internal auth not configured"** when
  no server token is set, so `/internal/*` is *never* reachable without a token in any environment.
  **Verified:** `AFTER_failclosed_default_config.txt` (no token → 503). Test
  `test_internal_score_fail_closed_when_unconfigured`.

### A5-18 — Integration harness broken: unbound `$polyglot-fraud-system` 🟠 **[B]** ✅ FIXED **[NEW]**
* **Category:** Contract fidelity / tooling. **File:** `integration-tests/run_integration.sh`.
* **Defect:** lines 14/15/25/52 referenced `$polyglot-fraud-system`; the component root var is `$A3`.
  Under `set -u`, `$polyglot` is unbound → script aborts on line 14 (`exit 1`). E2E never ran — making
  the v1 "4/4 PASS" claim impossible.
* **Repro (before):** `polyglot: unbound variable; exit=1` (`BEFORE_integration.txt`).
* **Fix:** use `$A3` (resolved from `BASH_SOURCE`) and plumb a per-run `A3_INTERNAL_TOKEN` to both the API
  and the worker (required now that auth is fail-closed). **Verified:** **4/4 PASS, exit 0**
  (`suites/AFTER_integration.txt`).

### A5-19 — Timing-unsafe token comparison 🟡 ✅ FIXED **[NEW]**
* **Category:** AuthZ. **File:** `app/routes.py`.
* **Risk:** v1 used `x_internal_token != _INTERNAL_TOKEN` (`==`), a non-constant-time compare that can
  leak the secret byte-by-byte via timing.
* **Fix:** `hmac.compare_digest(...)`. Covered by `test_internal_score_requires_token` (wrong token → 401).

### A5-20 — Worker contract drift under fail-closed auth 🟡 ✅ FIXED **[NEW]**
* **Category:** Contract fidelity. **File:** `node-worker/src/worker.js`, `integration-tests/run_integration.sh`.
* **Risk:** with the API now fail-closed, a worker that doesn't send `X-Internal-Token` would have *every*
  `postScore` rejected (401) and dead-letter all work — a silent contract drift between API and worker.
* **Fix:** the worker already reads `A3_INTERNAL_TOKEN` and attaches `X-Internal-Token` when set; the
  integration harness now exports a shared token to both. **Verified end-to-end:** integration 4/4 PASS
  proves the worker authenticates successfully (`suites/AFTER_integration.txt`).

---

## Blocking issues — all closed

| ID | Title | Before | After | Test |
|---|---|---|---|---|
| A5-1 | Path traversal | file escapes `queue/` | 422 | `test_path_traversal_transaction_id_rejected` |
| A5-2/A5-17 | Internal auth fail-open | forged 200 | 401 / 503 fail-closed | `test_internal_score_requires_token`, `…_fail_closed_…` |
| A5-3 | Duplicate → 500 | 500 | 409 | `test_duplicate_transaction_id_returns_409` |
| A5-13 | Score poisoning | 999 stored | 422 | `test_score_poisoning_*`, `…_band_mismatch_…` |
| A5-14 | Callback overwrite | flipped to low | 409 / idempotent | `test_callback_overwrite_rejected`, `…_idempotent_replay` |
| A5-16 | Concurrent IntegrityError | 500 | 409 | `test_concurrent_duplicate_create_no_500` |
| A5-18 | Integration broken | exit 1 | 4/4 PASS, exit 0 | `run_integration.sh` |

## Agent-reasoned vs live-verified

* **Live-verified (reproduced before & after):** A5-1, A5-2, A5-13, A5-14, A5-15, A5-16, A5-17, A5-18
  (see `artifacts/repro/`).
* **Test-verified:** A5-3, A5-7, A5-9, A5-10, A5-19, A5-20 (unit/integration assertions).
* **Reasoned-from-code (deferred-with-rationale):** A5-4 (boundary test), A5-5, A5-6 (mitigated by A5-14),
  A5-8, A5-11, A5-12.

## Suite results (final)

```
rust    : cargo test  → 7 passed   (suites/AFTER_rust.txt)
fastapi : pytest -q   → 18 passed  (suites/AFTER_pytest.txt)
node    : npm test    → 14 passed  (suites/AFTER_node.txt)
e2e     : run_integration.sh → INTEGRATION: PASS (4/4), exit 0  (suites/AFTER_integration.txt)
```

See `docs/REMEDIATION_LOG.md` for per-fix before/after diffs+repro and `docs/TEST_MATRIX.md` for the
finding→test mapping.
