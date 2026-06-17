# A5 — Adversarial Code Review: A3 Polyglot Fraud-Score System

> Principal-engineer adversarial review of the agent-generated A3 PR (FastAPI ingestion + Node
> worker + Rust engine). **Posture: assume the implementation is wrong until proven correct.**
> Goal: prevent production incidents. Date: 2026-06-17.
> Reviewed: diff/source (`fastapi-service/`, `node-worker/`, `rust-engine/`), tests, runtime behavior.
> The three highest-severity findings were **reproduced live** (evidence below) — not theorized.

---

## Executive Summary

The A3 system is functionally correct on the happy path (its own suites are green), but adversarial
review found **3 blocking defects** — including a **Critical arbitrary-file-write (path traversal)**
that is trivially exploitable from an unauthenticated request, an **unauthenticated internal scoring
endpoint that lets anyone neutralize fraud scores**, and an **unhandled duplicate-ID crash (HTTP
500)**. All three were reproduced. Beyond these, money is stored as floating point, the DB-write /
enqueue step is non-atomic, and the worker has no engine timeout, no queue-claim (double-processing
under concurrency), and silently dead-letters transactions on transient API outages. **Recommendation:
do not ship until the 3 blocking issues are fixed.**

| Severity | Count |
|---|---|
| Critical | 1 |
| High | 3 |
| Medium | 5 |
| Low | 3 |

---

## Issue Inventory

### A5-1 — Path traversal / arbitrary file write via `transaction_id` 🔴
* **Dimension:** Security / Correctness
* **Description:** The queue filename is built directly from the client-supplied `transaction_id`
  with no sanitization, so a `transaction_id` containing `../` writes the queue file **outside** the
  queue directory — arbitrary file write within the process's permissions (overwrite configs, plant
  files, fill disks).
* **Evidence (File Path):** `fastapi-service/app/queue.py:16`
  ```python
  path = os.path.join(queue_dir, f"{txn['transaction_id']}.json")  # transaction_id is client-controlled, unsanitized
  ```
  `fastapi-service/app/schemas.py` — `TransactionIn.transaction_id: str` has **no format/length constraint**.
  **Reproduced:**
  ```text
  POST /transactions {"transaction_id":"../A5_PWNED", ...}   -> 201
  $ ls /tmp/a5_repro/queue        -> (empty)
  $ ls /tmp/a5_repro/A5_PWNED.json -> -rw-r--r-- ... A5_PWNED.json   # ESCAPED the queue dir
  ```
* **Severity:** **Critical** · **Blocking**
* **Suggested Fix:** Validate `transaction_id` against a strict allowlist (e.g. `^[A-Za-z0-9_-]{1,64}$`)
  in `TransactionIn` (Pydantic `pattern=`), AND defensively use only the basename + assert the
  resolved path stays within `queue_dir` (`os.path.realpath(path).startswith(os.path.realpath(queue_dir))`).
* **Verification Method:** Re-run the POST with `"../A5_PWNED"` → expect **422** (rejected) and no
  file outside `queue/`; add a regression test asserting traversal IDs are rejected.

### A5-2 — Unauthenticated internal scoring endpoint (fraud bypass) 🟠
* **Dimension:** Security / API Design
* **Description:** `POST /internal/transactions/{id}/score` persists an arbitrary score/risk with **no
  authentication** and is mounted on the same public app. Any client can overwrite a high-risk score
  with `low`, defeating the entire fraud system.
* **Evidence (File Path):** `fastapi-service/app/routes.py:95-109` (no auth dependency; same router as public routes).
  **Reproduced:** a `amount=999999, country=US, merchant=gambling` txn forced to `score=0, risk=low`:
  ```text
  POST /internal/transactions/victim1/score {"score":0,"risk_level":"low",...} -> {"ok":true}
  GET /transactions/victim1 -> stored score: 0  risk: low
  ```
* **Severity:** **High** · **Blocking**
* **Suggested Fix:** Require a shared-secret/mTLS/internal-network auth on `/internal/*` (e.g. a
  `X-Internal-Token` header validated against an env secret), or move the callback to a private
  network/queue not exposed publicly.
* **Verification Method:** POST to `/internal/...` without the token → expect **401/403**; with the
  token → 200. Add an auth test.

### A5-3 — Duplicate `transaction_id` → unhandled `IntegrityError` (HTTP 500) 🟠
* **Dimension:** Error Handling / Correctness
* **Description:** Re-POSTing an existing `transaction_id` violates the primary key; the
  `IntegrityError` from `db.commit()` is uncaught → HTTP 500 (and leaves the session in a bad state).
  No idempotency, no 409.
* **Evidence (File Path):** `fastapi-service/app/routes.py:43-57` (`db.add(txn); db.commit()` with PK = `transaction_id`, no existence check / try-except).
  **Reproduced:** `first POST: 201`, `second POST: 500`.
