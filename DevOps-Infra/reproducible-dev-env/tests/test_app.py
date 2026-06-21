"""HTTP-surface tests — must pass on a clean machine after a single bootstrap."""

from fastapi.testclient import TestClient

from app.middleware.security import SECURITY_HEADERS
from app.schemas import OPERAND_LIMIT


def test_health_ok(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    # /health echoes the live runtime + the declared env, proving the pin is live.
    assert body["python"].startswith("3.12")
    assert body["app_env"]  # APP_ENV is declared (mise.toml / devcontainer)
    assert body["version"]


def test_security_headers_on_every_response(client: TestClient) -> None:
    r = client.get("/health")
    for header, value in SECURITY_HEADERS.items():
        assert r.headers.get(header) == value
    # Every response is correlatable.
    assert r.headers.get("X-Request-ID")


def test_add_v1_canonical(client: TestClient) -> None:
    r = client.post("/v1/add", json={"a": 2, "b": 3})
    assert r.status_code == 200
    assert r.json() == {"a": 2, "b": 3, "sum": 5, "even": False}


def test_add_v1_even(client: TestClient) -> None:
    r = client.post("/v1/add", json={"a": 2, "b": 4})
    assert r.status_code == 200
    assert r.json()["even"] is True


def test_add_v1_rejects_unknown_keys(client: TestClient) -> None:
    r = client.post("/v1/add", json={"a": 1, "b": 2, "c": 3})
    assert r.status_code == 422


def test_add_v1_rejects_out_of_range(client: TestClient) -> None:
    r = client.post("/v1/add", json={"a": OPERAND_LIMIT + 1, "b": 0})
    assert r.status_code == 422


def test_add_legacy_still_works(client: TestClient) -> None:
    r = client.get("/add", params={"a": 2, "b": 3})
    assert r.status_code == 200
    assert r.json() == {"a": 2, "b": 3, "sum": 5, "even": False}


def test_add_legacy_validation(client: TestClient) -> None:
    r = client.get("/add", params={"a": "x", "b": 3})
    assert r.status_code == 422


def test_add_legacy_out_of_range(client: TestClient) -> None:
    r = client.get("/add", params={"a": OPERAND_LIMIT + 1, "b": 0})
    assert r.status_code == 422


def test_metrics_endpoint(client: TestClient) -> None:
    # Drive one request so a counter is non-zero, then scrape.
    client.get("/health")
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "http_requests_total" in r.text
