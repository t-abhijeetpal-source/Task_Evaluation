"""Shared pytest fixtures for the D6 test suite."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A TestClient that surfaces 5xx as responses (not raised exceptions),
    so error-path metrics/logging can be asserted."""
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
