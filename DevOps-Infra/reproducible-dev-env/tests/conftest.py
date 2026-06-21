"""Shared pytest fixtures for the D5 service test suite."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """A FastAPI TestClient bound to the real app (exercises middleware too)."""
    with TestClient(app) as test_client:
        yield test_client
