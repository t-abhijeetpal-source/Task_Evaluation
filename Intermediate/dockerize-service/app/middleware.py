"""Request-context middleware: correlation ID, access logging, metrics.

Assigns/propagates an ``X-Request-ID`` (generated when the client omits it),
times the request, records Prometheus metrics, and emits one structured JSON
access log line. Logs metadata only — never the request body.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.metrics import observe

log = logging.getLogger("currency-service")


def _route_template(request: Request) -> str:
    """Low-cardinality path label: the matched route, else the raw path."""
    route = request.scope.get("route")
    return getattr(route, "path", request.url.path)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Correlation ID + access log + metrics around each request."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id
        start = time.perf_counter()
        client = request.client.host if request.client else None

        try:
            response: Response = await call_next(request)
        except Exception:
            duration_s = time.perf_counter() - start
            path = _route_template(request)
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
                    "client": client,
                },
            )
            resp = JSONResponse(
                status_code=500,
                content={"error": "internal server error", "request_id": request_id},
            )
            resp.headers["X-Request-ID"] = request_id
            return resp

        duration_s = time.perf_counter() - start
        path = _route_template(request)
        # Don't let the scrape pollute its own metrics.
        if path != "/metrics":
            observe(request.method, path, response.status_code, duration_s)
            log.info(
                "request_completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_s * 1000, 2),
                    "client": client,
                },
            )
        response.headers["X-Request-ID"] = request_id
        return response
