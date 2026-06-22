"""Database access for the D2 Jobs API.

A psycopg connection pool is opened once at application startup (FastAPI
lifespan) and closed at shutdown, so request handlers borrow a warm pooled
connection instead of paying TCP + auth on every call.

When the pool has not been opened — unit tests (which patch
:func:`db_connection`), or a handler somehow invoked before startup — the code
falls back to a short-lived direct connection so the path is always usable.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg_pool import ConnectionPool

DATABASE_URL = os.environ.get("DATABASE_URL", "")
POOL_MIN_SIZE = int(os.environ.get("DB_POOL_MIN_SIZE", "1"))
POOL_MAX_SIZE = int(os.environ.get("DB_POOL_MAX_SIZE", "10"))
CONNECT_TIMEOUT = float(os.environ.get("DB_CONNECT_TIMEOUT", "5"))

_pool: ConnectionPool[psycopg.Connection[Any]] | None = None


def open_pool() -> None:
    """Open the connection pool (idempotent). Called from the app lifespan."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=DATABASE_URL,
            min_size=POOL_MIN_SIZE,
            max_size=POOL_MAX_SIZE,
            kwargs={"connect_timeout": CONNECT_TIMEOUT},
            open=True,
        )


def close_pool() -> None:
    """Close the connection pool (idempotent). Called from the app lifespan."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


@contextmanager
def db_connection() -> Iterator[psycopg.Connection[Any]]:
    """Yield a database connection — pooled when the pool is open, else direct."""
    if _pool is None:
        with psycopg.connect(DATABASE_URL, connect_timeout=int(CONNECT_TIMEOUT)) as conn:
            yield conn
    else:
        with _pool.connection() as conn:
            yield conn
