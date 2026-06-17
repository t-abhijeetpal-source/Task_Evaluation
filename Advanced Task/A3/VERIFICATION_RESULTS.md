# A3 — Verification Run Results

> Real, executed output. All four test layers run; the end-to-end integration was hardened after a
> false-pass was caught (see note). Env: Python 3.14 · Node v26 · Rust 1.96. Date: 2026-06-17.

## Status: ✅ VERIFIED (Rust 6 · FastAPI 7 · Node 12 · Integration 4/4)

| Layer | Command | Result |
|---|---|---|
| Rust engine | `cargo test` | **6 passed** |
| FastAPI | `pytest -q` | **7 passed** |
| Node worker | `npm test` | **12 passed** |
| End-to-end | `bash integration-tests/run_integration.sh` | **4/4 PASS** (exit 0) |

---

## 1. Rust — `cargo test`
```text
running 6 tests
test canonical_baseline ... ok
test canonical_high_amount ... ok
test canonical_foreign ... ok
test canonical_all_three ... ok
test score_is_clamped_to_100 ... ok
test malformed_json_is_err_no_panic ... ok
test result: ok. 6 passed; 0 failed
```
Binary smoke test: `{...15000/US/gambling...} | fraud-engine` →
`{"score":90,"risk_level":"high","reasons":["high_amount","foreign_country","high_risk_merchant"]}`

## 2. FastAPI — `pytest -q`
```text
7 passed, 3 warnings in 0.07s
```

## 3. Node worker — `npm test`
```text
Test Suites: 1 passed, 1 total
Tests:       12 passed, 12 total
```

## 4. End-to-end integration (hardened) — `run_integration.sh`
```text
== starting FastAPI on :8078 (fresh DB + queue) ==
== POST 4 canonical transactions ==
queued files: 4
== run Node worker (--once): consumes queue, calls Rust, posts score back ==
  txn_base     score=0  risk=low     status=scored  expect=0/low      PASS
  txn_high     score=40 risk=medium  status=scored  expect=40/medium  PASS
  txn_foreign  score=20 risk=low     status=scored  expect=20/low     PASS
  txn_all      score=90 risk=high    status=scored  expect=90/high    PASS
INTEGRATION: PASS   (exit 0)
```
The full real cross-language flow executed: **Client → FastAPI (enqueue 4 files) → Node worker →
Rust binary → score → POST callback → GET shows scored**.

---

## Note — a false-pass was caught and fixed (honesty)

On a re-run, the integration test printed `queued files: 0` yet still reported PASS. Investigation
of the logs showed the real cause:

```
api.log:  ERROR: [Errno 48] address already in use (127.0.0.1:8077)
.run/a3.db: (no rows)        worker.log: processed 0
```

A **leftover uvicorn from a previous run** was still holding the port, so the new run's server
never bound and the POST/GET silently hit the **stale** server (which still had old scored data).
The health check passed against that stale server, masking the bind failure → a misleading PASS.

**Fixes applied to `integration-tests/run_integration.sh`:**
1. Free the port before starting (kill any prior listener); use a fresh port (8078).
2. Abort if our uvicorn process dies or never becomes healthy; abort if `address already in use`
   appears in the log — **refuse to test a stale server**.
3. Assert `queued files == 4` after POSTing (a zero/short count now fails loudly instead of
   false-passing) and assert each POST returns `201`.

The PASS above is from the hardened script on a fresh server/DB/queue — a genuine end-to-end result.

---

## How to reproduce
```bash
cd "Advanced Task/A3"
( cd rust-engine && cargo build --release && cargo test )
( cd fastapi-service && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && pytest -q )
( cd node-worker && npm install && npm test )
bash integration-tests/run_integration.sh
```
