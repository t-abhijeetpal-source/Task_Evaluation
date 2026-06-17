"""D6 — the instrumented service (FastAPI core reused from D3/D4).

Bolt-on observability:
  * Phase 2 — structured JSON access logs with request_id / status / duration.
  * Phase 3 — Prometheus counters + latency histogram exposed at GET /metrics.

Business endpoints are unchanged (`/health`, `/ready`, `/`, `/add`); `/error`
is added so the load generator can exercise the 5xx error boundary.
"""

import os
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.calc import add, is_even
from app.logging_setup import configure_logging
from app.metrics import REGISTRY, observe

APP_ENV = os.getenv("APP_ENV", "local")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

log = configure_logging(LOG_LEVEL)
app = FastAPI(title="D6 Observability Service", version=APP_VERSION)


def _route_template(request: Request) -> str:
    """Low-cardinality path label: the matched route, else the raw path."""
    route = request.scope.get("route")
    return getattr(route, "path", request.url.path)


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    request_id = uuid.uuid4().hex
    request.state.request_id = request_id
    start = time.perf_counter()

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
            },
        )
        return JSONResponse(status_code=500, content={"detail": "internal server error", "request_id": request_id})

    duration_s = time.perf_counter() - start
    path = _route_template(request)
    if path != "/metrics":
        observe(request.method, path, response.status_code, duration_s)

    response.headers["X-Request-ID"] = request_id
    log.info(
        "request_completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": path,
            "status_code": response.status_code,
            "duration_ms": round(duration_s * 1000, 2),
            "client": request.client.host if request.client else None,
        },
    )
    return response


@app.get("/metrics")
def metrics() -> Response:
    """Prometheus scrape target."""
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
def root() -> dict:
    return {"service": "d6-sample", "env": APP_ENV, "version": APP_VERSION}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict:
    return {"status": "ready"}


@app.get("/add")
def add_endpoint(a: int, b: int) -> dict:
    total = add(a, b)
    return {"a": a, "b": b, "sum": total, "even": is_even(total)}


@app.get("/error")
def error() -> dict:
    """Deliberate 5xx to exercise the error-rate metric and stack-trace logging."""
    raise RuntimeError("synthetic failure for observability verification")
