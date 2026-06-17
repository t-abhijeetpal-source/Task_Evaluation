import json
import logging
import uuid

from fastapi import FastAPI, Request

from .database import Base, engine
from .routes import router

# Configure structured JSON logging.
logger = logging.getLogger("fastapi-service")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

app = FastAPI(title="Transaction Ingestion Service")


@app.on_event("startup")
def on_startup():
    # Import models so tables are registered on Base.metadata before create_all.
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    logger.info(
        json.dumps(
            {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
            }
        )
    )
    return response


app.include_router(router)
