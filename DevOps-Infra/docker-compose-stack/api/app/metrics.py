"""Prometheus metrics for the D2 Jobs API.

Three core runtime vectors, all labelled by method + route template (low
cardinality — the matched route, not the raw URL):
  * http_requests_total              — Counter (total requests, by status_code)
  * http_request_errors_total        — Counter (responses with status >= 400)
  * http_request_duration_seconds    — Histogram (latency distribution)
Plus the default process/runtime collectors shipped by prometheus_client.

A small set of domain counters track the job lifecycle the worker drives, so
the API surface and the queue it feeds are observable from one /metrics scrape.
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

# Domain counter: jobs accepted via POST /jobs (the work the worker consumes).
JOBS_CREATED = Counter(
    "jobs_created_total",
    "Jobs accepted by the API and enqueued for the worker.",
    registry=REGISTRY,
)


def observe(method: str, path: str, status_code: int, duration_s: float) -> None:
    sc = str(status_code)
    REQUEST_COUNT.labels(method, path, sc).inc()
    REQUEST_LATENCY.labels(method, path).observe(duration_s)
    if status_code >= 400:
        REQUEST_ERRORS.labels(method, path, sc).inc()
