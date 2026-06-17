"""D5 sample service — the unit under reproducible bootstrap.

Intentionally small; the point of D5 is that a *fresh clone* builds and passes
its tests with one command, on a clean machine, with pinned runtime versions.
"""

import os
import sys

from fastapi import FastAPI

from app.calc import add, is_even

app = FastAPI(title="D5 Reproducible Service", version="1.0.0")


@app.get("/health")
def health() -> dict:
    # Echo the interpreter + env so it is obvious which pinned runtime is live.
    return {
        "status": "ok",
        "python": sys.version.split()[0],
        "app_env": os.getenv("APP_ENV", "unset"),
    }


@app.get("/add")
def add_endpoint(a: int, b: int) -> dict:
    total = add(a, b)
    return {"a": a, "b": b, "sum": total, "even": is_even(total)}
