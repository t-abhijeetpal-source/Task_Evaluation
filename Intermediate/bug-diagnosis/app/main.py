"""FastAPI application entry point for the orders service."""

from fastapi import FastAPI

from app.routes import router

app = FastAPI(title="Orders Service", version="1.0.0")
app.include_router(router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
