"""Tests for the D4 workload — run before building the image."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ready():
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json() == {"status": "ready"}


def test_root_surfaces_config():
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "d4-sample"
    # env/greeting/version come from env (ConfigMap in-cluster, defaults locally).
    assert {"env", "greeting", "version"} <= body.keys()


def test_add_endpoint():
    r = client.get("/add", params={"a": 2, "b": 3})
    assert r.status_code == 200
    assert r.json() == {"a": 2, "b": 3, "sum": 5, "even": False}


def test_add_validation_rejects_non_int():
    r = client.get("/add", params={"a": "x", "b": 3})
    assert r.status_code == 422
