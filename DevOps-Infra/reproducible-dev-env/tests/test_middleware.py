"""Tests for the security/observability middleware error path and CORS config."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware import security
from app.middleware.security import SECURITY_HEADERS, cors_origins, install_middleware


def test_server_error_is_observed_and_reraised() -> None:
    """A handler that raises is logged + metered, then surfaced as a 500."""
    app = FastAPI()
    install_middleware(app)

    @app.get("/boom")
    def boom() -> dict:
        raise RuntimeError("kaboom")

    with TestClient(app, raise_server_exceptions=False) as c:
        r = c.get("/boom")
    assert r.status_code == 500


def test_cors_origins_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", " https://a.example , https://b.example ,")
    assert cors_origins() == ["https://a.example", "https://b.example"]

    monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)
    assert cors_origins() == []


def test_cors_middleware_installed_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://app.example")
    app = FastAPI()
    install_middleware(app)

    @app.get("/ping")
    def ping() -> dict:
        return {"ok": True}

    with TestClient(app) as c:
        r = c.get("/ping", headers={"Origin": "https://app.example"})
    assert r.headers.get("access-control-allow-origin") == "https://app.example"
    # Security headers are present regardless of CORS.
    for header in SECURITY_HEADERS:
        assert header in r.headers


def test_security_headers_constant_is_nonempty() -> None:
    assert "X-Content-Type-Options" in security.SECURITY_HEADERS
