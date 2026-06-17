#!/usr/bin/env bash
# End-to-end test against the LIVE stack:
#   client -> API (DB write) -> worker consumption -> DB update -> verification query.
set -euo pipefail
API="${API_URL:-http://localhost:8080}"

echo "[e2e] 1) API health (proves API <-> DB connectivity)"
curl -fsS "$API/health"; echo

echo "[e2e] 2) create a job via the API (DB write)"
JOB=$(curl -fsS -X POST "$API/jobs" -H 'content-type: application/json' -d '{"payload":"hello-d2"}')
echo "  -> $JOB"
ID=$(echo "$JOB" | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')

echo "[e2e] 3) poll until the WORKER processes job id=$ID (DB update)"
STATUS=""; RESP=""
for _ in $(seq 1 30); do
  RESP=$(curl -fsS "$API/jobs/$ID")
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
