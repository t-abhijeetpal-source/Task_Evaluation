"""FastAPI application entry point (dockerized in I5)."""

from fastapi import FastAPI

from app.routes import router

app = FastAPI(
    title="Currency Conversion Service (Dockerized)",
    description="FastAPI service containerized for I5. Exposes /convert and /health.",
    version="1.0.0",
)

app.include_router(router)


@app.get("/health")
def health() -> dict:
    """Liveness/readiness probe used by the Docker HEALTHCHECK."""
    return {"status": "ok"}
