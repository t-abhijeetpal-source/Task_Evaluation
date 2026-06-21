"""Security + observability middleware for the D5 service.

Packaged as installable middleware so ``app.main`` stays declarative. Each
request is tagged with a ``request_id``, timed, recorded into Prometheus, and
written to the structured access log; each response is hardened with a fixed
set of security headers. CORS is *off by default* and opt-in via the
``CORS_ALLOW_ORIGINS`` env var (comma-separated allow-list) — a JSON API has no
business being reachable cross-origin unless explicitly configured.

Mirrors the posture of the sibling ``DevOps-Infra/ci-pipeline`` (D3) service.
"""

import logging
import os
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.logging_setup import LOGGER_NAME

try:  # prometheus_client is a runtime dep; degrade gracefully if absent.
    from app.metrics import observe

    _METRICS_ENABLED = True
except ImportError:  # pragma: no cover - exercised only without the optional dep
    _METRICS_ENABLED = False

log = logging.getLogger(LOGGER_NAME)

# Hardening headers applied to every response (sensible defaults for a JSON API).
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Cache-Control": "no-store",
}

# Endpoints excluded from request metrics (scraping its own metrics is noise).
_METRICS_PATH = "/metrics"


def _route_template(request: Request) -> str:
    """Low-cardinality path label: the matched route template, else the raw path."""
    route = request.scope.get("route")
    return getattr(route, "path", request.url.path)


class SecurityObservabilityMiddleware(BaseHTTPMiddleware):
    """Tag, time, observe, log, and harden every request/response."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = getattr(request.state, "request_id", None) or uuid.uuid4().hex
        request.state.request_id = request_id
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_s = time.perf_counter() - start
            path = _route_template(request)
            if _METRICS_ENABLED and path != _METRICS_PATH:
                observe(request.method, path, 500, duration_s)
            log.error(
                "request_failed",
                exc_info=True,
                extra=_log_fields(request, request_id, path, 500, duration_s),
            )
            raise

        duration_s = time.perf_counter() - start
        path = _route_template(request)
        if _METRICS_ENABLED and path != _METRICS_PATH:
            observe(request.method, path, response.status_code, duration_s)

        response.headers["X-Request-ID"] = request_id
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)

        log.info(
            "request_completed",
            extra=_log_fields(request, request_id, path, response.status_code, duration_s),
        )
        return response


def _log_fields(
    request: Request, request_id: str, path: str, status_code: int, duration_s: float
) -> dict[str, object]:
    return {
        "request_id": request_id,
        "method": request.method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration_s * 1000, 2),
        "client": request.client.host if request.client else None,
    }


def cors_origins() -> list[str]:
    """Parse the ``CORS_ALLOW_ORIGINS`` allow-list (comma-separated); empty = disabled."""
    raw = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
    if not raw:
        return []
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def install_middleware(app: FastAPI) -> None:
    """Attach CORS (if configured) and the security/observability middleware."""
    origins = cors_origins()
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        )
    app.add_middleware(SecurityObservabilityMiddleware)
