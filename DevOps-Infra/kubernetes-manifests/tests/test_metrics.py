"""Tests for the Prometheus metrics endpoint and instrumentation."""

from fastapi.testclient import TestClient
from prometheus_client import CONTENT_TYPE_LATEST


def test_metrics_endpoint_exposition_format(client: TestClient) -> None:
    r = client.get("/metrics")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith(CONTENT_TYPE_LATEST.split(";")[0])
    body = r.text
    # Core vectors and default collectors are present in the exposition.
    assert "http_requests_total" in body
    assert "http_request_duration_seconds" in body
    assert "process_" in body or "python_info" in body


def test_request_counter_increments(client: TestClient) -> None:
    # Drive a known route, then assert its time series advanced.
    client.get("/health")
    client.get("/health")
    body = client.get("/metrics").text
    # The matched route template is the label value (low cardinality).
    assert 'http_requests_total{method="GET",path="/health",status_code="200"}' in body


def test_error_responses_counted(client: TestClient) -> None:
    client.get("/add", params={"a": "x", "b": 3})  # 422
    body = client.get("/metrics").text
    assert "http_request_errors_total" in body
    assert 'status_code="422"' in body


def test_metrics_path_not_self_counted(client: TestClient) -> None:
    """/metrics must not instrument itself (avoids a self-referential series)."""
    client.get("/metrics")
    body = client.get("/metrics").text
    assert 'path="/metrics"' not in body
