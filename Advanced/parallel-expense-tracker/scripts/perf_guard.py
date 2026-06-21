"""Performance regression gate for GET /api/summary (A6 linkage).

Runs the A6 benchmark harness (Advanced/performance-optimization/bench_summary.py)
against this app and fails (exit 1) if the p50 latency regresses past a
threshold. The A6 optimization moved aggregation into a SQL GROUP BY over an
indexed integer-cents column; the optimized baseline is ~30ms p50 @ 50k rows on
Python 3.12.7. We gate at a ceiling that catches a real regression (e.g. an
accidental return to per-row Python summation, which is ~330ms) while tolerating
CI noise, and emit a WARNING band below the ceiling for early drift signal.

Usage:
    python scripts/perf_guard.py                 # N=50000, p50 <= 50ms (warn >= 40ms)
    A6_N=20000 P50_MAX_MS=40 python scripts/perf_guard.py
    python scripts/perf_guard.py --json          # parse bench --json instead of text
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

A2_DIR = Path(__file__).resolve().parent.parent
BENCH = A2_DIR.parent / "performance-optimization" / "bench_summary.py"
P50_MAX_MS = float(os.environ.get("P50_MAX_MS", "50"))
P50_WARN_MS = float(os.environ.get("P50_WARN_MS", "40"))


def _run_bench(use_json: bool):
    env = dict(os.environ)
    env.setdefault("A6_N", "50000")
    env.setdefault("A6_ITERS", "15")
    cmd = [sys.executable, str(BENCH)]
    if use_json:
        cmd.append("--json")
    proc = subprocess.run(cmd, cwd=str(A2_DIR), env=env, capture_output=True, text=True)
    return proc, env["A6_N"]


def main() -> int:
    if not BENCH.is_file():
        print(f"perf_guard: benchmark not found at {BENCH}", file=sys.stderr)
        return 1

    use_json = "--json" in sys.argv
    proc, n = _run_bench(use_json)

    if not use_json:
        sys.stdout.write(proc.stdout)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        print("perf_guard: benchmark process failed", file=sys.stderr)
        return 1

    if use_json:
        try:
            data = json.loads(proc.stdout)
            p50 = float(data["latency_ms"]["p50"])
        except (ValueError, KeyError) as exc:
            print(f"perf_guard: could not read p50 from JSON: {exc}", file=sys.stderr)
            return 1
    else:
        match = re.search(r"p50\s*=\s*([0-9.]+)\s*ms", proc.stdout)
        if not match:
            print("perf_guard: could not parse p50 from benchmark output", file=sys.stderr)
            return 1
        p50 = float(match.group(1))

    if p50 > P50_MAX_MS:
        print(
            f"\n❌ PERF REGRESSION: p50={p50:.2f}ms > {P50_MAX_MS:.0f}ms ceiling "
            f"(N={n}). The A6 SQL-aggregation optimization may have regressed.",
            file=sys.stderr,
        )
        return 1

    if p50 > P50_WARN_MS:
        print(
            f"\n⚠️  PERF WARNING: p50={p50:.2f}ms is within ceiling {P50_MAX_MS:.0f}ms "
            f"but above warn band {P50_WARN_MS:.0f}ms (N={n}). Watch for drift."
        )
        return 0

    print(
        f"\n✅ PERF OK: p50={p50:.2f}ms <= {P50_WARN_MS:.0f}ms warn band "
        f"(ceiling {P50_MAX_MS:.0f}ms, N={n}). A6 summary optimization intact."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
