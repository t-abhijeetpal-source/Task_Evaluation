"""D2 Jobs API — FastAPI + PostgreSQL.

Writes jobs that the background worker later claims and processes. Hardened
with the same cross-cutting observability the rest of the platform uses:
  * structured JSON access logs (request_id / status / duration) on stdout,
  * per-route Prometheus metrics exposed at ``/metrics``,
  * security response headers + a stable ``X-Request-ID`` on every response,
  * an optional ``X-API-Key`` gate (enabled only when ``API_KEY`` is set).

Database access goes through a lifespan-managed psycopg connection pool
(:mod:`app.db`); ``/health`` runs a real ``SELECT 1`` against it.
"""

from __future__ import annotations

import os
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

from app.db import close_pool, db_connection, open_pool
from app.logging_setup import configure_logging
from app.metrics import JOBS_CREATED, REGISTRY, observe
from app.middleware.security import SECURITY_HEADERS

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
APP_VERSION = os.getenv("APP_VERSION", "2.0.0")

# Paths that never require an API key (probes, scrape target, API docs) so
# healthchecks and Prometheus keep working regardless of auth configuration.
_AUTH_EXEMPT = frozenset({"/health", "/metrics", "/docs", "/redoc", "/openapi.json"})

log = configure_logging(LOG_LEVEL)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Open the DB connection pool on startup, close it on shutdown."""
    open_pool()
    try:
        yield
    finally:
        close_pool()


app = FastAPI(title="D2 Jobs API", version=APP_VERSION, lifespan=lifespan)


class JobIn(BaseModel):
    payload: str


def _required_api_key() -> str:
    """Read at request time so deployments (and tests) can toggle auth via env."""
    return os.getenv("API_KEY", "")


def _route_template(request: Request) -> str:
    """Low-cardinality path label: the matched route template, or /_unmatched.

    Junk/404 URLs collapse to one ``/_unmatched`` series so they can never
    explode metric cardinality.
    """
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if path:
        return str(path)
    return "/_unmatched"


def _apply_security_headers(response: Response) -> None:
    for header, value in SECURITY_HEADERS.items():
        response.headers.setdefault(header, value)


def _finalize(response: Response, request_id: str) -> Response:
    response.headers["X-Request-ID"] = request_id
    _apply_security_headers(response)
    return response


@app.middleware("http")
async def observability_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = uuid.uuid4().hex
    request.state.request_id = request_id
    start = time.perf_counter()
    client = request.client.host if request.client else None

    # ---- Optional API-key gate -------------------------------------------------
    api_key = _required_api_key()
    auth_required = bool(api_key) and request.url.path not in _AUTH_EXEMPT
    if auth_required and request.headers.get("X-API-Key") != api_key:
        duration_s = time.perf_counter() - start
        path = _route_template(request)
        observe(request.method, path, 401, duration_s)
        log.info(
            "request_rejected",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": path,
                "status_code": 401,
                "duration_ms": round(duration_s * 1000, 2),
                "client": client,
            },
        )
        return _finalize(
            JSONResponse(
                status_code=401,
                content={"detail": "invalid or missing API key", "request_id": request_id},
            ),
            request_id,
        )

    # ---- Handle the request ----------------------------------------------------
    try:
        response = await call_next(request)
    except Exception:
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
                "client": client,
            },
        )
        return _finalize(
            JSONResponse(
                status_code=500,
                content={"detail": "internal server error", "request_id": request_id},
            ),
            request_id,
        )

    duration_s = time.perf_counter() - start
    path = _route_template(request)
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
    return _finalize(response, request_id)


@app.get("/metrics")
def metrics() -> Response:
    """Prometheus scrape target."""
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
def health() -> Response:
    """Liveness + DB connectivity probe — runs a real ``SELECT 1``."""
    try:
        with db_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
    except psycopg.Error as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "db": "down", "error": str(exc)},
        )
    return JSONResponse(content={"status": "ok", "db": "up"})


@app.post("/jobs", status_code=201)
def create_job(job: JobIn) -> dict[str, object]:
    with db_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO jobs (payload) VALUES (%s) RETURNING id, payload, status",
            (job.payload,),
        )
        row = cur.fetchone()
        conn.commit()
    if row is None:  # pragma: no cover — RETURNING always yields a row on success
        raise HTTPException(status_code=500, detail="insert returned no row")
    JOBS_CREATED.inc()
    return {"id": row[0], "payload": row[1], "status": row[2]}


@app.get("/jobs/{job_id}")
def get_job(job_id: int) -> dict[str, object]:
    with db_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, payload, status, result, processed_by FROM jobs WHERE id = %s",
            (job_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="job not found")
    return {
        "id": row[0],
        "payload": row[1],
        "status": row[2],
        "result": row[3],
        "processed_by": row[4],
    }


@app.get("/jobs")
def list_jobs() -> list[dict[str, object]]:
    with db_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, payload, status, result FROM jobs ORDER BY id DESC LIMIT 100")
        rows = cur.fetchall()
    return [{"id": r[0], "payload": r[1], "status": r[2], "result": r[3]} for r in rows]