* **Severity:** **High** · **Blocking** (retries/at-least-once delivery upstream will routinely resend IDs → 500 storms).
* **Suggested Fix:** Treat as idempotent — check `db.get(Transaction, id)` first and return 200/conflict,
  or catch `IntegrityError`, `db.rollback()`, and return 409. Add a unique-violation handler.
* **Verification Method:** POST same ID twice → expect 200/409 (not 500); regression test.

### A5-4 — Money stored as floating point 🟠
* **Dimension:** Correctness (financial)
* **Description:** `amount` is a `float`/SQL `REAL` end to end. Floating point is lossy for currency
  (`0.1+0.2`), causing wrong totals/threshold edge behavior in a *financial fraud* system.
* **Evidence (File Path):** `fastapi-service/app/models.py` (`amount = Column(Float)`),
  `fastapi-service/app/schemas.py` (`amount: float`), Rust `amount: f64`.
* **Severity:** **High** · Non-blocking (works for the demo thresholds) but must fix before real money.
* **Suggested Fix:** Use integer **minor units** (paise/cents) or `Decimal`/`NUMERIC`; keep the engine on integers.
* **Verification Method:** Test `amount=0.1` summed 3× equals `0.3` exactly; threshold test at `10000.00`.

### A5-5 — Non-atomic DB-commit-then-enqueue (lost/stuck work) 🟡
* **Dimension:** Correctness / Reliability
* **Description:** The row is committed `status=pending` (`routes.py:57`) **then** the queue file is
  written (`routes.py:59`). If enqueue fails (bad path, disk full, crash between the two), the txn is
  permanently `pending` and never scored, with no reconciliation.
* **Evidence (File Path):** `fastapi-service/app/routes.py:56-69`.
* **Severity:** **Medium** · Non-blocking.
* **Suggested Fix:** Enqueue first (or use an outbox pattern / single transaction), and add a sweeper
  that re-enqueues `pending` rows older than N seconds.
* **Verification Method:** Inject an enqueue failure → assert the row isn't left silently pending (or is re-swept).

### A5-6 — Worker has no queue claim → double-processing under concurrency 🟡
* **Dimension:** Concurrency
* **Description:** `processQueueOnce` lists all `*.json` and processes them; the only "claim" is the
  move to `processed/` **after** scoring. Two worker instances (loop mode / horizontal scale) will
  both pick up the same file → duplicate engine calls and duplicate score POSTs.
