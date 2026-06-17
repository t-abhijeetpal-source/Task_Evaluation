# A2 — QA Analysis & Test Plan (Expense Tracker)

> **Agent Generated.** This plan and the accompanying test suite were authored
> by the QA agent in a parallel build. **Test results are NOT-YET-RUN** here —
> the coordinator executes the suite in Phase 4 and verifies pass/fail.

## Scope

Backend under test: FastAPI app at `app/main.py` with router `app/routes.py`,
SQLAlchemy models `app/models.py`, schemas `app/schemas.py`, DB wiring
`app/database.py`, and the static SPA shell served from `static/`.

Endpoints covered:

| Method & path        | Behaviour verified                                              |
|----------------------|-----------------------------------------------------------------|
| `GET /api/health`    | 200, body `{"status":"ok"}`                                     |
| `POST /api/expenses` | 201 + full body; 422 domain error on amount<=0; 422 validation on missing/bad fields |
| `GET /api/expenses`  | 200, list newest-first (descending id)                          |
| `GET /api/summary`   | 200, correct `total`, `count`, `by_category` aggregation        |
| `GET /`              | 200, HTML app shell from static mount                           |

## Isolation Strategy (temp DB)

The app reads `DATABASE_URL` **at import time** (`app/database.py` builds the
engine on import). To guarantee tests never touch the real
`./data/expenses.db`, `tests/conftest.py` does the following **at the very top
of the file, before any app import**:

1. `tempfile.mkdtemp()` -> a throwaway directory.
2. `os.environ["DATABASE_URL"] = "sqlite:///" + <tmp>/test.db`.
3. Only then `from app.main import app` and `from app.database import engine, Base`.

Per-test isolation is provided by an **autouse** fixture that runs
`Base.metadata.drop_all(bind=engine)` then `create_all(bind=engine)` before
every test, so each test starts from an empty schema. Ordering and aggregation
assertions are therefore deterministic and order-independent. The `client`
fixture wraps the app in a `fastapi.testclient.TestClient` (used as a context
manager so startup/shutdown events fire).

## Test Cases

### `tests/test_api.py` (unit / contract)
- `test_health_returns_ok` — health endpoint shape.
- `test_create_expense_returns_201_and_body` — 201 + id/amount/category/note/created_at present and correct.
- `test_create_expense_without_note_defaults_to_empty` — optional `note` defaults to `""`.
- `test_create_expense_rejects_zero_amount` — amount==0 -> 422 `{"error":"amount must be positive"}`.
- `test_create_expense_rejects_negative_amount` — amount<0 -> same 422 domain error.
- `test_create_expense_rejects_missing_amount` — missing required field -> 422.
- `test_create_expense_rejects_missing_category` — missing required field -> 422.
- `test_create_expense_rejects_bad_amount_type` — non-numeric amount -> 422.
- `test_list_expenses_empty` — empty DB -> `[]`.
- `test_list_expenses_newest_first` — three inserts return in descending-id order.
- `test_summary_empty` — empty DB -> `{total:0,count:0,by_category:{}}`.
- `test_summary_computes_totals_and_by_category` — 3 records across 2 categories; asserts total=35, count=3, by_category `{food:15, transport:20}`.

### `tests/test_integration.py` (full-stack-ish via TestClient)
- `test_root_serves_html_page` — `GET /` returns 200 + `text/html`, body looks like the app shell (`<html` plus a form/title/"expense" marker).
- `test_create_then_appears_in_list` — POST then the record surfaces in `GET /api/expenses` with matching fields.
- `test_create_then_reflected_in_summary` — POSTs are reflected in `GET /api/summary` totals.
- `test_full_round_trip_create_list_summary` — create several; verify newest-first list and aggregated summary together.

## How to Run

From the A2 base directory (so `app` is importable):

```bash
cd "Advanced/parallel-expense-tracker"
pytest -v
```

`pytest.ini` sets `testpaths = tests` and `python_files = test_*.py`, so a bare
`pytest` discovers the suite. Requires the backend deps (fastapi, sqlalchemy,
httpx for TestClient) and pytest installed in the environment.

## Expected Coverage

- **Endpoints:** all five backend routes plus the static `/` mount.
- **Happy paths:** create, list ordering, summary aggregation, round trips.
- **Error paths:** amount<=0 domain rule (zero and negative), missing `amount`,
  missing `category`, wrong-typed `amount`.
- **Edge cases:** empty list and empty summary; optional-note default.
- Total: **16 test functions** (12 API + 4 integration).

### Known dependency / caveat
- `test_root_serves_html_page` requires `static/index.html` to exist (built by
  the FE agent in parallel). If the static asset is absent at run time, this
  test will fail with 404 — expected to pass once the frontend is in place at
  Phase 4 integration.

---
_Status: tests authored, NOT-YET-RUN. Coordinator to execute `pytest -v` in Phase 4 and record results._
