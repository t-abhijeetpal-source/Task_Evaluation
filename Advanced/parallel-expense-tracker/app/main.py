from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.database import engine, run_migrations
from app.routes import router

# Import models so the ORM mapping is registered before any query runs.
from app import models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Apply db/migrations/*.sql at startup. This is the single source of truth
    # for the runtime schema and brings the CHECK constraints + indexes that
    # ORM create_all would not emit. Idempotent (CREATE ... IF NOT EXISTS).
    run_migrations(engine)
    yield


app = FastAPI(title="Expense Tracker", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return a JSON-safe 422 for invalid input.

    FastAPI's default handler echoes the raw offending value back in the error
    body. When that value is a non-finite float (NaN / Infinity sent as a JSON
    literal), the JSON encoder raises and the client gets a 500 instead of a
    422. We emit only loc/msg/type — never the raw input — so non-finite money
    is rejected cleanly with a 422.
    """
    errors = [
        {
            "loc": list(err.get("loc", [])),
            "msg": err.get("msg", ""),
            "type": err.get("type", ""),
        }
        for err in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})

# Register the API router BEFORE mounting static files so that /api/* is
# handled by the router and not swallowed by the static mount at "/".
app.include_router(router)

app.mount("/", StaticFiles(directory="static", html=True), name="static")
