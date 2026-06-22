"""Observability + security + auth middleware behaviour."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import app.main as main_module
import pytest
from app.metrics import REGISTRY
from fastapi.testclient import TestClient


def test_request_id_header_is_hex_uuid(client: TestClient) -> None:
    r = client.get("/health")
    request_id = r.headers["X-Request-ID"]
    assert len(request_id) == 32
    int(request_id, 16)  # raises if not hex


def test_request_ids_are_unique_per_request(client: TestClient) -> None:
    a = client.get("/health").headers["X-Request-ID"]
    b = client.get("/health").headers["X-Request-ID"]
    assert a != b


def test_security_headers_present(client: TestClient) -> None:
    r = client.get("/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Referrer-Policy"] == "no-referrer"
    assert r.headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert "Permissions-Policy" in r.headers


def test_unmatched_route_uses_normalized_label(client: TestClient) -> None:
    r = client.get("/this-route-does-not-exist")
    assert r.status_code == 404
    assert REGISTRY.get_sample_value(
        "http_requests_total",
        {"method": "GET", "path": "/_unmatched", "status_code": "404"},
    )
    assert (
        REGISTRY.get_sample_value(
            "http_requests_total",
            {"method": "GET", "path": "/this-route-does-not-exist", "status_code": "404"},
        )
        is None
    )


# ---- Optional X-API-Key gate -------------------------------------------------


def test_auth_disabled_by_default(client: TestClient) -> None:
    # No API_KEY in env (conftest deletes it) → protected routes are open.
    assert client.post("/jobs", json={"payload": "x"}).status_code == 201


def test_auth_rejects_missing_key(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "s3cret")
    r = client.post("/jobs", json={"payload": "x"})
    assert r.status_code == 401
    assert r.json()["detail"] == "invalid or missing API key"
    assert "X-Request-ID" in r.headers


def test_auth_rejects_wrong_key(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "s3cret")
    r = client.post("/jobs", json={"payload": "x"}, headers={"X-API-Key": "nope"})
    assert r.status_code == 401


def test_auth_accepts_correct_key(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "s3cret")
    r = client.post("/jobs", json={"payload": "x"}, headers={"X-API-Key": "s3cret"})
    assert r.status_code == 201


def test_auth_exempts_health_and_metrics(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("API_KEY", "s3cret")
    assert client.get("/health").status_code == 200
    assert client.get("/metrics").status_code == 200


# ---- Unhandled-error path ----------------------------------------------------


def test_unhandled_error_returns_500_with_request_id(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A non-psycopg failure inside a handler is caught by the middleware,
    surfaced as a sanitized 500, and recorded in the error counter."""

    @contextmanager
    def boom() -> Iterator[object]:
        raise RuntimeError("unexpected")
        yield  # pragma: no cover

    monkeypatch.setattr(main_module, "db_connection", boom)
    r = client.get("/jobs")
    assert r.status_code == 500
    body = r.json()
    assert body["detail"] == "internal server error"
    assert body["request_id"] == r.headers["X-Request-ID"]
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert (
        REGISTRY.get_sample_value(
            "http_request_errors_total",
            {"method": "GET", "path": "/jobs", "status_code": "500"},
        )
        is not None
    )
