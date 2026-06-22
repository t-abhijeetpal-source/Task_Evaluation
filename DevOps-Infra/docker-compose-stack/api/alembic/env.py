"""Alembic migration environment for the D2 Jobs API.

Reads the connection string from the ``DATABASE_URL`` environment variable so
no credentials are committed. Supports both online (live DB) and offline
(``--sql``) runs — the latter needs no database and is used to verify the
migration in CI.
"""

from __future__ import annotations

import os

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config

# psycopg 3 uses the ``postgresql+psycopg`` SQLAlchemy dialect.
_url = os.environ.get("DATABASE_URL", "postgresql+psycopg://appuser:apppass@localhost:5432/appdb")
if _url.startswith("postgresql://"):
    _url = _url.replace("postgresql://", "postgresql+psycopg://", 1)
config.set_main_option("sqlalchemy.url", _url)


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
