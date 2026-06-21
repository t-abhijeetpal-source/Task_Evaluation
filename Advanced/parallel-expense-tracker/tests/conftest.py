"""Pytest fixtures for the Expense Tracker test suite.

CRITICAL: the temp SQLite database is configured at the TOP of this file,
*before* the application (and its `engine`) are imported. The app reads
DATABASE_URL at import time in app/database.py, so the env var must be set
first to guarantee tests never touch the real ./data/expenses.db file.

The test schema is created by the SAME migration runner the app uses at
startup (app.database.run_migrations), so tests exercise the real runtime
schema — CHECK constraints and indexes included — not an ORM approximation.
"""

import os
import shutil
import tempfile

# ---------------------------------------------------------------------------
# 1. Point the app at an isolated temp SQLite DB BEFORE importing anything
#    from the app package. This must happen first.
# ---------------------------------------------------------------------------
_TMP_DIR = tempfile.mkdtemp(prefix="expense_test_")
_DB_PATH = os.path.join(_TMP_DIR, "test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB_PATH

# ---------------------------------------------------------------------------
# 2. Now it is safe to import the app, which will bind its engine to the
#    temp DATABASE_URL set above.
# ---------------------------------------------------------------------------
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.database import engine, run_migrations  # noqa: E402
from app.models import Expense  # noqa: E402  (registers the ORM mapping)


@pytest.fixture()
def client():
    """A FastAPI TestClient bound to the app (temp DB)."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def _reset_database():
    """Reset to an empty, migration-applied schema before each test.

    Dropping the table and re-running the migrations (rather than ORM
    create_all) keeps every test on the exact runtime schema, so list ordering
    and summary aggregation assertions are deterministic and order-independent.
    """
    with engine.begin() as conn:
        from sqlalchemy import text

        conn.execute(text("DROP TABLE IF EXISTS expenses"))
    run_migrations(engine)
    yield


def pytest_sessionfinish(session, exitstatus):
    """Dispose the engine and remove the temp DB dir (no leaked tmp files)."""
    engine.dispose()
    shutil.rmtree(_TMP_DIR, ignore_errors=True)
