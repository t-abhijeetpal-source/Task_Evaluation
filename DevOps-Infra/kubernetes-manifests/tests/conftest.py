"""Shared pytest fixtures for the D4 workload tests."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A TestClient bound to the app, used by every endpoint test."""
    with TestClient(app) as c:
        yield c
