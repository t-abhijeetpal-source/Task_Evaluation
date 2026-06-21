"""Tests for observability: /metrics endpoint and X-Request-ID correlation."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

PAYLOAD = {"amount": 100, "from": "USD", "to": "INR"}


@pytest.fixture
def client():
    return TestClient(app=create_app())


def test_metrics_endpoint_exposes_prometheus(client):
    # Generate at least one request so the counter is populated.
    client.post("/convert", json=PAYLOAD)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    body = resp.text
    assert "http_requests_total" in body
    assert "http_request_duration_seconds" in body


def test_response_has_request_id(client):
    resp = client.post("/convert", json=PAYLOAD)
    assert resp.status_code == 200
    assert resp.headers.get("x-request-id")  # present and non-empty


def test_request_id_is_propagated_when_supplied(client):
    resp = client.post(
        "/convert", json=PAYLOAD, headers={"X-Request-ID": "trace-abc-123"}
    )
    assert resp.headers["x-request-id"] == "trace-abc-123"


def test_health_also_carries_request_id(client):
    resp = client.get("/health")
    assert resp.headers.get("x-request-id")
