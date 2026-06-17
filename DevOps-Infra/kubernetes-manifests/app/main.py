"""D4 sample FastAPI service — the workload deployed to Kubernetes.

Reuses the D3 service core (`/health`, `/add`) and adds:
  * `/ready`  — readiness probe target, separate from liveness.
  * `/`       — surfaces runtime config injected via the ConfigMap, so the
                ConfigMap manifest is functionally exercised (not decorative).

All configuration is read from the environment at startup so the same image
runs unchanged across environments — values come from `k8s/configmap.yaml`.
"""

import os

from fastapi import FastAPI

from app.calc import add, is_even

# Runtime config — injected by the Kubernetes ConfigMap (envFrom) in-cluster,
# falls back to sane defaults for local `uvicorn` runs.
APP_ENV = os.getenv("APP_ENV", "local")
APP_GREETING = os.getenv("APP_GREETING", "hello from D4")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

app = FastAPI(title="D4 Sample Service", version=APP_VERSION)


@app.get("/")
def root() -> dict:
    """Echo the runtime config so ConfigMap injection is observable over HTTP."""
    return {"service": "d4-sample", "env": APP_ENV, "greeting": APP_GREETING, "version": APP_VERSION}


@app.get("/health")
def health() -> dict:
    """Liveness probe target — process is up and serving."""
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict:
    """Readiness probe target — app is ready to receive traffic."""
    return {"status": "ready"}


@app.get("/add")
def add_endpoint(a: int, b: int) -> dict:
    total = add(a, b)
    return {"a": a, "b": b, "sum": total, "even": is_even(total)}
