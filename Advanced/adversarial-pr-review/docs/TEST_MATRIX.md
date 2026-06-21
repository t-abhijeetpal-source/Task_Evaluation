# A5 Test Matrix — finding → regression test

Every blocking fix and every High non-blocking fix maps to ≥1 automated test. Suite totals:
**Rust 7 · pytest 18 · Node 14 · integration 4/4 (exit 0)**.

| ID | Sev | Blocking | Status | Test(s) | Suite |
|---|---|---|---|---|---|
| A5-1 | Critical | ✅ | Fixed | `test_path_traversal_transaction_id_rejected` | pytest |
| A5-2 | High | ✅ | Fixed | `test_internal_score_requires_token` | pytest |
| A5-3 | High | ✅ | Fixed | `test_duplicate_transaction_id_returns_409` | pytest |
| A5-4 | High | — | Deferred | `high_amount_threshold_boundary` (boundary guard) | rust |
| A5-5 | Medium | — | Deferred | (documented; covered indirectly by happy-path enqueue) | — |
| A5-6 | Medium | — | Deferred (mitigated by A5-14) | `test_callback_overwrite_rejected` (data-corruption guard) | pytest |
| A5-7 | Medium | — | Fixed | `A5-7: rejects (and kills child) when the engine never closes` | node |
| A5-8 | Medium | — | Deferred | (documented) | — |
| A5-9 | Medium | — | Fixed | `test_post_missing_field`, `test_path_traversal_*` | pytest |
| A5-10 | Low | — | Fixed | `A5-10: rejects when engine stdout exceeds the output cap` | node |
| A5-11 | Low | — | Deferred (reduced) | (A5-3/A5-16 remove the 500 source) | — |
| A5-12 | Low | — | Deferred | (lockfiles present) | — |
| A5-13 | High | ✅ | Fixed | `test_score_poisoning_out_of_range_rejected`, `test_score_invalid_risk_level_rejected`, `test_score_band_mismatch_rejected` | pytest |
| A5-14 | High | ✅ | Fixed | `test_callback_idempotent_replay`, `test_callback_overwrite_rejected` | pytest |
| A5-15 | Medium | — | Fixed | `test_score_path_body_id_mismatch_rejected` | pytest |
| A5-16 | High | ✅ | Fixed | `test_concurrent_duplicate_create_no_500` | pytest |
| A5-17 | High | ✅ | Fixed | `test_internal_score_fail_closed_when_unconfigured` | pytest |
| A5-18 | High | ✅ | Fixed | `run_integration.sh` (4/4 PASS, exit 0) | integration |
| A5-19 | Medium | — | Fixed | `test_internal_score_requires_token` (wrong token → 401) | pytest |
| A5-20 | Medium | — | Fixed | `run_integration.sh` (worker authenticates E2E) | integration |

## Coverage check against the rubric

* **≥1 test per blocking fix:** A5-1, A5-2, A5-3, A5-13, A5-14, A5-16, A5-17, A5-18 — all ✅.
* **≥1 test per High non-blocking fix:** A5-4 is the only High that is deferred → guarded by
  `high_amount_threshold_boundary`. ✅
* **Full suites green:** Rust 7/7, pytest 18/18 (was 10), Node 14/14 (was 12), integration 4/4 exit 0. ✅

## How to run

```bash
cd Advanced/polyglot-fraud-system/rust-engine     && cargo test
cd Advanced/polyglot-fraud-system/fastapi-service && .venv/bin/python -m pytest -q
cd Advanced/polyglot-fraud-system/node-worker     && npm test
bash Advanced/polyglot-fraud-system/integration-tests/run_integration.sh   # exit 0

# Re-run the live API exploit harness (before/after the same script):
cd Advanced/polyglot-fraud-system/fastapi-service
PYTHONPATH="$PWD" .venv/bin/python ../../adversarial-pr-review/artifacts/repro/api_exploits_repro.py            # default = fail-closed (no token)
PYTHONPATH="$PWD" .venv/bin/python ../../adversarial-pr-review/artifacts/repro/api_exploits_repro.py --with-token
```
