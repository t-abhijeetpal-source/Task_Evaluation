import os
import tempfile

import pytest

# Set env BEFORE importing the app so database/queue/token pick up test values.
_TMP = tempfile.mkdtemp(prefix="a3_fastapi_test_")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_TMP, "test.db")
os.environ["QUEUE_DIR"] = os.path.join(_TMP, "queue")
# A5-2 / A5-17: the internal callback is now fail-closed, so a token must be
# configured for the app under test. Tests send it via the `auth` fixture.
TEST_INTERNAL_TOKEN = "test-internal-token"
os.environ["A3_INTERNAL_TOKEN"] = TEST_INTERNAL_TOKEN

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app import models  # noqa: F401,E402
from app.main import app  # noqa: E402


@pytest.fixture()
def queue_dir():
    return os.environ["QUEUE_DIR"]


@pytest.fixture()
def auth():
    """Valid X-Internal-Token header for the internal scoring callback."""
    return {"X-Internal-Token": TEST_INTERNAL_TOKEN}


@pytest.fixture()
def client():
    # Recreate tables per test for isolation.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
