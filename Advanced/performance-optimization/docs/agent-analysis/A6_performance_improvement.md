# A6 — Performance Profiling & Targeted Optimization

> Target: `GET /api/summary` in the A2 Expense Tracker (`Advanced/parallel-expense-tracker/app/routes.py`).
> Method: **measure → profile → identify → minimal change → verify** (never optimize on intuition).
> Result: **92.7% latency reduction** (278.64 ms → 20.26 ms at N=50k) with a **~10-line, single-function
> change**, behavior preserved (16/16 tests). Date: 2026-06-17.

---

## Baseline Results

**Environment:** Python 3.14.6 · FastAPI + SQLAlchemy 2 · SQLite (temp file) · `TestClient`.
**Input size:** N = 50,000 expenses across 6 categories.
**Command:**
```bash
cd "Advanced/parallel-expense-tracker" && .venv/bin/python "../A6/bench_summary.py"
```
**Output (current code — Python-side aggregation):**
```text
env: python=3.14.6  N=50000  iters=15  db=sqlite(temp)
correctness: count=50000  total=12550000.00  categories=6
/api/summary latency over 15 runs (N=50000):
  min  = 263.36 ms   p50 = 278.64 ms   p95 = 301.36 ms   max = 314.84 ms   mean = 279.60 ms
```
Latency ~280 ms for a 6-number summary — and it grows linearly with row count (throughput ceiling).

## Profiling Evidence

**Command:** `.venv/bin/python "../A6/bench_summary.py" --profile` (cProfile, 10 summary calls)
**Output (top by `tottime`):**
```text
         10046725 function calls (10045369 primitive calls) in 4.455 seconds
   ncalls  tottime  cumtime  filename:lineno(function)
   500000    1.157    2.344   sqlalchemy/orm/loading.py:1068(_instance)        <-- ORM row -> object
   500000    0.347    0.755   sqlalchemy/orm/instrumentation.py:501(new_instance)
       10    0.340    0.340   {method 'fetchall' of 'sqlite3.Cursor'}          <-- raw SQL: only 0.34s
       10    0.327    3.317   sqlalchemy/engine/result.py:582(_allrows)
   500000    0.314    0.314   sqlalchemy/orm/state.py:201(__init__)
   500000    0.256    0.256   sqlalchemy/orm/loading.py:1329(_populate_full)
  2000000    0.254    0.254   sqlalchemy/orm/attributes.py:555(__get__)         <-- 2M attribute reads
       10    0.227    3.970   app/routes.py:43(summary)                         <-- our endpoint
```

## Bottleneck Analysis

* **Single highest-impact bottleneck:** ORM **object materialization**, not the database.
  `summary` calls `db.query(Expense).all()`, which hydrates **every** row into a fully-instrumented
  `Expense` ORM object before Python sums them. For 50k rows × 10 calls that is 500,000 `_instance`
  constructions and **2,000,000** instrumented `attributes.__get__` reads (`.amount`/`.category`).
* **Why it's expensive:** building SQLAlchemy ORM objects (identity map, state, instrumentation) costs
  ~100× more than reading scalar values. The actual SQL (`fetchall`) is only **0.34s of 4.46s (~8%)**;
  ~90% of the time is Python-side object hydration + attribute access. It also transfers all N rows
  over the cursor and scales O(N).
* **Why it matters:** a dashboard "summary" call blocks ~280 ms and degrades linearly as data grows —
  a latent latency/throughput incident as the table fills.
* **Expected gain:** pushing the aggregation into SQL (`GROUP BY`) returns **one row per category** (6)
  instead of 50,000 objects, eliminating the hydration entirely → expected order-of-magnitude win.

## Code Change

