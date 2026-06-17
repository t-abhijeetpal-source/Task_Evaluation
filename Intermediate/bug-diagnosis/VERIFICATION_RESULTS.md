# I6 — Verification Run Results

> Real, executed output from the bug-diagnosis workflow. Environment: Python 3.14.6 ·
> pytest 8.4.2 (run via the shared I4 venv; no install — disk-constrained host).

---

## Status: ✅ REPRODUCED → ROOT-CAUSED → FIXED → VERIFIED

| Step | Command | Result |
|---|---|---|
| Reproduce (buggy code) | `pytest -v` | **3 failed, 2 passed** (failures at `qty == 10`) |
| Root cause | `grep "qty >" app/services.py` | `services.py:18` used strict `>` |
| Fix | `>` → `>=` (one operator) | applied |
| Compile check | `py_compile app/*.py` | OK |
| Verify (fixed code) | `pytest -v` | **5 passed, 0 failed** |
| Re-validation (this run) | `pytest -q` | **5 passed** |

---

## 1. Reproduction (before fix)

```text
$ pytest -v
tests/test_orders.py::test_no_discount_below_threshold              PASSED
tests/test_orders.py::test_bulk_discount_applies_at_threshold_of_10 FAILED
tests/test_orders.py::test_discount_above_threshold                 PASSED
tests/test_orders.py::test_mixed_order_total                        FAILED
tests/test_orders.py::test_api_order_total_at_threshold             FAILED
==================== 3 failed, 2 passed in 0.30s ====================

# assertion evidence:
assert {'id': 1, 'total': 1000.0} == {'id': 1, 'total': 900.0}
test_mixed_order_total: assert 1400.0 == 1350.0
```
All failures are exactly the `qty == 10` boundary cases.

## 2. Fix (the entire change)

```diff
# app/services.py :: calculate_line_total (line 18)
-    if item.qty > BULK_QTY_THRESHOLD:
+    if item.qty >= BULK_QTY_THRESHOLD:
```

## 3. Verification (after fix)

```text
$ python -m py_compile app/*.py
py_compile: OK (no syntax errors)

$ pytest -v
tests/test_orders.py::test_no_discount_below_threshold              PASSED
tests/test_orders.py::test_bulk_discount_applies_at_threshold_of_10 PASSED
tests/test_orders.py::test_discount_above_threshold                 PASSED
tests/test_orders.py::test_mixed_order_total                        PASSED
tests/test_orders.py::test_api_order_total_at_threshold             PASSED
========================= 5 passed in 0.27s =========================
```

## 4. Re-validation (independent re-run for this report)

```text
$ pytest -q
.....                                                                    [100%]
5 passed, 1 warning in 0.21s
```

---

## Summary

| Check | Result |
|---|---|
| Bug reproduced (real failing tests) | ✅ 3 failed at boundary |
| Root cause cited (`services.py:18`) | ✅ |
| Minimal fix (1 operator) | ✅ |
| Compile clean | ✅ |
| Tests after fix | ✅ 5 passed |
| Re-validated | ✅ 5 passed |

**Verdict: I6 is complete, reproduced, fixed, and verified.** Full analysis (risk, rollback,
agent-vs-verified) in `docs/agent-analysis/I6_bug_diagnosis.md`.

> Note: the bug was *seeded* (no buggy repo was provided), disclosed transparently in the docs.
> The reproduction and verification outputs above are genuine executions, not predictions.
