#!/usr/bin/env bash
# A3 end-to-end integration test (HARDENED):
#   Client -> FastAPI (enqueue) -> Node worker -> Rust engine -> score -> POST back -> GET shows score
# Runs the REAL components and asserts scores against the canonical contract vectors.
# Fails loudly rather than testing a stale server: frees the port first, verifies our server
# bound, and asserts the queue actually received the work.
set -u
# Resolve the component root from this script's location (robust to renames/moves).
A3="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${A3_PORT:-8078}"
RUNDIR="$A3/integration-tests/.run"
QUEUE_DIR="$RUNDIR/queue"
DB="$RUNDIR/a3.db"
# A5-18: these previously referenced $polyglot-fraud-system — an UNBOUND variable
# under `set -u` that aborted the script before any component started. Use $A3
# (resolved from this script's own location above).
ENGINE="$A3/rust-engine/target/release/fraud-engine"
PYBIN="$A3/fastapi-service/.venv/bin/python"
# A5-2 / A5-17: the internal callback is now fail-closed, so the API and the
# worker must share an internal token. Generated per-run.
export A3_INTERNAL_TOKEN="${A3_INTERNAL_TOKEN:-itest-$$-$RANDOM}"

fail() { echo "FAIL: $1"; [ -n "${SP:-}" ] && kill "$SP" 2>/dev/null; exit 1; }

# 0. preconditions + free the port
[ -x "$ENGINE" ] || fail "rust engine binary not built ($ENGINE) — run: cargo build --release"
OLD=$(lsof -tiTCP:$PORT -sTCP:LISTEN 2>/dev/null); [ -n "$OLD" ] && { echo "freeing port $PORT (killing $OLD)"; kill $OLD 2>/dev/null; sleep 1; }
rm -rf "$RUNDIR"; mkdir -p "$QUEUE_DIR"

echo "== starting FastAPI on :$PORT (fresh DB + queue) =="
( cd "$A3/fastapi-service" && QUEUE_DIR="$QUEUE_DIR" DATABASE_URL="sqlite:///$DB" \
    A3_INTERNAL_TOKEN="$A3_INTERNAL_TOKEN" \
    "$PYBIN" -m uvicorn app.main:app --port $PORT >"$RUNDIR/api.log" 2>&1 ) &
SP=$!
UP=""
for i in $(seq 1 40); do
  if ! kill -0 "$SP" 2>/dev/null; then fail "uvicorn process died on startup; see api.log:\n$(cat "$RUNDIR/api.log")"; fi
  if curl -s "localhost:$PORT/health" >/dev/null 2>&1; then UP=1; break; fi
  sleep 0.25
done
[ -n "$UP" ] || fail "server did not become healthy on :$PORT"
grep -q "address already in use" "$RUNDIR/api.log" && fail "port $PORT was occupied — refusing to test a stale server"

echo "== POST 4 canonical transactions =="
post() { curl -s -o /dev/null -w "%{http_code}" -X POST "localhost:$PORT/transactions" -H 'Content-Type: application/json' -d "$1"; }
for body in \
 '{"transaction_id":"txn_base","user_id":"u1","amount":5000,"country":"IN","merchant_category":"electronics","timestamp":"2026-06-17T10:00:00Z"}' \
 '{"transaction_id":"txn_high","user_id":"u1","amount":15000,"country":"IN","merchant_category":"electronics","timestamp":"2026-06-17T10:00:00Z"}' \
 '{"transaction_id":"txn_foreign","user_id":"u1","amount":5000,"country":"US","merchant_category":"electronics","timestamp":"2026-06-17T10:00:00Z"}' \
 '{"transaction_id":"txn_all","user_id":"u1","amount":15000,"country":"US","merchant_category":"gambling","timestamp":"2026-06-17T10:00:00Z"}'; do
  code=$(post "$body"); [ "$code" = "201" ] || fail "POST returned $code (expected 201)"
done

QN=$(ls "$QUEUE_DIR" | wc -l | tr -d ' ')
echo "queued files: $QN"
[ "$QN" = "4" ] || fail "expected 4 queued files, found $QN (server/enqueue not working — would have been a false pass)"

echo "== run Node worker (--once): consumes queue, calls Rust, posts score back =="
( cd "$A3/node-worker" && QUEUE_DIR="$QUEUE_DIR" API_URL="http://localhost:$PORT" ENGINE_BIN="$ENGINE" \
    A3_INTERNAL_TOKEN="$A3_INTERNAL_TOKEN" \
    node src/worker.js --once >"$RUNDIR/worker.log" 2>&1 ) || fail "worker exited non-zero; see worker.log"

echo "== GET each transaction and assert score (expected per CONTRACT.md) =="
"$PYBIN" - "$PORT" <<'PY'
import sys, json, urllib.request
port = sys.argv[1]
expected = {"txn_base":(0,"low"),"txn_high":(40,"medium"),"txn_foreign":(20,"low"),"txn_all":(90,"high")}
ok = True
for tid,(score,risk) in expected.items():
    r = json.load(urllib.request.urlopen(f"http://localhost:{port}/transactions/{tid}"))
    good = (r.get("score")==score and r.get("risk_level")==risk and r.get("status")=="scored")
    ok = ok and good
    print(f"  {tid:12} score={r.get('score')} risk={r.get('risk_level')} status={r.get('status')}  expect={score}/{risk}  {'PASS' if good else 'FAIL'}")
print("INTEGRATION:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
PY
RESULT=$?
kill "$SP" 2>/dev/null
exit $RESULT
