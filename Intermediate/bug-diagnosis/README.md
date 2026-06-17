# I6 — Orders Service (Bug Diagnosis Exercise)

A small layered FastAPI orders service used to demonstrate the full bug-diagnosis workflow:
**reproduce → root-cause → minimal fix → verify**.

The business rules are in `SPEC.md`. The diagnosis report is in
`docs/agent-analysis/I6_bug_diagnosis.md`.

> A realistic off-by-one boundary bug (bulk discount at `qty == 10`) was *seeded* into
> `app/services.py`, reproduced via a failing test, root-caused, fixed (one operator), and
> verified. The repo here contains the **fixed** code; the report shows the before/after evidence.

## Structure

```text
I6/
├── app/
│   ├── main.py        # FastAPI app + /health
│   ├── routes.py      # POST /orders, GET /orders/{id}/total
│   ├── schemas.py     # Item / Order schemas
│   ├── services.py    # bulk-discount + total logic (defect was here)
│   └── storage.py     # in-memory order store
├── tests/test_orders.py
├── SPEC.md            # business rules (defines expected behavior)
├── requirements.txt
└── docs/agent-analysis/I6_bug_diagnosis.md
```

## Install & Run

```bash
cd I6
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload          # http://127.0.0.1:8000/docs
```

## Test

```bash
pytest -v
```

Expected: **5 passed** (the fix is applied). To see the bug reproduced, revert the operator in
`app/services.py` (`>=` → `>`) and re-run — 3 tests fail at the `qty == 10` boundary.

## The bug, in one line

```diff
# app/services.py, calculate_line_total
-    if item.qty > BULK_QTY_THRESHOLD:    # excludes qty == 10  (bug)
+    if item.qty >= BULK_QTY_THRESHOLD:   # includes qty == 10  (per SPEC rule 3)
```
