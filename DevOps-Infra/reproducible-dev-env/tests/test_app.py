"""Tests that must pass on a clean machine after a single bootstrap command."""

import sys

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_runtime_is_pinned_312():
    # Proves the venv runs the mise-pinned Python (3.12.x), not the host default.
    assert sys.version_info[:2] == (3, 12)


def test_add_endpoint():
    r = client.get("/add", params={"a": 2, "b": 3})
    assert r.status_code == 200
    assert r.json() == {"a": 2, "b": 3, "sum": 5, "even": False}


def test_add_validation():
    r = client.get("/add", params={"a": "x", "b": 3})
    assert r.status_code == 422
