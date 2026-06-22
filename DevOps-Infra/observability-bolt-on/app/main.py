"""D6 — the instrumented service (FastAPI core reused from D3/D4).

Bolt-on observability:
  * Phase 2 — structured JSON access logs with request_id / status / duration.
  * Phase 3 — Prometheus counters + latency histogram exposed at GET /metrics.
  * Hardening — security response headers + optional OpenTelemetry tracing
    (feature-flagged via OTEL_ENABLED) with trace/span ids in the JSON logs.

Business endpoints are unchanged (`/health`, `/ready`, `/`, `/add`); `/error`
is added so the load generator can exercise the 5xx error boundary.
"""

import os
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app import tracing
from app.calc import add, is_even
from app.logging_setup import configure_logging
from app.metrics import REGISTRY, observe
from app.middleware.security import SECURITY_HEADERS

APP_ENV = os.getenv("APP_ENV", "local")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

log = configure_logging(LOG_LEVEL)
tracing.init_tracing()
app = FastAPI(title="D6 Observability Service", version=APP_VERSION)


def _route_template(request: Request) -> str:
    """Low-cardinality path label.

    Returns the *matched* route template (e.g. ``/add``) so each endpoint maps
    to one time series regardless of query string. Unmatched URLs (404 scans,
    junk paths, bots) collapse to a single ``/_unmatched`` label so they can
    never explode metric cardinality.
    """
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if path:
        return str(path)
    return "/_unmatched"


def _apply_security_headers(response: Response) -> None:
    for header, value in SECURITY_HEADERS.items():
        response.headers.setdefault(header, value)


@app.middleware("http")
async def observability_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = uuid.uuid4().hex
    request.state.request_id = request_id
    start = time.perf_counter()

    with tracing.span(f"{request.method} {request.url.path}"):
        trace_id, span_id = tracing.current_ids()
        try:
            response = await call_next(request)
        except Exception:
            # Unhandled error → emit 500, record metrics, log the stack trace.
            duration_s = time.perf_counter() - start
            path = _route_template(request)
            if path != "/metrics":
                observe(request.method, path, 500, duration_s)
            log.error(
                "request_failed",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": path,
                    "status_code": 500,
                    "duration_ms": round(duration_s * 1000, 2),
                    "client": request.client.host if request.client else None,
                    "trace_id": trace_id,
                    "span_id": span_id,
                },
            )
            error_response: Response = JSONResponse(
                status_code=500,
                content={"detail": "internal server error", "request_id": request_id},
            )
            _apply_security_headers(error_response)
            error_response.headers["X-Request-ID"] = request_id
            return error_response

        duration_s = time.perf_counter() - start
        path = _route_template(request)
        if path != "/metrics":
            observe(request.method, path, response.status_code, duration_s)

        response.headers["X-Request-ID"] = request_id
        _apply_security_headers(response)
        log.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": path,
                "status_code": response.status_code,
                "duration_ms": round(duration_s * 1000, 2),
                "client": request.client.host if request.client else None,
                "trace_id": trace_id,
                "span_id": span_id,
            },
        )
        return response


@app.get("/metrics")
def metrics() -> Response:
    """Prometheus scrape target."""
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "d6-sample", "env": APP_ENV, "version": APP_VERSION}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready"}


@app.get("/add")
def add_endpoint(a: int, b: int) -> dict[str, object]:
    total = add(a, b)
    return {"a": a, "b": b, "sum": total, "even": is_even(total)}


@app.get("/error")
def error() -> dict[str, str]:
    """Deliberate 5xx to exercise the error-rate metric and stack-trace logging."""
    raise RuntimeError("synthetic failure for observability verification")
