# I6 — Bug Diagnosis Report

> Status: **REPRODUCED → ROOT-CAUSED → FIXED → VERIFIED.**
> Bug type: off-by-one boundary error in the bulk-discount rule.
> Environment: Python 3.14.6 · FastAPI · pytest 8.4.2 (run via the shared I4 venv; no install — host disk full).

> **Transparency note:** no pre-existing buggy repo was provided, so a realistic bug was *seeded*
> into a small layered orders service (per the I6 "seeded bug" framing). The workflow below was
> then performed as a genuine diagnosis — the failing/passing test outputs are real.

---

## Problem Statement

Per `SPEC.md` rule 3, a line item qualifies for a **10% bulk discount when `qty >= 10`**.
Observed: an order line with **exactly `qty = 10`** is charged full price (no discount).

- **Observed behavior:** `qty = 10` → total `1000.0` (full price).
- **Expected behavior:** `qty = 10` → total `900.0` (1000 − 10%).
- **Scope:** only the exact boundary `qty == 10`; `qty <= 9` and `qty >= 11` behave correctly.
- **User impact:** customers ordering exactly 10 units are **overcharged by 10%** on that line.
- **Affected module:** `app/services.py` (bulk-discount calculation).
- **Severity:** **Medium** — incorrect billing (real money), but narrow (single boundary) and no crash/data loss.

---

## Reproduction Steps

```bash
cd I6
# (uses the shared I4 venv since the host disk is full; otherwise: pip install -r requirements.txt)
PY=/Users/abhijeetpal/Desktop/workspace/Tasks/polyglot-currency-pair/fastapi-service/.venv/bin/python
$PY -m pytest -v
```

**Actual result (before fix) — 3 failed, 2 passed:**
```
tests/test_orders.py::test_no_discount_below_threshold           PASSED
tests/test_orders.py::test_bulk_discount_applies_at_threshold_of_10  FAILED
tests/test_orders.py::test_discount_above_threshold              PASSED
tests/test_orders.py::test_mixed_order_total                     FAILED
tests/test_orders.py::test_api_order_total_at_threshold          FAILED
==================== 3 failed, 2 passed in 0.30s ====================

# key assertion failure:
assert {'id': 1, 'total': 1000.0} == {'id': 1, 'total': 900.0}
test_mixed_order_total: assert 1400.0 == 1350.0
```
The failures are exactly the cases involving `qty == 10`. This is the captured reproduction evidence.

---

## Investigation (execution path)

```
HTTP GET /orders/{id}/total
   ↓  app/routes.py :: get_order_total          (looks up order, calls service)
   ↓  app/services.py :: calculate_total        (sums line totals)
   ↓  app/services.py :: calculate_line_total   (applies bulk discount)  <-- defect here
```

| File | Function | Purpose |
|---|---|---|
| `app/routes.py` | `get_order_total` | HTTP entry; fetches items, calls `calculate_total` |
| `app/services.py` | `calculate_total` | sums per-line totals, rounds |
| `app/services.py` | `calculate_line_total` | computes one line; **applies discount** |

`calculate_line_total` was returning the un-discounted line total for `qty == 10`, so
`calculate_total` summed the wrong number → the endpoint returned the wrong total.

---

## Root Cause

- **File:** `app/services.py`
- **Function:** `calculate_line_total`
- **Line:** 18
- **Defect:** the discount condition used a **strict** comparison:
  ```python
  if item.qty > BULK_QTY_THRESHOLD:   # BULK_QTY_THRESHOLD = 10
  ```
  SPEC rule 3 requires the discount at **10 or more** (`>=`). With `>`, `qty == 10` fails the
  condition and gets no discount — a classic **off-by-one / boundary** error.
- **Evidence:** the threshold constant is `10` (`services.py:11`); the failing tests are precisely
  the `qty == 10` cases while `qty = 9` and `qty = 11` pass; the assertion shows `1000.0` (== `100×10`,
  no discount) instead of `900.0`.

