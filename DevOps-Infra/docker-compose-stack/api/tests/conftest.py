"""Shared pytest fixtures for the D2 API suite.

The API is unit-tested with NO real PostgreSQL: a small in-memory fake stands
in for psycopg's connection/cursor, interpreting the handful of SQL statements
the handlers issue. The app lifespan (which would open a real pool) is stubbed
out so the suite runs fully offline.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import app.main as main_module
import pytest
from app.main import app
from fastapi.testclient import TestClient


class JobStore:
    """Minimal in-memory stand-in for the `jobs` table."""

    def __init__(self) -> None:
        self._jobs: dict[int, dict[str, Any]] = {}
        self._next = 1

    def insert(self, payload: str) -> dict[str, Any]:
        job = {
            "id": self._next,
            "payload": payload,
            "status": "pending",
            "result": None,
            "processed_by": None,
        }
        self._jobs[self._next] = job
        self._next += 1
        return job

    def add_done(self, payload: str, result: str, processed_by: str = "worker-1") -> dict[str, Any]:
        job = self.insert(payload)
        job.update(status="done", result=result, processed_by=processed_by)
        return job

    def get(self, job_id: int) -> dict[str, Any] | None:
        return self._jobs.get(job_id)

    def all_desc(self) -> list[dict[str, Any]]:
        return sorted(self._jobs.values(), key=lambda j: j["id"], reverse=True)


class FakeCursor:
    def __init__(self, store: JobStore) -> None:
        self._store = store
        self._result: list[tuple[Any, ...]] = []

    def __enter__(self) -> FakeCursor:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        s = " ".join(sql.split())
        if s.startswith("SELECT 1"):
            self._result = [(1,)]
        elif s.startswith("INSERT INTO jobs"):
            job = self._store.insert(params[0])
            self._result = [(job["id"], job["payload"], job["status"])]
        elif "WHERE id = %s" in s:
            job = self._store.get(params[0])
            self._result = (
                []
                if job is None
                else [
                    (job["id"], job["payload"], job["status"], job["result"], job["processed_by"])
                ]
            )
        elif s.startswith("SELECT id, payload, status, result FROM jobs"):
            self._result = [
                (j["id"], j["payload"], j["status"], j["result"]) for j in self._store.all_desc()
            ]
        else:  # pragma: no cover — defensive
            self._result = []

    def fetchone(self) -> tuple[Any, ...] | None:
        return self._result[0] if self._result else None

    def fetchall(self) -> list[tuple[Any, ...]]:
        return list(self._result)


class FakeConnection:
    def __init__(self, store: JobStore) -> None:
        self._store = store
        self.commits = 0

    def cursor(self) -> FakeCursor:
        return FakeCursor(self._store)

    def commit(self) -> None:
        self.commits += 1


@pytest.fixture
def store() -> JobStore:
    return JobStore()


@pytest.fixture
def client(store: JobStore, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """TestClient with the DB layer faked and the real pool lifespan stubbed."""

    @contextmanager
    def fake_db_connection() -> Iterator[FakeConnection]:
        yield FakeConnection(store)

    monkeypatch.setattr(main_module, "db_connection", fake_db_connection)
    monkeypatch.setattr(main_module, "open_pool", lambda: None)
    monkeypatch.setattr(main_module, "close_pool", lambda: None)
    monkeypatch.delenv("API_KEY", raising=False)

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
