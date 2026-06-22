"""Fakes for the worker unit tests — no real PostgreSQL.

A ``FakeConnection`` records the SQL the worker runs and serves pending rows
from a list, so ``process_once`` can be exercised deterministically offline.
"""

from __future__ import annotations

import os
from typing import Any

import pytest

# worker.py reads DATABASE_URL at import time; provide a dummy so the module
# imports cleanly under test (no real connection is ever opened).
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")


class FakeCursor:
    def __init__(self, pending: list[tuple[int, str]]) -> None:
        self._pending = pending
        self.updates: list[tuple[str, str, int]] = []
        self._fetch: list[tuple[int, str]] = []

    def __enter__(self) -> FakeCursor:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        s = " ".join(sql.split())
        if s.startswith("SELECT id, payload FROM jobs"):
            # Claimed jobs are removed from the pending set (SKIP LOCKED semantics).
            self._fetch = list(self._pending)
            self._pending.clear()
        elif s.startswith("UPDATE jobs"):
            result, worker_id, job_id = params
            self.updates.append((result, worker_id, job_id))

    def fetchall(self) -> list[tuple[int, str]]:
        return list(self._fetch)


class FakeConnection:
    def __init__(self, pending: list[tuple[int, str]] | None = None) -> None:
        self.cur = FakeCursor(pending or [])
        self.commits = 0

    def cursor(self) -> FakeCursor:
        return self.cur

    def commit(self) -> None:
        self.commits += 1


@pytest.fixture
def make_conn() -> Any:
    def _factory(pending: list[tuple[int, str]] | None = None) -> FakeConnection:
        return FakeConnection(pending)

    return _factory