**VERIFIED cause:** `>` should be `>=` at `services.py:18`.
**POSSIBLE (considered and ruled out):** wrong discount rate (rate is correctly `0.10`); rounding
error (results are exact); schema coercion of `qty` (it's a validated `int`). None of these explain
a boundary-only failure — only the comparison operator does.

---

## Files Involved / Files Changed

| File | Changed? | Why |
|---|---|---|
| `app/services.py` | ✅ yes | the defect: discount boundary operator |
| `app/routes.py` | no | correct; only routes to the service |
| `app/schemas.py` | no | validation correct |
| `tests/test_orders.py` | no (already encodes the spec) | the boundary test reproduces the bug |

---

## Fix Description / Diff Summary

Smallest possible change — one operator, one line, no refactor:

```diff
--- a/app/services.py
+++ b/app/services.py
@@ def calculate_line_total(item: Item) -> float:
     line_total = item.price * item.qty
-    if item.qty > BULK_QTY_THRESHOLD:
+    if item.qty >= BULK_QTY_THRESHOLD:
         line_total = line_total * (1 - BULK_DISCOUNT_RATE)
     return line_total
```

`>` → `>=` makes `qty == 10` qualify, matching SPEC rule 3. Blast radius: one boundary case;
all previously-correct cases (`qty <= 9`, `qty >= 11`) are unaffected.

---

## Verification Results

```bash
PY=/Users/abhijeetpal/Desktop/workspace/Tasks/polyglot-currency-pair/fastapi-service/.venv/bin/python
$PY -m py_compile app/*.py     # build/compile check
$PY -m pytest -v               # tests
```

**Compile:** `py_compile: OK (no syntax errors)`.

**Tests (after fix) — 5 passed, 0 failed:**
```
tests/test_orders.py::test_no_discount_below_threshold           PASSED
tests/test_orders.py::test_bulk_discount_applies_at_threshold_of_10  PASSED
tests/test_orders.py::test_discount_above_threshold              PASSED
tests/test_orders.py::test_mixed_order_total                     PASSED
tests/test_orders.py::test_api_order_total_at_threshold          PASSED
========================= 5 passed in 0.27s =========================
```

| Check | Command | Result |
|---|---|---|
| Reproduction (before) | `pytest -v` | 3 failed, 2 passed |
| Compile (after) | `py_compile app/*.py` | OK |
| Tests (after) | `pytest -v` | **5 passed, 0 failed** |

---

## Risk Assessment

**Risk: Low.**
- One-character change to a single conditional; no signature, schema, or API change.
- Behavior change is confined to the intended boundary (`qty == 10` now discounts); all other
  quantities are provably unchanged (tests for 9 and 11 still pass).
- Full suite green + compile clean. No new dependencies.

---

## Rollback Plan

The change is one line. To revert:
```diff
-    if item.qty >= BULK_QTY_THRESHOLD:
+    if item.qty > BULK_QTY_THRESHOLD:
```
Or, if committed: `git revert <sha>` (single-line commit) / `git checkout -- app/services.py`.
No data migration or state cleanup is involved (stateless calculation).

---

# Agent vs Verified

## Agent Suggested (hypotheses before confirming)
- **Potential causes:** (a) boundary operator `>` vs `>=`; (b) wrong discount rate; (c) float
  rounding; (d) `qty` type coercion.
- **Potential fixes:** change the comparison; or special-case `qty == threshold`.
- **Ideas:** add a boundary test at exactly the threshold (already present).

## Manually Verified (confirmed by execution)
- **Actual root cause:** `app/services.py:18` used `>`; should be `>=` (boundary-only failures
  prove it; rate/rounding/type ruled out).
- **Actual fix:** `>` → `>=` (one line).
- **Actual test results:** before = 3 failed / 2 passed; after = **5 passed / 0 failed**; `py_compile` OK.
- **Actual behavior:** `qty = 10 → total 900.0` (was `1000.0`), via both the unit function and the
  live `GET /orders/{id}/total` endpoint.

---

## Completion Criteria

- [x] Bug reproduced (real failing tests captured)
- [x] Root cause identified (`services.py:18`, `>` vs `>=`)
- [x] Source files cited
- [x] Minimal fix implemented (one operator)
- [x] Tests executed (before + after captured)
- [x] Verification output captured (compile + 5 passed)
- [x] Risk assessment included (Low)
- [x] Rollback plan included
- [x] I6_bug_diagnosis.md generated
