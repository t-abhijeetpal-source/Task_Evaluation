-- migration 0001: initial schema
-- Agent Generated
-- Creates the expenses table and its supporting indexes. Applied at app startup
-- (app/main.py lifespan -> app.database.run_migrations) and in the test suite, so
-- the CHECK constraints and indexes are guaranteed present at runtime.
-- Idempotent: safe to run on every boot (IF NOT EXISTS throughout).

CREATE TABLE IF NOT EXISTS expenses (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
    category     TEXT    NOT NULL CHECK(length(category) > 0),
    note         TEXT    NOT NULL DEFAULT '',
    created_at   TEXT    NOT NULL   -- ISO-8601 UTC
);

CREATE INDEX IF NOT EXISTS idx_expenses_category   ON expenses(category);
CREATE INDEX IF NOT EXISTS idx_expenses_created_at ON expenses(created_at);
