# A2 Expense Tracker — Locked API & Data Contract

> Single source of truth for the API surface, money representation, validation
> rules, and schema. If code and this document disagree, **that is a bug** — the
> `make a2-verify` gate (pytest + live integration smoke) exists to keep them in
> sync. Last reconciled: 2026-06-21, Python 3.12.7, FastAPI + SQLAlchemy 2 + SQLite.

## 1. Money representation (read this first)

- Money is **stored and aggregated as an integer number of cents**
  (`amount_cents`, SQLite `INTEGER`). There is **no float column**. Summation
  happens in SQL over integers, so totals are exact — `0.10 + 0.20` is `0.30`,
  never `0.30000000000000004`.
- On the **wire**, `amount` is a JSON number with at most 2 decimal places
  (e.g. `12.5`, `99.00`). It is derived from `amount_cents / 100` on output and
  parsed via `Decimal` on input.
- Inputs that cannot be exact money are **rejected with `422`**, never silently
  coerced or 500'd:
  - `NaN`, `Infinity`, `-Infinity` (even as raw JSON literals)
  - more than 2 decimal places (sub-cent)
  - magnitude `> 10,000,000,000`
  - non-positive amounts (see the dedicated error below)

## 2. Endpoints

Base URL: `http://localhost:8000`. All API paths are prefixed with `/api`.

### `GET /api/health` — deep health
- `200 {"status":"ok"}` when the process **and** the database are reachable
  (a `SELECT 1` round-trip succeeds).
- `503 {"status":"unavailable","detail":"database unreachable"}` if the DB
  round-trip fails. Docker/K8s probes act on this.

### `POST /api/expenses` — create
Request body:
```json
{ "amount": 12.50, "category": "food", "note": "lunch" }
```
- `amount` (required): positive number/numeric-string, ≤ 2 dp, ≤ 1e10, finite.
- `category` (required): non-empty string, **trimmed and lowercased**, ≤ 64 chars.
- `note` (optional): string, trimmed, ≤ 255 chars, defaults to `""`.

Responses:
| Status | Body | When |
|---|---|---|
| `201` | `{"id","amount","category","note","created_at"}` | created |
| `422` | `{"error":"amount must be positive"}` | `amount <= 0` |
| `422` | `{"detail":[{"loc","msg","type"}]}` | any other invalid field (NaN, sub-cent, overflow, missing/typed, empty/over-long category, over-long note) |

`created_at` is server-generated ISO-8601 UTC.

### `GET /api/expenses` — list (newest first, paginated)
- Query params: `limit` (default `100`, `1..1000`), `offset` (default `0`, `>=0`).
  Out-of-range values → `422`.
- `200` → array of expense objects ordered by `id` descending.

### `GET /api/summary` — aggregate
- `200 {"total":<number>,"count":<int>,"by_category":{<category>:<number>}}`
- Totals computed via SQL `GROUP BY` over integer cents (exact; A6-optimized,
  indexed on `category`). Empty DB → `{"total":0,"count":0,"by_category":{}}`.

### `GET /` and `GET /app.js` — static frontend
- `200` HTML / JS. The API router is registered **before** the static mount so
  `/api/*` is never swallowed by the static handler.

## 3. Data schema (runtime, not aspirational)

The runtime schema is applied at startup by `app.database.run_migrations`
(executes `db/migrations/*.sql`) — **not** `Base.metadata.create_all`. So the
`CHECK` constraints and indexes below exist at runtime and are enforced by the
DB. `tests/test_schema_honesty.py` asserts this against the live database.

```sql
CREATE TABLE expenses (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
    category     TEXT    NOT NULL CHECK(length(category) > 0),
    note         TEXT    NOT NULL DEFAULT '',
    created_at   TEXT    NOT NULL
);
CREATE INDEX idx_expenses_category   ON expenses(category);
CREATE INDEX idx_expenses_created_at ON expenses(created_at);
```

## 4. Known limitations (honest)

- **No authentication.** Full public CRUD and `/docs` are exposed. This is a
  demo/single-tenant default — add an API key / reverse-proxy auth before any
  non-local exposure. (See README → Security.)
- **SQLite single-writer.** Fine for a single instance; move to Postgres for
  high-concurrency or multi-replica deploys.
- **Forward-only migrations.** `run_migrations` applies `IF NOT EXISTS` DDL; it
  does not alter a pre-existing table created under a different schema. Start
  from a fresh DB file when upgrading from the legacy float schema.
