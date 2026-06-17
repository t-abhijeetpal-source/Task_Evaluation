"""Pytest fixtures for the Expense Tracker test suite.

CRITICAL: the temp SQLite database is configured at the TOP of this file,
*before* the application (and its `engine`) are imported. The app reads
DATABASE_URL at import time in app/database.py, so the env var must be set
first to guarantee tests never touch the real ./data/expenses.db file.
"""

import os
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
from app.database import engine, Base  # noqa: E402


@pytest.fixture()
def client():
    """A FastAPI TestClient bound to the app (temp DB)."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def _reset_database():
    """Drop and recreate all tables before each test for full isolation.

    Running before every test guarantees each test starts from an empty
    schema, so list ordering / summary aggregation assertions are
    deterministic and independent of execution order.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
