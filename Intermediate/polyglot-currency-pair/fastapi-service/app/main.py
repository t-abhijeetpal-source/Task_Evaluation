"""FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI

from app.routes import router

app = FastAPI(
    title="Currency Conversion Service",
    description="FastAPI service exposing POST /convert with hardcoded rates (I4).",
    version="1.0.0",
)

app.include_router(router)


@app.get("/health")
def health() -> dict:
    """Liveness probe."""
    return {"status": "ok"}