* **Evidence (File Path):** `node-worker/src/worker.js:319-353` (no lock/rename-to-claim before work).
* **Severity:** **Medium** · Non-blocking (single worker today).
* **Suggested Fix:** Atomically claim each file first (`rename` to a `processing/` dir owned by the worker; the loser's rename fails) before scoring.
* **Verification Method:** Run two workers against one file → exactly one POST; assert via a mock API call count.

### A5-7 — `callEngine` has no timeout (hung engine stalls the worker) 🟡
* **Dimension:** Reliability / Performance
* **Description:** `callEngine` resolves only on the child's `close`; a hung/never-exiting engine
  leaves the Promise pending forever, blocking the (sequential) queue loop indefinitely.
* **Evidence (File Path):** `node-worker/src/worker.js:77-151` (no `setTimeout`/`child.kill`).
* **Severity:** **Medium** · Non-blocking.
* **Suggested Fix:** Add a timeout that `child.kill()`s and rejects after N seconds.
* **Verification Method:** Mock a spawn that never closes → assert rejection after the timeout.

### A5-8 — Transient failures are silently dead-lettered, never retried 🟡
* **Dimension:** Reliability / Observability
* **Description:** On engine-exhaustion or `postScore` failure, the file is moved to `failed/`
  (`worker.js:257,277`) and never reprocessed. A brief API outage permanently fails every in-flight
  txn, with no alerting and no redrive.
* **Evidence (File Path):** `node-worker/src/worker.js:251-279`.
* **Severity:** **Medium** · Non-blocking.
* **Suggested Fix:** Distinguish retryable (5xx/network) from permanent errors; redrive `failed/` on a
  schedule; emit a metric/alert on dead-letter.
* **Verification Method:** Take the API down, process a file, bring it up → assert the txn eventually scores.

### A5-9 — No input validation limits on transaction fields 🟡
* **Dimension:** Security / Input validation
* **Description:** `TransactionIn` constrains nothing — `user_id`, `country`, `merchant_category`,
  `transaction_id` accept arbitrary length/content (enables A5-1; allows unbounded DB growth, non-ISO countries).
* **Evidence (File Path):** `fastapi-service/app/schemas.py` (no `max_length`, `pattern`, or `Literal`).
* **Severity:** **Medium** · Non-blocking.
* **Suggested Fix:** Add `max_length`, `pattern` (transaction_id), ISO-2 validation for `country`, and a sane `amount` upper bound.
* **Verification Method:** POST oversized/invalid fields → expect 422.

### A5-10 — Engine stdout parsed unbounded 🔵
* **Dimension:** Performance / Robustness
* **Evidence:** `node-worker/src/worker.js:101-103` accumulates `stdout` with no cap; a misbehaving engine could exhaust memory.
* **Severity:** **Low** · Non-blocking. **Fix:** cap buffered output. **Verify:** feed large output → bounded.

### A5-11 — 500 paths not observable 🔵
* **Dimension:** Observability
* **Evidence:** request_id middleware exists, but the uncaught `IntegrityError` (A5-3) emits a stack trace, no structured error log/metric. **Severity:** Low. **Fix:** exception handler emitting structured JSON + a 5xx counter. **Verify:** trigger error → structured log present.

### A5-12 — Dependency drift risk 🔵
* **Dimension:** Dependency Risk
* **Evidence:** `node-worker/package.json` `axios ^1.7` (caret); Python `requirements.txt` ranges. Lockfiles exist (`package-lock.json`, `Cargo.lock`) but Python has no hash lock. **Severity:** Low/Nit. **Fix:** hash-pin Python deps. **Verify:** reproducible install.

---

## Blocking Issues
**A5-1 (Critical, path traversal)**, **A5-2 (High, unauth scoring)**, **A5-3 (High, duplicate→500)** — all reproduced; must be fixed before merge.

## Security Findings
A5-1 (arbitrary file write), A5-2 (auth bypass / fraud neutralization), A5-9 (input validation), A5-12 (deps). A5-1 + A5-2 are the production-incident risks.

## Performance Findings
A5-7 (hung engine stalls the sequential loop), A5-10 (unbounded stdout), and the throughput ceiling of single-threaded `processQueueOnce` + 2 s poll (latency floor). None are the top risk; correctness/security dominate.

## Test Coverage Gaps
The suites cover the happy path and basic validation but **miss every adversarial case**: no path-traversal test (A5-1), no duplicate-ID test (A5-3), no auth test on `/internal` (A5-2), no concurrency/double-processing test (A5-6), no engine-timeout test (A5-7), no dead-letter/redrive test (A5-8), no float-precision test (A5-4).

## Maintainability Concerns
`/internal` shares the public router (no boundary); scoring rules duplicated conceptually between contract and Rust (acceptable, single source is Rust); worker error taxonomy is binary (success/failed) with no retryable/permanent distinction (A5-8).

## Suggested Fixes (priority order)
1. **A5-1** validate `transaction_id` (`pattern=^[A-Za-z0-9_-]{1,64}$`) + path-containment assert in `enqueue`.
2. **A5-2** auth-gate `/internal/*` (shared secret / network isolation).
3. **A5-3** idempotent create (check-then-insert or catch IntegrityError → 409).
4. **A5-4** money to integer minor units / Decimal.
5. **A5-6/7/8** queue-claim, engine timeout, retryable-vs-permanent + redrive.

---

## Agent vs Verified

### Potential issues (reasoned from code, not executed)
A5-4 (float precision — type confirmed, impact inferred), A5-5 (non-atomic enqueue), A5-6 (double-processing), A5-7 (no engine timeout), A5-8 (dead-letter), A5-9/10/11/12.

### Verified issues (reproduced live, evidence captured)
* **A5-1** — POST `transaction_id="../A5_PWNED"` → `201`; file created at `/tmp/a5_repro/A5_PWNED.json` **outside** `queue/`.
* **A5-2** — `/internal/.../score` with no auth forced a 999999/US/gambling txn to `score 0 / low`.
* **A5-3** — duplicate `transaction_id`: first `201`, second `500`.

---

## Remediation Status (post-review)
The 3 blocking issues were subsequently **fixed in A3 and regression-tested** (verified):
* **A5-1** → `transaction_id` constrained (`pattern=^[A-Za-z0-9_-]{1,64}$`) + path-containment in `queue.py`; test `test_path_traversal_transaction_id_rejected` (traversal id → **422**, no escape).
* **A5-2** → optional `X-Internal-Token` auth on `/internal/*`; test `test_internal_score_requires_token_when_configured` (**401** without / **200** with).
* **A5-3** → idempotent create returns **409**; test `test_duplicate_transaction_id_returns_409`.
A3 fastapi suite: 7 → **10 passed**; end-to-end integration still **4/4 PASS**. (A5-4..12 remain as backlog.)

## Completion Criteria
- [x] Issue list (12, across all 11 dimensions)
- [x] Severity assigned (Critical/High/Medium/Low)
- [x] Blocking classification (3 blocking)
- [x] Fix proposal per issue
- [x] Verification steps per issue (reproduce + verify-fix + expected outcome)
- [x] `A5_adversarial_review.md`
