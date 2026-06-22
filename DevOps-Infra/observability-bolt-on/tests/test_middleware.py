"""Tests for the observability + security middleware."""

from fastapi.testclient import TestClient

from app.metrics import REGISTRY


def test_request_id_header_is_hex_uuid(client: TestClient) -> None:
    r = client.get("/health")
    request_id = r.headers["X-Request-ID"]
    assert len(request_id) == 32
    int(request_id, 16)  # raises if not hex


def test_request_ids_are_unique_per_request(client: TestClient) -> None:
    a = client.get("/health").headers["X-Request-ID"]
    b = client.get("/health").headers["X-Request-ID"]
    assert a != b


def test_unmatched_route_uses_normalized_label(client: TestClient) -> None:
    """404 paths collapse to a single low-cardinality /_unmatched label."""
    r = client.get("/this-route-does-not-exist")
    assert r.status_code == 404
    assert REGISTRY.get_sample_value(
        "http_requests_total",
        {"method": "GET", "path": "/_unmatched", "status_code": "404"},
    )
    # The raw junk path must NOT have become its own series.
    assert (
        REGISTRY.get_sample_value(
            "http_requests_total",
            {"method": "GET", "path": "/this-route-does-not-exist", "status_code": "404"},
        )
        is None
    )


def test_security_headers_present_on_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Referrer-Policy"] == "no-referrer"
    assert r.headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert "Permissions-Policy" in r.headers


def test_security_headers_present_on_error(client: TestClient) -> None:
    r = client.get("/error")
    assert r.status_code == 500
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Request-ID" in r.headers
