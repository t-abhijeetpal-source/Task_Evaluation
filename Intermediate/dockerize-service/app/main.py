"""FastAPI application entry point (dockerized in I5).

Thin entry: conversion logic/schemas/routes live in the shared ``currency_core``
package. This module assembles the production app via ``create_app`` — wiring the
security baseline (CORS, security headers, body-size cap, rate limiting) and a
JSON-safe validation error handler.

Middleware order (outermost -> innermost): security headers -> CORS -> rate limit
-> body-size cap -> routes. (Starlette runs the last-added middleware first.)
"""

import os
from typing import Optional

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app import health
from app.config import Settings
from app.errors import validation_exception_handler
from app.logging_config import configure_logging
from app.metrics import CONTENT_TYPE_LATEST, render_latest
from app.middleware import RequestContextMiddleware
from app.security import (
    BodySizeLimitMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
from currency_core.routes import router

# Paths exempt from the strict /convert rate limit (probes + metrics scrape).
RATE_LIMIT_EXEMPT = {"/health", "/ready", "/metrics"}


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = settings or Settings()
    configure_logging(os.getenv("LOG_LEVEL", "INFO"))

    app = FastAPI(
        title="Currency Conversion Service (Dockerized)",
        description="FastAPI service containerized for I5. Exposes /convert and /health.",
        version=settings.service_version,
    )
    app.state.settings = settings

    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # Added inner -> outer; Starlette executes the last-added (outermost) first.
    # Effective order: security headers -> CORS -> request-context -> rate limit
    # -> body-size cap -> routes.
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_body_bytes)
    app.add_middleware(
        RateLimitMiddleware,
        limit=settings.rate_limit_per_minute,
        exempt_paths=RATE_LIMIT_EXEMPT,
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.resolved_cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)

    app.include_router(router)

    @app.get("/metrics")
    def metrics() -> Response:
        """Prometheus scrape target (text exposition format)."""
        return Response(render_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/health")
    def health_probe() -> dict:
        """Liveness probe — backs the Docker HEALTHCHECK. Always ok if running."""
        return health.liveness(settings)

    @app.get("/ready")
    def readiness_probe() -> Response:
        """Readiness probe — 503 when config/rates are not loaded."""
        body, status_code = health.readiness(settings)
        return JSONResponse(status_code=status_code, content=body)

    return app


app = create_app()
