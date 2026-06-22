#!/usr/bin/env bash
# End-to-end test against the LIVE stack:
#   client -> API (DB write) -> worker consumption -> DB update -> verification query.
# Honors API_KEY: when set (in the env or .env), the matching X-API-Key header is
# sent on protected routes so the test works with auth enabled or disabled.
set -euo pipefail
API="${API_URL:-http://localhost:8080}"

# Pick up API_KEY from a sibling .env if not already exported.
if [ -z "${API_KEY:-}" ] && [ -f "$(dirname "$0")/../.env" ]; then
  API_KEY="$(grep -E '^API_KEY=' "$(dirname "$0")/../.env" | tail -1 | cut -d= -f2-)"
fi
AUTH=()
if [ -n "${API_KEY:-}" ]; then
  AUTH=(-H "X-API-Key: ${API_KEY}")
  echo "[e2e] (auth enabled — sending X-API-Key header)"
fi

echo "[e2e] 1) API health (proves API <-> DB connectivity)"
curl -fsS "$API/health"; echo

echo "[e2e] 2) create a job via the API (DB write)"
JOB=$(curl -fsS -X POST "$API/jobs" "${AUTH[@]+"${AUTH[@]}"}" -H 'content-type: application/json' -d '{"payload":"hello-d2"}')
echo "  -> $JOB"
ID=$(echo "$JOB" | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')

echo "[e2e] 3) poll until the WORKER processes job id=$ID (DB update)"
STATUS=""; RESP=""
for _ in $(seq 1 30); do
  RESP=$(curl -fsS "$API/jobs/$ID" "${AUTH[@]+"${AUTH[@]}"}")
  STATUS=$(echo "$RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])')
  [ "$STATUS" = "done" ] && break
  sleep 1
done

RESULT=$(echo "$RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("result"))')
echo "  -> final job: $RESP"
echo "[e2e] expected: status=done result=HELLO-D2"
echo "[e2e] actual:   status=$STATUS result=$RESULT"

if [ "$STATUS" = "done" ] && [ "$RESULT" = "HELLO-D2" ]; then
  echo "[e2e] PASS"
  exit 0
fi
echo "[e2e] FAIL"
exit 1
