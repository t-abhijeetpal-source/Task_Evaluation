import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/expenses.db")

# When using the default SQLite file, make sure the data/ directory exists.
if DATABASE_URL == "sqlite:///./data/expenses.db":
    os.makedirs("./data", exist_ok=True)

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)


# --- SQLite concurrency hardening -------------------------------------------
# Default SQLite uses rollback-journal + a 0ms busy timeout, so a single writer
# blocks all readers and concurrent writes fail immediately with
# "database is locked". For a service taking parallel POSTs that is a
# correctness/availability bug, not just a perf nit. We enable:
#   * WAL (write-ahead logging): readers don't block the writer and vice-versa.
#   * busy_timeout=5000ms: a contended connection waits/retries instead of
#     erroring out instantly.
# Applied per-connection via a connect event so pooled/recycled connections all
# get it. Only for SQLite (no-op for other backends, which handle this natively).
if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.execute("PRAGMA synchronous=NORMAL")
        finally:
            cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# db/migrations lives next to the app package (project root / db / migrations).
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "db" / "migrations"


def run_migrations(target_engine=engine) -> list[str]:
    """Apply every db/migrations/*.sql file, in sorted order, to the database.

    This is the single source of truth for the runtime schema. Because the
    migration DDL carries the CHECK constraints and indexes (which SQLAlchemy's
    ``create_all`` would NOT emit from the ORM model), running it at startup
    guarantees those guards exist at runtime — not just in db/schema.sql.

    Idempotent: every statement uses ``IF NOT EXISTS``, so it is safe to run on
    every boot. Returns the list of applied migration filenames (for logging).
    """
    if not MIGRATIONS_DIR.is_dir():
        raise FileNotFoundError(f"migrations directory not found: {MIGRATIONS_DIR}")

    applied: list[str] = []
    # executescript handles multi-statement SQL; use the raw DBAPI connection so
    # SQLite runs the whole file (SQLAlchemy's text() is single-statement).
    raw = target_engine.raw_connection()
    try:
        cursor = raw.cursor()
        for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            cursor.executescript(sql_file.read_text())
            applied.append(sql_file.name)
        raw.commit()
    finally:
        raw.close()
    return applied


def get_db():
    """FastAPI dependency that yields a database session and closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
