"""Concurrency tests for the write path under SQLite WAL.

These guard the WAL + busy_timeout hardening in app/database.py: parallel POSTs
must all succeed (no "database is locked" 500s) and the resulting row count /
aggregate must be exactly correct — no lost or double-counted writes.

Without WAL + a busy_timeout, SQLite's default rollback journal serializes
writers with a 0ms timeout, so concurrent inserts intermittently fail. With the
pragmas applied, contended connections wait and retry instead of erroring.
"""

import concurrent.futures

from fastapi.testclient import TestClient

from app.database import engine
from app.main import app


def test_wal_mode_enabled():
    """The connect-event pragmas must actually put the DB in WAL mode."""
    with engine.connect() as conn:
        from sqlalchemy import text

        mode = conn.execute(text("PRAGMA journal_mode")).scalar()
        timeout = conn.execute(text("PRAGMA busy_timeout")).scalar()
    assert str(mode).lower() == "wal", f"expected WAL, got {mode}"
    assert int(timeout) >= 5000, f"expected busy_timeout >= 5000, got {timeout}"


def test_parallel_posts_all_succeed_and_count_is_exact():
    """N concurrent POSTs -> N rows, exact total, zero lock errors."""
    n = 50
    client = TestClient(app)

    def post(i: int):
        return client.post(
            "/api/expenses",
            json={"amount": 10.00, "category": "food", "note": f"c{i}"},
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        responses = list(pool.map(post, range(n)))

    statuses = [r.status_code for r in responses]
    assert all(s == 201 for s in statuses), (
        f"some POSTs failed (locked?): {sorted(set(statuses))}"
    )

    summary = client.get("/api/summary").json()
    assert summary["count"] == n, f"expected {n} rows, got {summary['count']}"
    # 50 * $10.00 = $500.00, exact (integer cents, no float drift).
    assert summary["total"] == 500.00, summary["total"]
    assert summary["by_category"]["food"] == 500.00
