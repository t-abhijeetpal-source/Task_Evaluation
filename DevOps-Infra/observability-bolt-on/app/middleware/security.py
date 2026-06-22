"""Security response headers (defensive hardening).

A small, dependency-free set of headers applied to every response by the
observability middleware. Values are conservative defaults for a JSON API.

A restrictive ``Content-Security-Policy`` (e.g. ``default-src 'none'``) is
deliberately *omitted*: FastAPI's bundled Swagger UI at ``/docs`` loads its
JS/CSS from a CDN, and a strict CSP would break the documented `app-docs`
reproduction. The headers below harden the API surface without that side
effect; a fronting reverse proxy/CDN is the right place to add CSP/HSTS in a
real deployment.
"""

from __future__ import annotations

# Applied via ``response.headers.setdefault(...)`` so a route may override any
# individual header when it has a good reason to.
SECURITY_HEADERS: dict[str, str] = {
    # Stop browsers MIME-sniffing a response away from its declared type.
    "X-Content-Type-Options": "nosniff",
    # This JSON API is never meant to be framed.
    "X-Frame-Options": "DENY",
    # Don't leak full URLs (which may carry ids) in the Referer header.
    "Referrer-Policy": "no-referrer",
    # Isolate the browsing context group (defence-in-depth against XS-Leaks).
    "Cross-Origin-Opener-Policy": "same-origin",
    # Drop powerful browser features the API has no use for.
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}
