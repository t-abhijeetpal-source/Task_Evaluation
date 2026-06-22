"""/metrics endpoint + metric recording."""

from __future__ import annotations

from app.metrics import REGISTRY
from fastapi.testclient import TestClient


def test_metrics_endpoint_exposes_core_series(client: TestClient) -> None:
    client.get("/health")  # generate at least one observation
    r = client.get("/metrics")
    assert r.status_code == 200
    body = r.text
    assert "http_requests_total" in body
    assert "http_request_duration_seconds" in body


def test_metrics_endpoint_is_not_self_counted(client: TestClient) -> None:
    """/metrics scrapes must not inflate the request counters (would feed back)."""
    before = REGISTRY.get_sample_value(
        "http_requests_total", {"method": "GET", "path": "/metrics", "status_code": "200"}
    )
    client.get("/metrics")
    after = REGISTRY.get_sample_value(
        "http_requests_total", {"method": "GET", "path": "/metrics", "status_code": "200"}
    )
    assert before is None
    assert after is None


def test_jobs_created_counter_increments(client: TestClient) -> None:
    before = REGISTRY.get_sample_value("jobs_created_total") or 0.0
    client.post("/jobs", json={"payload": "metric-job"})
    after = REGISTRY.get_sample_value("jobs_created_total") or 0.0
    assert after == before + 1.0


def test_error_counter_tracks_4xx(client: TestClient) -> None:
    client.get("/jobs/999")  # 404
    value = REGISTRY.get_sample_value(
        "http_request_errors_total",
        {"method": "GET", "path": "/jobs/{job_id}", "status_code": "404"},
    )
    assert value is not None and value >= 1.0
