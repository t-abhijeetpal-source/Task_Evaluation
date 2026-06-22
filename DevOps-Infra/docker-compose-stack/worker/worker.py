"""D2 background worker — claims pending jobs and processes them deterministically.

Processing = uppercase the payload, mark ``status='done'``. Uses
``FOR UPDATE SKIP LOCKED`` so multiple worker replicas never double-process a
job. Resilient: if the schema isn't seeded yet, it logs and retries rather than
crashing.

Lifecycle: a SIGTERM/SIGINT handler requests a graceful stop — the worker
finishes the batch it is committing, then exits 0 (so ``docker compose down``
and orchestrator rollouts drain cleanly instead of killing mid-transaction).
"""

from __future__ import annotations

import datetime
import json
import os
import signal
import time
from types import FrameType
from typing import Any

import psycopg

DATABASE_URL = os.environ["DATABASE_URL"]
WORKER_ID = os.environ.get("WORKER_ID", "worker-1")
POLL = float(os.environ.get("POLL_INTERVAL", "1"))
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "10"))

# Flipped by the signal handler; the main loop checks it at safe boundaries.
_shutdown = False


def log(msg: str, **fields: Any) -> None:
    print(
        json.dumps(
            {
                "ts": datetime.datetime.now(datetime.UTC).isoformat(),
                "worker": WORKER_ID,
                "msg": msg,
                **fields,
            }
        ),
        flush=True,
    )


def _request_shutdown(signum: int, _frame: FrameType | None) -> None:
    global _shutdown
    _shutdown = True
    log("shutdown requested", signal=signal.Signals(signum).name)


def install_signal_handlers() -> None:
    signal.signal(signal.SIGTERM, _request_shutdown)
    signal.signal(signal.SIGINT, _request_shutdown)


def process_once(conn: psycopg.Connection[Any]) -> int:
    """Claim and process up to ``BATCH_SIZE`` pending jobs; return the count."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, payload FROM jobs WHERE status = 'pending' "
            "ORDER BY id FOR UPDATE SKIP LOCKED LIMIT %s",
            (BATCH_SIZE,),
        )
        rows = cur.fetchall()
        for job_id, payload in rows:
            result = (payload or "").upper()
            cur.execute(
                "UPDATE jobs SET status='done', result=%s, processed_by=%s, processed_at=now() "
                "WHERE id=%s",
                (result, WORKER_ID, job_id),
            )
            log("processed job", job_id=job_id, result=result)
        conn.commit()
        return len(rows)


def main() -> None:
    install_signal_handlers()
    log("worker starting", target=DATABASE_URL.split("@")[-1])
    while not _shutdown:
        try:
            with psycopg.connect(DATABASE_URL, connect_timeout=5) as conn:
                while not _shutdown:
                    if process_once(conn) == 0:
                        time.sleep(POLL)
        except Exception as exc:  # keep the loop alive across transient DB errors
            if _shutdown:
                break
            log("worker error (will retry)", error=str(exc))
            time.sleep(POLL)
    log("worker stopped")


if __name__ == "__main__":
    main()
