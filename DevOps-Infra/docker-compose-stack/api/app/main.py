"""D2 Jobs API — FastAPI + PostgreSQL. Writes jobs the worker later processes."""
import os

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

DATABASE_URL = os.environ["DATABASE_URL"]

app = FastAPI(title="D2 Jobs API", version="1.0.0")


class JobIn(BaseModel):
    payload: str


def _connect():
    return psycopg.connect(DATABASE_URL, connect_timeout=5)


@app.get("/health")
def health():
    try:
        with _connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return {"status": "ok", "db": "up"}
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(status_code=503, content={"status": "degraded", "db": "down", "error": str(exc)})


@app.post("/jobs", status_code=201)
def create_job(job: JobIn):
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO jobs (payload) VALUES (%s) RETURNING id, payload, status",
            (job.payload,),
        )
        row = cur.fetchone()
    return {"id": row[0], "payload": row[1], "status": row[2]}


@app.get("/jobs/{job_id}")
def get_job(job_id: int):
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, payload, status, result, processed_by FROM jobs WHERE id = %s",
            (job_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="job not found")
    return {"id": row[0], "payload": row[1], "status": row[2], "result": row[3], "processed_by": row[4]}


@app.get("/jobs")
def list_jobs():
    with _connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, payload, status, result FROM jobs ORDER BY id DESC LIMIT 100")
        rows = cur.fetchall()
    return [{"id": r[0], "payload": r[1], "status": r[2], "result": r[3]} for r in rows]
