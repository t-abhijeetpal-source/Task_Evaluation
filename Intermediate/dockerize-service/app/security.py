"""Security middleware: response hardening headers, body-size cap, rate limiting.

Kept dependency-free (pure Starlette) so the image stays small. The rate limiter
is an in-memory fixed-window counter — correct for a single replica; front it with
a shared store (e.g. Redis) when running more than one instance.
"""

import time
from collections import defaultdict
from typing import Dict, Iterable, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# Static security headers appropriate for a JSON API (no markup, no framing).
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach security headers to every response (including errors)."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject oversized request bodies (by Content-Length) with 413."""

    def __init__(self, app, max_bytes: int):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > self.max_bytes:
                    return JSONResponse(
                        status_code=413, content={"error": "Request body too large"}
                    )
            except ValueError:
                return JSONResponse(
                    status_code=400, content={"error": "Invalid Content-Length"}
                )
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-client fixed-window rate limit. Exempt paths bypass the limit."""

    def __init__(self, app, limit: int, exempt_paths: Iterable[str] = ()):
        super().__init__(app)
        self.limit = limit
        self.exempt_paths = set(exempt_paths)
        # (client_ip, window_start) -> count
        self._hits: Dict[Tuple[str, int], int] = defaultdict(int)

    def _client_ip(self, request: Request) -> str:
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        window = int(time.time() // 60)
        key = (self._client_ip(request), window)
        self._hits[key] += 1
        # Opportunistically drop stale windows to bound memory.
        if len(self._hits) > 10_000:
            self._hits = defaultdict(
                int, {k: v for k, v in self._hits.items() if k[1] >= window}
            )

        if self._hits[key] > self.limit:
            retry_after = 60 - int(time.time() % 60)
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded"},
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)
