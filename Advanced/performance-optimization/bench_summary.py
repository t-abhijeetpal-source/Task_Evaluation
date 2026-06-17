"""A6 benchmark + profiler for A2's GET /api/summary.

Seeds N expenses into a temp SQLite DB, then either TIMES the endpoint (default)
or PROFILES it with cProfile (--profile). Run from the A2 dir so `app` imports:

    cd "Advanced Task/A2"
    .venv/bin/python "../A6/bench_summary.py"            # timing
    .venv/bin/python "../A6/bench_summary.py" --profile  # cProfile hotspots
"""
import os
import sys
import tempfile
import time
import statistics

N = int(os.environ.get("A6_N", "50000"))
ITERS = int(os.environ.get("A6_ITERS", "15"))

# Must set DATABASE_URL before importing the app (read at import time).
_tmp = tempfile.mkdtemp(prefix="a6_")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/bench.db"

# Make the A2 app importable when this script lives in the A6 folder.
sys.path.insert(0, os.getcwd())

from app.database import engine, Base, SessionLocal  # noqa: E402
from app.models import Expense  # noqa: E402
from app.main import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

CATEGORIES = ["food", "transport", "utilities", "groceries", "entertainment", "health"]


def seed(n: int) -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    s = SessionLocal()
    rows = [
        {
            "amount": float((i % 500) + 1) + 0.50,
            "category": CATEGORIES[i % len(CATEGORIES)],
            "note": "n",
            "created_at": "2026-01-01T00:00:00+00:00",
        }
        for i in range(n)
    ]
    s.bulk_insert_mappings(Expense, rows)
    s.commit()
    s.close()


def main() -> None:
    profile = "--profile" in sys.argv
    print(f"env: python={sys.version.split()[0]}  N={N}  iters={ITERS}  db=sqlite(temp)")
    t0 = time.perf_counter()
    seed(N)
    print(f"seeded {N} rows in {(time.perf_counter()-t0):.2f}s")

    client = TestClient(app)
    r = client.get("/api/summary")  # warm-up
    assert r.status_code == 200, r.text
    body = r.json()
    print(f"correctness: count={body['count']}  total={body['total']:.2f}  "
          f"categories={len(body['by_category'])}")

    if profile:
        import cProfile
        import pstats
        import io
        pr = cProfile.Profile()
        pr.enable()
        for _ in range(10):
            client.get("/api/summary")
        pr.disable()
        st = pstats.Stats(pr, stream=(buf := io.StringIO())).sort_stats("tottime")
        st.print_stats(12)
        print("\n===== cProfile (top by tottime, 10 calls) =====")
        print(buf.getvalue())
        return

    samples = []
    for _ in range(ITERS):
        t = time.perf_counter()
        client.get("/api/summary")
        samples.append((time.perf_counter() - t) * 1000.0)
    samples.sort()
    print(f"\n/api/summary latency over {ITERS} runs (N={N}):")
    print(f"  min   = {min(samples):.2f} ms")
    print(f"  p50   = {statistics.median(samples):.2f} ms")
    print(f"  p95   = {samples[int(len(samples)*0.95)-1]:.2f} ms")
    print(f"  max   = {max(samples):.2f} ms")
    print(f"  mean  = {statistics.mean(samples):.2f} ms")


if __name__ == "__main__":
    main()
