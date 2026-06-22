"""Tests for the observability middleware: security headers + request id."""

from fastapi.testclient import TestClient

from app.middleware.security import SECURITY_HEADERS


def test_security_headers_present_on_health(client: TestClient) -> None:
    r = client.get("/health")
    for header, value in SECURITY_HEADERS.items():
        assert r.headers.get(header) == value


def test_security_headers_present_on_all_routes(client: TestClient) -> None:
    for path in ("/", "/ready", "/add?a=1&b=2"):
        r = client.get(path)
        assert r.headers.get("X-Content-Type-Options") == "nosniff"
        assert r.headers.get("X-Frame-Options") == "DENY"


def test_request_id_echoed_and_unique(client: TestClient) -> None:
    r1 = client.get("/health")
    r2 = client.get("/health")
    id1 = r1.headers.get("X-Request-ID")
    id2 = r2.headers.get("X-Request-ID")
    assert id1 and id2
    assert id1 != id2  # a fresh id per request


def test_no_csp_header_so_swagger_docs_keep_working(client: TestClient) -> None:
    """A strict CSP would break /docs (CDN assets); confirm it is not set."""
    r = client.get("/health")
    assert "Content-Security-Policy" not in r.headers
