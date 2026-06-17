from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_add_endpoint():
    r = client.get("/add", params={"a": 2, "b": 3})
    assert r.status_code == 200
    body = r.json()
    assert body["sum"] == 5
    assert body["even"] is False
