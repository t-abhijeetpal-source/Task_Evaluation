"""D3 sample FastAPI service (the unit-under-CI)."""

from fastapi import FastAPI

from app.calc import add, is_even

app = FastAPI(title="D3 Sample Service", version="1.0.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/add")
def add_endpoint(a: int, b: int) -> dict:
    total = add(a, b)
    return {"a": a, "b": b, "sum": total, "even": is_even(total)}
