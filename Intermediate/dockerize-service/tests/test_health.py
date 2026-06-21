"""Tests for the K8s-style liveness (/health) and readiness (/ready) probes."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    return TestClient(app=create_app())


# --- Liveness -------------------------------------------------------------
def test_health_liveness_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    # Backward compatible: existing scripts still see status == "ok".
    assert "version" in body
    assert "build" in body


# --- Readiness ------------------------------------------------------------
def test_ready_ok_in_normal_state(client):
    resp = client.get("/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["version"] and body["build"]


def test_ready_503_when_rates_missing(client, monkeypatch):
    # Synthetic failure hook: empty the rates table -> not ready.
    from currency_core import services

    monkeypatch.setattr(services, "RATES", {})
    resp = client.get("/ready")
    assert resp.status_code == 503
    assert resp.json()["status"] == "not ready"
