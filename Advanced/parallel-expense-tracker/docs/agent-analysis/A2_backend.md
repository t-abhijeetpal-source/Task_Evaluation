# A2 Backend — Expense Tracker (FastAPI + SQLAlchemy + SQLite)

> **Agent Generated.** This document and the backend implementation it describes were authored by an automated coding agent (Claude Code) as the Backend Engineer in a parallel build.

## Overview

A FastAPI backend exposing a small Expense Tracker API backed by SQLAlchemy ORM
over a SQLite database. The app also serves a static frontend from `/`.

Authored files (all paths absolute):

- `/Users/abhijeetpal/Desktop/workspace/Tasks/Advanced/parallel-expense-tracker/app/__init__.py`
- `/Users/abhijeetpal/Desktop/workspace/Tasks/Advanced/parallel-expense-tracker/app/database.py`
- `/Users/abhijeetpal/Desktop/workspace/Tasks/Advanced/parallel-expense-tracker/app/models.py`
- `/Users/abhijeetpal/Desktop/workspace/Tasks/Advanced/parallel-expense-tracker/app/schemas.py`
- `/Users/abhijeetpal/Desktop/workspace/Tasks/Advanced/parallel-expense-tracker/app/routes.py`
- `/Users/abhijeetpal/Desktop/workspace/Tasks/Advanced/parallel-expense-tracker/app/main.py`
- `/Users/abhijeetpal/Desktop/workspace/Tasks/Advanced/parallel-expense-tracker/requirements.txt`

## Endpoints

| Method | Path            | Request Body    | Success                          | Notes                                                        |
|--------|-----------------|-----------------|----------------------------------|--------------------------------------------------------------|
| GET    | `/api/health`   | —               | `200 {"status":"ok"}`            | Liveness check.                                              |
| POST   | `/api/expenses` | `ExpenseCreate` | `201 ExpenseOut`                 | `amount <= 0` returns `422 {"error":"amount must be positive"}`. `created_at` set to UTC ISO-8601. |
| GET    | `/api/expenses` | —               | `200 list[ExpenseOut]`           | Ordered newest first (`id` descending).                     |
| GET    | `/api/summary`  | —               | `200 Summary`                    | `total`, `count`, and `by_category` map of category → summed amount. |

All endpoints are mounted under the `APIRouter(prefix="/api")` defined in
`/Users/abhijeetpal/Desktop/workspace/Tasks/Advanced/parallel-expense-tracker/app/routes.py`.

## Data Model

Table `expenses` (defined in `app/models.py`):

| Column       | Type    | Constraints                          |
|--------------|---------|--------------------------------------|
| `id`         | INTEGER | PRIMARY KEY, autoincrement           |
| `amount`     | REAL    | NOT NULL, `> 0` enforced at the API  |
| `category`   | TEXT    | NOT NULL                             |
| `note`       | TEXT    | nullable, default `''`               |
| `created_at` | TEXT    | NOT NULL, ISO-8601 UTC string        |

## Layering

The code is organized into clear, single-responsibility layers:

1. **Persistence / config** — `app/database.py`: builds the `engine`,
   `SessionLocal` factory, declarative `Base`, and the `get_db()` dependency
   that yields a session and guarantees it is closed in a `finally` block.
2. **ORM models** — `app/models.py`: the `Expense` SQLAlchemy model mapping the
   `expenses` table.
3. **Validation / serialization** — `app/schemas.py`: Pydantic v2 models
   (`ExpenseCreate`, `ExpenseOut`, `Summary`). `ExpenseOut` uses
   `ConfigDict(from_attributes=True)` so ORM rows serialize directly.
4. **Routing / business logic** — `app/routes.py`: the `APIRouter` with the four
   endpoints, depending on `get_db` for session injection.
5. **Application assembly** — `app/main.py`: builds the `FastAPI` app, creates
   tables on startup, includes the router, then mounts static assets.

## Validation

- **Schema-level**: FastAPI + Pydantic v2 validate request bodies against
  `ExpenseCreate` (types coerced/validated for `amount`, `category`, `note`).
- **Business rule**: positive-amount enforcement lives in the route handler. A
  non-positive `amount` short-circuits with
  `JSONResponse(status_code=422, content={"error": "amount must be positive"})`
  rather than relying on a Pydantic constraint, matching the exact contract.
- `note` defaults to `""` both in the schema (`Optional[str] = ""`) and at write
  time (`payload.note or ""`), so a null/omitted note is stored as an empty
  string.

## How `DATABASE_URL` works

Defined in `app/database.py`:

```python
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/expenses.db")
```

- If the `DATABASE_URL` environment variable is set, that connection string is
  used as-is (e.g. point at Postgres or a different SQLite path).
- If unset, it defaults to the local SQLite file `./data/expenses.db`, and the
  `./data` directory is created with `os.makedirs("./data", exist_ok=True)` so
  the file has somewhere to live.
- For any SQLite URL, the engine is created with
  `connect_args={"check_same_thread": False}` so connections can be shared
  across FastAPI's threadpool. Non-SQLite URLs get no special connect args.

Tables are created on app startup via
`Base.metadata.create_all(bind=engine)` in `app/main.py`.

## Static Frontend

`app/main.py` includes the API router first, then calls
`app.mount("/", StaticFiles(directory="static", html=True), name="static")`.
Because the router is registered before the catch-all static mount, `/api/*`
requests reach the API while everything else is served from the `static/`
directory (with `index.html` served for `/`).
