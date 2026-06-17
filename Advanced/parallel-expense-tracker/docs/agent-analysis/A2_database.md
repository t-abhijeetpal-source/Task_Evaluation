# A2 Database Design

> **Agent Generated** — authored by the Database Engineer agent in the A2 parallel build.

## Overview

The application uses a single-table SQLite schema to persist expense records. The
canonical DDL lives in `db/schema.sql`, with an equivalent initial migration in
`db/migrations/0001_init.sql`. The schema is locked to match the SQLAlchemy ORM in
`app/models.py` exactly.

## Table: `expenses`

| Column       | Type    | Constraints                          | Notes                          |
|--------------|---------|--------------------------------------|--------------------------------|
| `id`         | INTEGER | PRIMARY KEY AUTOINCREMENT            | Surrogate key                  |
| `amount`     | REAL    | NOT NULL, CHECK(amount > 0)          | Must be strictly positive      |
| `category`   | TEXT    | NOT NULL                             | e.g. food / transport / utilities |
| `note`       | TEXT    | DEFAULT ''                           | Optional free-text, empty by default |
| `created_at` | TEXT    | NOT NULL                             | ISO-8601 UTC timestamp string  |

### Constraint rationale
- `CHECK(amount > 0)` enforces a positive monetary value at the DB layer, defending
  against bad inserts even if application validation is bypassed.
- `note` defaults to `''` so the column is never NULL for omitted notes, matching the
  ORM default.
- `created_at` is stored as an ISO-8601 UTC string (TEXT) for portability and
  lexicographic-equals-chronological ordering.

## Indexes

| Index                     | Column       | Rationale                                              |
|---------------------------|--------------|--------------------------------------------------------|
| `idx_expenses_category`   | `category`   | Speeds up filtering/grouping by category (reports, summaries). |
| `idx_expenses_created_at` | `created_at` | Speeds up date-range queries and chronological sorts; ISO-8601 strings sort correctly. |

## Migration approach

Migrations are plain, ordered SQL files under `db/migrations/`, applied in filename
order (`0001_init.sql`, then `0002_...`, etc.). Each file is idempotent where practical
(`CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`) so re-running is safe.
The initial migration carries the header comment `-- migration 0001: initial schema`
and is identical in effect to `db/schema.sql`.

## Mapping to the SQLAlchemy model

The DDL maps 1:1 onto `app/models.py`:

| SQL column / constraint              | ORM field (`Expense`)                          |
|--------------------------------------|------------------------------------------------|
| `id INTEGER PK AUTOINCREMENT`        | `id = Column(Integer, primary_key=True, autoincrement=True)` |
| `amount REAL NOT NULL CHECK(>0)`     | `amount = Column(Float, nullable=False)`       |
| `category TEXT NOT NULL`             | `category = Column(String, nullable=False)`    |
| `note TEXT DEFAULT ''`               | `note = Column(String, nullable=True, default="")` |
| `created_at TEXT NOT NULL`           | `created_at = Column(String, nullable=False)`  |

SQLAlchemy's `Float` maps to SQLite `REAL`; `String` maps to `TEXT`. The `CHECK(amount > 0)`
is a DB-level guard not expressed in the ORM column definitions, so application code
should still validate positivity before insert.

## How to apply

```sh
# Create / initialize the database from the canonical schema
sqlite3 data/expenses.db < db/schema.sql

# (Optional) load sample data for local development
sqlite3 data/expenses.db < db/seed.sql

# Alternatively, apply via migrations in order
sqlite3 data/expenses.db < db/migrations/0001_init.sql
```
