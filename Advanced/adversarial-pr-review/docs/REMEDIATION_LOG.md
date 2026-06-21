# A5 Remediation Log — before/after per fix

Each entry: the exploit/repro **before**, the change, and the **after** result from re-running the
*same* exploit. Repro evidence lives in `artifacts/repro/`. Date: 2026-06-21.

> Honesty note: this log only marks an item "fixed" when the original reproduction no longer succeeds
> against the patched code. Deferred items are marked DEFERRED with a rationale, not as "fixed".

---

## A5-1 — Path traversal (Critical, blocking)
* **Before:** `POST {"transaction_id":"../A5_PWNED"}` → 201, file written outside `queue/`.
* **Change:** `TransactionIn.transaction_id` `pattern=^[A-Za-z0-9_-]{1,64}$`; `enqueue()` uses basename +
  realpath containment assert (`fastapi-service/app/schemas.py`, `app/queue.py`).
* **After:** traversal id → **422**, nothing escapes `queue/` — `artifacts/repro/AFTER_api_exploits.txt` [A5-1].
* **Test:** `test_path_traversal_transaction_id_rejected`.

## A5-2 / A5-17 — Internal auth fail-open → fail-closed (High/Critical, blocking)
* **Before:** default config (no `A3_INTERNAL_TOKEN`); forged `score=0/low` on a 999999/US/gambling txn,
  **no** `X-Internal-Token` → **HTTP 200**, score neutralized — `artifacts/repro/BEFORE_api_exploits.txt`.
* **Root cause:** v1 guard `if _INTERNAL_TOKEN is not None and token != _INTERNAL_TOKEN` skipped auth
  entirely when the env var was unset (the default).
* **Change:** `_check_internal_auth()` in `app/routes.py` — **fail-closed**:
  * no server token configured → **503** "internal auth not configured" (deny all);
  * missing/wrong header → **401** (constant-time `hmac.compare_digest`, see A5-19);
  * correct header → proceed.
* **After:**
  * token configured, no/wrong header → **401**; correct → 200 — `AFTER_api_exploits.txt` [A5-2].
  * **default config, no token → 503** (un-callable) — `AFTER_failclosed_default_config.txt`.
* **Tests:** `test_internal_score_requires_token`, `test_internal_score_fail_closed_when_unconfigured`.

## A5-3 / A5-16 — Duplicate & concurrent create → 500 → 409 (High, blocking)
* **Before:** duplicate id → uncaught `IntegrityError` → **500**; even the v1 pre-check left a TOCTOU race
  that still 500s under concurrency — `BEFORE_api_exploits.txt` [A5-16].
* **Change:** `app/routes.py` — keep the idempotent pre-check (→409) **and** wrap `db.commit()` in
  `try/except IntegrityError: db.rollback(); return 409`. The PK constraint is the authoritative guard.
* **After:** sequential duplicate → **409**; raced duplicate (pre-check forced to miss) → **409**, never 500
  — `AFTER_api_exploits.txt` [A5-16].
* **Tests:** `test_duplicate_transaction_id_returns_409`, `test_concurrent_duplicate_create_no_500`.

## A5-13 — Score poisoning (High, blocking)
* **Before:** `POST score=999 risk_level=low` → **200**, persisted — `BEFORE_api_exploits.txt` [A5-13].
* **Change:** `app/routes.py` validates range `0..100`, `risk_level ∈ {low,medium,high}`, and band
  consistency (`risk_level == band(score)`) → 422; `app/schemas.py` adds `score: Field(ge=0, le=100)`.
* **After:** `score=999` → **422**, txn stays `pending` — `AFTER_api_exploits.txt` [A5-13].
* **Tests:** `test_score_poisoning_out_of_range_rejected`, `test_score_invalid_risk_level_rejected`,
  `test_score_band_mismatch_rejected`.

## A5-14 — Callback overwrite (High, blocking)
* **Before:** 1st `90/high` → 200; 2nd `0/low` → **200**; GET → `0/low` (high silently flipped) —
  `BEFORE_api_exploits.txt` [A5-14].
* **Change:** `app/routes.py` — if already `scored`: identical replay → 200 `{idempotent:true}`;
  conflicting → **409**, original preserved.
* **After:** 2nd conflicting score → **409**; GET → `90/high` — `AFTER_api_exploits.txt` [A5-14].
* **Tests:** `test_callback_idempotent_replay`, `test_callback_overwrite_rejected`.

## A5-15 — Path/body id mismatch (Medium)
* **Before:** path `realA`, body `totally_different` → **200** — `BEFORE_api_exploits.txt` [A5-15].
* **Change:** reject path≠body id → 422.
* **After:** → **422** — `AFTER_api_exploits.txt` [A5-15].
* **Test:** `test_score_path_body_id_mismatch_rejected`.

## A5-18 — Integration harness broken (High, blocking)
* **Before:** `bash run_integration.sh` → `polyglot: unbound variable`, **exit 1** — `BEFORE_integration.txt`.
* **Change:** `integration-tests/run_integration.sh` — replace `$polyglot-fraud-system` with `$A3`; export a
  per-run `A3_INTERNAL_TOKEN` to both API and worker.
* **After:** **INTEGRATION: PASS (4/4), exit 0** — `suites/AFTER_integration.txt`.

## A5-7 — Engine timeout (Medium) ✅
* **Change:** `worker.js` `ENGINE_TIMEOUT_MS` (5s) `SIGKILL`s a hung child and rejects.
* **Test:** `A5-7: rejects (and kills child) when the engine never closes` (never-closing fake child).

## A5-10 — Unbounded engine stdout (Low) ✅
* **Change:** `worker.js` `MAX_OUTPUT_BYTES` (1 MiB) cap kills child + rejects.
* **Test:** `A5-10: rejects when engine stdout exceeds the output cap`.

## A5-19 — Timing-unsafe token compare (Medium) ✅
* **Change:** `hmac.compare_digest` replaces `!=`. Covered by `test_internal_score_requires_token`.

## A5-20 — Worker contract drift under fail-closed auth (Medium) ✅
* **Change:** worker attaches `X-Internal-Token` from `A3_INTERNAL_TOKEN`; integration shares the token.
* **Verified:** integration 4/4 PASS proves the worker authenticates end-to-end.

## A5-9 — Input validation limits (Medium) ✅
* **Change:** `transaction_id` pattern + `max_length` on `user_id`/`merchant_category`/`timestamp`,
  `min/max_length` on `country` (`app/schemas.py`). Verified by happy-path + traversal tests.

---

## Deferred (explicit, with rationale + guard where applicable)

| ID | Why deferred | Guard / mitigation |
|---|---|---|
| A5-4 | Integer minor-units/Decimal spans 3 langs + bumps the LOCKED contract (`amount:number`, Rust `f64`). v1.1 work, not an in-place patch. | `rust-engine/tests/scoring.rs::high_amount_threshold_boundary` pins the threshold the migration must preserve. |
| A5-5 | Outbox/sweeper is a design change; non-blocking on single node. | `enqueue()` failure now surfaces as a 500 (visible), not a silent pending. |
| A5-6 | Atomic rename-claim; single worker today. | **Data risk neutralized by A5-14** (idempotent/409 callback); only duplicate *work* remains. |
| A5-8 | Needs retryable/permanent taxonomy + redrive + metric. | Rust call already retries 3×; documented. |
| A5-11 | Dedicated 5xx handler + counter. | Primary 500 sources (A5-3/A5-16) eliminated. |
| A5-12 | Python hash-pinning. | Lockfiles present (`package-lock.json`, `Cargo.lock`). |
