"""D5 sample service — the unit under reproducible bootstrap.

Deliberately small, but production-shaped in posture:
  * structured JSON access logs with a per-request ``request_id``,
  * Prometheus metrics at ``GET /metrics``,
  * security response headers on every reply,
  * a liveness probe (``/health``) that echoes the live pinned runtime,
  * validated, bounded inputs (out-of-range / unknown keys -> 422).

The point of D5 is that a *fresh clone* builds and passes its tests with one
command, on a clean machine, with pinned runtime versions.
"""

import os
import sys

from fastapi import FastAPI, Query
from fastapi.responses import Response

from app.calc import add, is_even
from app.logging_setup import configure_logging
from app.middleware.security import install_middleware
from app.schemas import OPERAND_LIMIT, AddRequest, AddResponse, HealthResponse

try:  # prometheus_client is a runtime dep; degrade gracefully if absent.
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    from app.metrics import REGISTRY

    _METRICS_ENABLED = True
except ImportError:  # pragma: no cover - exercised only without the optional dep
    _METRICS_ENABLED = False

APP_ENV = os.getenv("APP_ENV", "dev")
APP_VERSION = os.getenv("APP_VERSION", "1.1.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

configure_logging(LOG_LEVEL)
app = FastAPI(title="D5 Reproducible Service", version=APP_VERSION)
install_middleware(app)


if _METRICS_ENABLED:

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        """Prometheus scrape target."""
        return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness probe — echoes the interpreter + env so the pinned runtime is visible."""
    return HealthResponse(
        status="ok",
        python=sys.version.split()[0],
        app_env=APP_ENV,
        version=APP_VERSION,
    )


@app.post("/v1/add", response_model=AddResponse)
def add_v1(req: AddRequest) -> AddResponse:
    """Canonical addition endpoint — bounded, validated JSON body."""
    total = add(req.a, req.b)
    return AddResponse(a=req.a, b=req.b, sum=total, even=is_even(total))


@app.get("/add", response_model=AddResponse, deprecated=True)
def add_legacy(
    a: int = Query(..., ge=-OPERAND_LIMIT, le=OPERAND_LIMIT),
    b: int = Query(..., ge=-OPERAND_LIMIT, le=OPERAND_LIMIT),
) -> AddResponse:
    """Deprecated query-param form, kept for backwards compatibility.

    Prefer ``POST /v1/add``. Bounds match the canonical endpoint so behaviour
    (including 422 on out-of-range input) is identical.
    """
    total = add(a, b)
    return AddResponse(a=a, b=b, sum=total, even=is_even(total))