Minimal, single-function change (plus one import) — no architecture change.
**File:** `Advanced/parallel-expense-tracker/app/routes.py`
```diff
+from sqlalchemy import func
 ...
 @router.get("/summary", response_model=Summary)
 def summary(db: Session = Depends(get_db)):
-    expenses = db.query(Expense).all()
-    total = sum(e.amount for e in expenses)
-    by_category: dict = {}
-    for e in expenses:
-        by_category[e.category] = by_category.get(e.category, 0) + e.amount
-    return Summary(total=total, count=len(expenses), by_category=by_category)
+    rows = (
+        db.query(Expense.category, func.sum(Expense.amount), func.count(Expense.id))
+        .group_by(Expense.category)
+        .all()
+    )
+    by_category = {cat: float(cat_total) for cat, cat_total, _ in rows}
+    total = float(sum(by_category.values()))
+    count = sum(cat_count for _, _, cat_count in rows)
+    return Summary(total=total, count=count, by_category=by_category)
```
Querying columns (not the entity) returns lightweight tuples, so no ORM objects are built; the DB
does the sum/count/group.

## Before Metrics
* p50 latency: **278.64 ms** (mean 279.60, p95 301.36) at N=50k.
* cProfile: **4.455 s** / **10,046,725** function calls for 10 calls; hotspot = ORM `_instance` (1.157s tottime).

## After Metrics
```text
/api/summary latency over 15 runs (N=50000):
  min = 19.52 ms   p50 = 20.26 ms   p95 = 21.38 ms   max = 21.38 ms   mean = 20.32 ms
# cProfile (10 calls): 48007 function calls in 0.229 seconds
#   0.152s sqlite 'execute'  +  0.043s 'fetchall'   (ORM hydration gone)
```

## Improvement %
| Metric | Before | After | Δ |
|---|---|---|---|
| p50 latency | 278.64 ms | 20.26 ms | **−92.7%** (13.75× faster) |
| mean latency | 279.60 ms | 20.32 ms | −92.7% |
| cProfile wall (10 calls) | 4.455 s | 0.229 s | −94.9% |
| Function calls (10 calls) | 10,046,725 | 48,007 | **−99.5%** (209× fewer) |
| Rows materialized per call | 50,000 ORM objects | 6 tuples | −99.99% |

Improvement % = (278.64 − 20.26) / 278.64 = **92.7%**.

## Risk Assessment
**Low.** The change is one function + one import; the API contract (`Summary{total,count,by_category}`)
is unchanged. Risks considered and cleared:
* **Numeric equivalence:** SQL `SUM` over `REAL` matches the prior Python float sum — verified identical
  (`total=12550000.00`, `count=50000`, 6 categories) before and after.
* **Empty table:** `GROUP BY` returns no rows → `by_category={}`, `total=0.0`, `count=0` — covered by
  the existing `test_*` empty-summary test (still green).
* **Float-for-money** remains a pre-existing concern (flagged separately in A5-4) — out of scope for
  this perf change; the optimization neither helps nor worsens it.
No architecture, schema, or dependency change.

## Behavior Verification
```text
$ pytest -q          # A2 suite (12 API + 4 integration)
16 passed, 3 warnings in 0.12s
```
Plus the benchmark's built-in correctness assertion (`count=50000, total=12550000.00, categories=6`)
returns identical values before and after the change.

---

## Agent vs Verified
* **Hypothesis (pre-measurement):** "the summary is slow because it loads all rows." — direction right, but *intuition is not evidence*.
* **Verified Bottleneck (cProfile):** ORM **object materialization** (`orm/loading.py:_instance` 1.157s tottime, 2,000,000 `attributes.__get__`), not the SQL (`fetchall` only 0.34s / 8%).
* **Suggested Optimization:** replace `query(Expense).all()` + Python loop with a SQL `GROUP BY` aggregation.
* **Verified Optimization:** measured **92.7%** p50 latency reduction (278.64 → 20.26 ms) and 209× fewer function calls; **16/16 tests pass**, output byte-identical.

## Completion Criteria
- [x] Baseline measured (p50 278.64 ms, N=50k)
- [x] Profiling completed (cProfile — ORM hydration hotspot)
- [x] Bottleneck identified (object materialization, not SQL)
- [x] Small change implemented (1 function + 1 import, SQL GROUP BY)
- [x] Improvement measured (−92.7% p50, −94.9% profile wall)
- [x] Tests passed (16/16)
- [x] `A6_performance_improvement.md`
