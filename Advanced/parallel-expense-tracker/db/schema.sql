-- Agent Generated
-- Canonical schema for the expenses tracker (SQLite).
-- Mirrors the SQLAlchemy ORM in app/models.py.

CREATE TABLE IF NOT EXISTS expenses (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    amount     REAL    NOT NULL CHECK(amount > 0),
    category   TEXT    NOT NULL,
    note       TEXT    DEFAULT '',
    created_at TEXT    NOT NULL   -- ISO-8601 UTC
);

CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);
CREATE INDEX IF NOT EXISTS idx_expenses_created_at ON expenses(created_at);
