"""Endpoint behaviour tests for the instrumented D6 service."""

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
    # Middleware stamps every response with a trace id.
    assert "X-Request-ID" in r.headers


def test_ready(client: TestClient) -> None:
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json() == {"status": "ready"}


def test_root_service_info(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["service"] == "d6-sample"


def test_add_endpoint(client: TestClient) -> None:
    r = client.get("/add", params={"a": 2, "b": 3})
    assert r.status_code == 200
    assert r.json() == {"a": 2, "b": 3, "sum": 5, "even": False}


def test_add_validation_error_counts(client: TestClient) -> None:
    r = client.get("/add", params={"a": "x", "b": 3})
    assert r.status_code == 422


def test_error_endpoint_returns_500(client: TestClient) -> None:
    r = client.get("/error")
    assert r.status_code == 500
    assert r.json()["detail"] == "internal server error"
    # The 500 envelope echoes the request id for support correlation.
    assert r.json()["request_id"] == r.headers["X-Request-ID"]


def test_metrics_endpoint_exposes_counters(client: TestClient) -> None:
    # Generate some traffic first so counters are non-zero.
    client.get("/health")
    client.get("/add", params={"a": 1, "b": 1})
    r = client.get("/metrics")
    assert r.status_code == 200
    body = r.text
    assert "http_requests_total" in body
    assert "http_request_duration_seconds_bucket" in body
    assert "http_request_errors_total" in body
