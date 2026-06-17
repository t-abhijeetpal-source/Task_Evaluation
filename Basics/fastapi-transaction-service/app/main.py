"""Application entry point.

Creates the FastAPI app and mounts the transaction routes. Run with:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI

from app.routes import router

app = FastAPI(
    title="Transaction Tracking Service",
    description="A lightweight transaction tracking system (B4 greenfield build).",
    version="1.0.0",
)

app.include_router(router)


@app.get("/health")
def health() -> dict:
    """Simple liveness probe."""
    return {"status": "ok"}
