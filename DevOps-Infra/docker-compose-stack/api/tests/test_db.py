"""Connection-pool lifecycle + the connection-acquisition fallback.

No real PostgreSQL: ``ConnectionPool`` and ``psycopg.connect`` are replaced with
fakes so both the pooled path and the direct-connect fallback are exercised.
"""

from __future__ import annotations

from typing import Any, ClassVar

import app.db as db
import pytest


class FakePool:
    instances: ClassVar[list[FakePool]] = []

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.closed = False
        self._conn = object()
        FakePool.instances.append(self)

    def close(self) -> None:
        self.closed = True

    def connection(self) -> Any:
        pool = self

        class _Ctx:
            def __enter__(self_inner) -> object:
                return pool._conn

            def __exit__(self_inner, *exc: object) -> bool:
                return False

        return _Ctx()


@pytest.fixture(autouse=True)
def _reset_pool() -> Any:
    db._pool = None
    FakePool.instances = []
    yield
    db._pool = None


def test_open_pool_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db, "ConnectionPool", FakePool)
    db.open_pool()
    db.open_pool()  # second call must not create a second pool
    assert len(FakePool.instances) == 1


def test_close_pool_closes_and_clears(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db, "ConnectionPool", FakePool)
    db.open_pool()
    pool = FakePool.instances[0]
    db.close_pool()
    assert pool.closed is True
    assert db._pool is None
    db.close_pool()  # idempotent — no error when already closed


def test_db_connection_uses_pool_when_open(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db, "ConnectionPool", FakePool)
    db.open_pool()
    with db.db_connection() as conn:
        assert conn is FakePool.instances[0]._conn


def test_db_connection_falls_back_to_direct_connect(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel = object()

    class _DirectCtx:
        def __enter__(self) -> object:
            return sentinel

        def __exit__(self, *exc: object) -> bool:
            return False

    captured: dict[str, Any] = {}

    def fake_connect(dsn: str, **kwargs: Any) -> _DirectCtx:
        captured["dsn"] = dsn
        captured["kwargs"] = kwargs
        return _DirectCtx()

    monkeypatch.setattr(db.psycopg, "connect", fake_connect)
    assert db._pool is None
    with db.db_connection() as conn:
        assert conn is sentinel
    assert "connect_timeout" in captured["kwargs"]
