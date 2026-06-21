"""Tests for the security baseline: CORS, security headers, rate limit, body cap."""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

PAYLOAD = {"amount": 100, "from": "USD", "to": "INR"}


@pytest.fixture
def client():
    return TestClient(app=create_app())


# --- Security headers -----------------------------------------------------
def test_security_headers_on_convert(client):
    resp = client.post("/convert", json=PAYLOAD)
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert resp.headers["referrer-policy"] == "no-referrer"
    assert "default-src 'none'" in resp.headers["content-security-policy"]


def test_security_headers_on_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers["x-content-type-options"] == "nosniff"


# --- CORS -----------------------------------------------------------------
def test_cors_allows_configured_origin():
    app = create_app(Settings(cors_origins=["http://allowed.example"]))
    client = TestClient(app=app)
    resp = client.options(
        "/convert",
        headers={
            "Origin": "http://allowed.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "http://allowed.example"


def test_cors_omits_header_for_disallowed_origin():
    app = create_app(Settings(cors_origins=["http://allowed.example"]))
    client = TestClient(app=app)
    resp = client.post(
        "/convert", json=PAYLOAD, headers={"Origin": "http://evil.example"}
    )
    # Request still processed, but no allow-origin granted to the bad origin.
    assert resp.headers.get("access-control-allow-origin") != "http://evil.example"


def test_cors_fails_closed_in_production():
    settings = Settings(env="production")  # CORS_ORIGINS unset
    assert settings.resolved_cors_origins == []


# --- Rate limiting --------------------------------------------------------
def test_rate_limit_triggers_429():
    app = create_app(Settings(rate_limit_per_minute=3))
    client = TestClient(app=app)
    for _ in range(3):
        assert client.post("/convert", json=PAYLOAD).status_code == 200
    resp = client.post("/convert", json=PAYLOAD)
    assert resp.status_code == 429
    assert resp.json() == {"error": "Rate limit exceeded"}
    assert "retry-after" in resp.headers


def test_health_exempt_from_rate_limit():
    app = create_app(Settings(rate_limit_per_minute=2))
    client = TestClient(app=app)
    for _ in range(10):
        assert client.get("/health").status_code == 200


# --- Body size limit ------------------------------------------------------
def test_oversized_body_rejected_413():
    app = create_app(Settings(max_body_bytes=64))
    client = TestClient(app=app)
    big = {"amount": 100, "from": "USD", "to": "INR", "padding": "x" * 200}
    resp = client.post("/convert", json=big)
    assert resp.status_code == 413
    assert resp.json() == {"error": "Request body too large"}
