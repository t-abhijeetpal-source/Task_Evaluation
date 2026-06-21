"""Prometheus metrics for the D5 service.

Three runtime vectors, all labelled by HTTP method + matched route template
(low cardinality — the route, not the raw URL), plus the default process/runtime
collectors. Exposed at ``GET /metrics``. Pattern shared with the sibling
``DevOps-Infra/ci-pipeline`` (D3) service.
"""

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Histogram,
    PlatformCollector,
    ProcessCollector,
)

# Dedicated registry so tests can introspect deterministically.
REGISTRY = CollectorRegistry()
ProcessCollector(registry=REGISTRY)
PlatformCollector(registry=REGISTRY)

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests processed.",
    ["method", "path", "status_code"],
    registry=REGISTRY,
)

REQUEST_ERRORS = Counter(
    "http_request_errors_total",
    "HTTP responses with status code >= 400.",
    ["method", "path", "status_code"],
    registry=REGISTRY,
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=REGISTRY,
)


def observe(method: str, path: str, status_code: int, duration_s: float) -> None:
    """Record one completed request across the three metric vectors."""
    sc = str(status_code)
    REQUEST_COUNT.labels(method, path, sc).inc()
    REQUEST_LATENCY.labels(method, path).observe(duration_s)
    if status_code >= 400:
        REQUEST_ERRORS.labels(method, path, sc).inc()
