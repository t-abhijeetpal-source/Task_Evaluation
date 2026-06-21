"""Application entry point.

Creates the FastAPI app, installs structured logging + a request-id
middleware, registers a consistent error envelope, and mounts the transaction
routes. Run with:
    uvicorn app.main:app --reload
"""

import time
import uuid

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import settings
from app.logging_config import configure_logging, request_id_ctx
from app.routes import router

logger = configure_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    description="A lightweight transaction tracking system (B4 greenfield build).",
    version=settings.app_version,
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    """Assign a request id, time the request, and log it as one JSON line."""
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex
    token = request_id_ctx.set(rid)
    start = time.perf_counter()
    try:
        response = await call_next(request)
    finally:
        request_id_ctx.reset(token)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["x-request-id"] = rid
    logger.info(
        "request",
        extra={
            "extra": {
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "elapsed_ms": elapsed_ms,
            }
        },
    )
    return response


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    """Return a consistent error envelope instead of FastAPI's raw default."""
    # Drop ctx/url/input: ctx/input can hold non-serialisable values (e.g. the
    # raw `inf` that triggered the error); type/loc/msg are what clients need.
    detail = jsonable_encoder(exc.errors(), exclude={"ctx", "url", "input"})
    logger.warning("validation_error", extra={"extra": {"errors": detail}})
    return JSONResponse(
        status_code=422,
        content={"error": "validation_failed", "detail": detail},
    )


app.include_router(router)


@app.get("/health")
def health() -> dict:
    """Liveness probe — reports service identity + version."""
    return {"status": "ok", "service": settings.app_name, "version": settings.app_version}
