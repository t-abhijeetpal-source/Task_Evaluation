"""Tests for the Prometheus metrics layer."""

from fastapi.testclient import TestClient

from app.metrics import REGISTRY, observe


def _count(name: str, **labels: str) -> float:
    value = REGISTRY.get_sample_value(name, labels)
    return value or 0.0


def test_observe_increments_request_and_latency() -> None:
    before = _count("http_requests_total", method="GET", path="/probe", status_code="200")
    observe("GET", "/probe", 200, 0.01)
    after = _count("http_requests_total", method="GET", path="/probe", status_code="200")
    assert after == before + 1
    # Histogram count moved too.
    assert _count("http_request_duration_seconds_count", method="GET", path="/probe") >= 1


def test_observe_4xx_increments_error_counter() -> None:
    before = _count("http_request_errors_total", method="GET", path="/probe", status_code="404")
    observe("GET", "/probe", 404, 0.01)
    after = _count("http_request_errors_total", method="GET", path="/probe", status_code="404")
    assert after == before + 1


def test_observe_5xx_increments_error_counter() -> None:
    before = _count("http_request_errors_total", method="GET", path="/probe", status_code="500")
    observe("GET", "/probe", 500, 0.01)
    after = _count("http_request_errors_total", method="GET", path="/probe", status_code="500")
    assert after == before + 1


def test_observe_2xx_does_not_increment_error_counter() -> None:
    before = _count("http_request_errors_total", method="GET", path="/probe", status_code="200")
    observe("GET", "/probe", 200, 0.01)
    after = _count("http_request_errors_total", method="GET", path="/probe", status_code="200")
    assert after == before


def test_metrics_endpoint_is_excluded_from_counters(client: TestClient) -> None:
    """Scraping /metrics must not record itself (would be self-referential noise)."""
    client.get("/metrics")
    client.get("/metrics")
    assert _count("http_requests_total", method="GET", path="/metrics", status_code="200") == 0.0


def test_request_increments_through_middleware(client: TestClient) -> None:
    before = _count("http_requests_total", method="GET", path="/health", status_code="200")
    client.get("/health")
    after = _count("http_requests_total", method="GET", path="/health", status_code="200")
    assert after == before + 1
