-- Agent Generated
-- Canonical schema for the expenses tracker (SQLite).
-- This is the SINGLE SOURCE OF TRUTH for the runtime schema: app startup and the
-- test suite both apply db/migrations/*.sql (which is identical to this file), so
-- the CHECK constraint and indexes below exist at RUNTIME — not just on paper.
-- The SQLAlchemy ORM in app/models.py mirrors these columns for query mapping.
--
-- Money is stored as an INTEGER number of cents (amount_cents) to avoid binary
-- floating-point error in storage and aggregation. The API presents a 2-decimal
-- number on the wire; conversion happens at the application boundary.

CREATE TABLE IF NOT EXISTS expenses (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
    category     TEXT    NOT NULL CHECK(length(category) > 0),
    note         TEXT    NOT NULL DEFAULT '',
    created_at   TEXT    NOT NULL   -- ISO-8601 UTC
);

CREATE INDEX IF NOT EXISTS idx_expenses_category   ON expenses(category);
CREATE INDEX IF NOT EXISTS idx_expenses_created_at ON expenses(created_at);
