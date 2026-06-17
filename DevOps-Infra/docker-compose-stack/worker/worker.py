"""D2 background worker — claims pending jobs and processes them (deterministically).

Processing = uppercase the payload, mark status='done'. Uses FOR UPDATE SKIP LOCKED
so multiple worker replicas never double-process a job. Resilient: if the schema
isn't seeded yet, it logs and retries rather than crashing.
"""
import datetime
import json
import os
import time

import psycopg

DATABASE_URL = os.environ["DATABASE_URL"]
WORKER_ID = os.environ.get("WORKER_ID", "worker-1")
POLL = float(os.environ.get("POLL_INTERVAL", "1"))


def log(msg, **fields):
    print(json.dumps({"ts": datetime.datetime.utcnow().isoformat() + "Z",
                      "worker": WORKER_ID, "msg": msg, **fields}), flush=True)


def process_once(conn) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, payload FROM jobs WHERE status = 'pending' "
            "ORDER BY id FOR UPDATE SKIP LOCKED LIMIT 10"
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


def main():
    log("worker starting", target=DATABASE_URL.split("@")[-1])
    while True:
        try:
            with psycopg.connect(DATABASE_URL, connect_timeout=5) as conn:
                while True:
                    if process_once(conn) == 0:
                        time.sleep(POLL)
        except Exception as exc:  # noqa: BLE001 — keep the loop alive (e.g. pre-seed)
            log("worker error (will retry)", error=str(exc))
            time.sleep(POLL)


if __name__ == "__main__":
    main()
