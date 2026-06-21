"""Prometheus metrics.

Follows the repo's observability pattern (DevOps-Infra/observability-bolt-on):
low-cardinality labels (method + matched route template, never the raw URL), a
dedicated registry, and the three core runtime vectors:
  * http_requests_total            — Counter, by method/path/status_code
  * http_request_errors_total      — Counter, responses with status >= 400
  * http_request_duration_seconds  — Histogram, latency distribution
"""

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    PlatformCollector,
    ProcessCollector,
    generate_latest,
)

# Dedicated registry (defined once at import) so repeated create_app() calls in
# tests do not re-register collectors on the global default registry.
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
    """Record one request's count, latency, and (if applicable) error."""
    sc = str(status_code)
    REQUEST_COUNT.labels(method, path, sc).inc()
    REQUEST_LATENCY.labels(method, path).observe(duration_s)
    if status_code >= 400:
        REQUEST_ERRORS.labels(method, path, sc).inc()


def render_latest() -> bytes:
    """Serialize the registry in Prometheus text exposition format."""
    return generate_latest(REGISTRY)


__all__ = ["REGISTRY", "observe", "render_latest", "CONTENT_TYPE_LATEST"]
