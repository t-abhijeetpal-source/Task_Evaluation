import os
import tempfile

import pytest

# Set env BEFORE importing the app so database/queue pick up temp paths.
_TMP = tempfile.mkdtemp(prefix="a3_fastapi_test_")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_TMP, "test.db")
os.environ["QUEUE_DIR"] = os.path.join(_TMP, "queue")

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app import models  # noqa: F401,E402
from app.main import app  # noqa: E402


@pytest.fixture()
def queue_dir():
    return os.environ["QUEUE_DIR"]


@pytest.fixture()
def client():
    # Recreate tables per test for isolation.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
