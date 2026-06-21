"""Proves the RUNTIME schema carries the guards the docs claim.

The previous build ran ``Base.metadata.create_all`` at startup, which emits
neither the CHECK constraint nor the indexes — so docs claiming "DB schema with
CHECK reconciled" were false at runtime. These tests introspect the live DB the
app actually uses (migration-applied) and assert the guards are really there and
really enforced.
"""

import sqlite3

import pytest
from sqlalchemy import text

from app.database import engine


def _expenses_ddl() -> str:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT sql FROM sqlite_master WHERE type='table' AND name='expenses'")
        ).fetchone()
    assert row is not None, "expenses table missing from runtime schema"
    return row[0]


def test_runtime_table_has_amount_positive_check():
    ddl = _expenses_ddl().lower()
    assert "check" in ddl
    assert "amount_cents > 0" in ddl


def test_runtime_table_uses_integer_cents_not_float():
    ddl = _expenses_ddl().lower()
    assert "amount_cents" in ddl
    assert "integer" in ddl
    # The old, buggy float column must be gone.
    assert "amount real" not in ddl and "amount float" not in ddl


def test_runtime_schema_has_supporting_indexes():
    with engine.connect() as conn:
        names = {
            r[0]
            for r in conn.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='index' AND tbl_name='expenses'"
                )
            ).fetchall()
        }
    assert "idx_expenses_category" in names
    assert "idx_expenses_created_at" in names


def test_db_check_constraint_is_enforced():
    """The CHECK must actually reject a non-positive amount at the DB layer."""
    with pytest.raises((sqlite3.IntegrityError, Exception)):
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO expenses (amount_cents, category, created_at) "
                    "VALUES (-1, 'x', '2026-01-01T00:00:00Z')"
                )
            )
