# Load testing — `GET /api/summary`

The A6 benchmark (`Advanced/performance-optimization/bench_summary.py`) measures **single-threaded**
latency in-process via `TestClient`. This complements it with a **concurrent, over-the-wire** load test
using [k6](https://k6.io), so the optimization is validated under realistic parallelism (the case where
the old ORM-hydration path would queue requests and the write path could hit SQLite lock contention).

## Prerequisites

- `k6` installed (`brew install k6`, or see k6 docs). CI skips the load test cleanly if k6 is absent.
- The service running locally with a seeded database.

## 1. Seed and run the service

```bash
cd Advanced/parallel-expense-tracker
. .venv/bin/activate

# Seed ~50k rows into a real DB file, then serve it.
A6_N=50000 python - <<'PY'
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./data/load.db")
from app.database import engine, Base, SessionLocal
from app.models import Expense
Base.metadata.create_all(bind=engine)
s = SessionLocal()
s.bulk_insert_mappings(Expense, [
    {"amount_cents": ((i % 500)+1)*100+50, "category": ["food","transport","utilities","groceries","entertainment","health"][i % 6],
     "note": "seed", "created_at": "2026-01-01T00:00:00+00:00"} for i in range(50000)])
s.commit(); s.close()
print("seeded 50000 rows into ./data/load.db")
PY

DATABASE_URL=sqlite:///./data/load.db uvicorn app.main:app --port 8000
```

## 2. Run the load test (in another shell)

```bash
cd Advanced/parallel-expense-tracker
BASE_URL=http://localhost:8000 k6 run scripts/load_summary.k6.js
```

## Profile

- **summary_read:** ramps 0→20 VUs, holds 20 for 30s, drains. Each VU GETs `/api/summary` every 0.5s.
- **occasional_write:** 2 constant VUs POST a new expense every 1s, so reads run against a moving table
  and the WAL concurrency path (`app/database.py`) is exercised.

## Thresholds (fail the run if breached)

| Threshold | Meaning |
|---|---|
| `http_req_duration{endpoint:summary} p(95) < 100ms` | The SQL `GROUP BY` keeps summary fast under load. A regression to per-row ORM summation blows past this immediately. |
| `http_req_failed rate < 1%` | WAL + `busy_timeout=5000` should prevent `database is locked` errors from concurrent writes. |

## Interpreting results

- p95 staying well under 100 ms under 20 concurrent readers confirms the optimization holds at concurrency,
  not just in a micro-benchmark.
- A near-zero `http_req_failed` rate confirms the WAL hardening: pre-WAL, the write VUs would intermittently
  return 500s under contention.
- If you remove the A6 optimization (revert to `db.query(Expense).all()`), expect p95 to exceed the
  threshold and throughput to collapse as requests queue on CPU-bound hydration.

> Note: SQLite is single-writer even with WAL; this load profile targets a read-heavy dashboard workload.
> For write-heavy concurrency, the production recommendation is Postgres (out of scope for A2).
