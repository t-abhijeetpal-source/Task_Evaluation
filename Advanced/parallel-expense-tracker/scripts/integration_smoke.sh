#!/usr/bin/env bash
# Live HTTP integration smoke test for the Expense Tracker.
# Starts a real uvicorn server against a throwaway SQLite DB, exercises every
# endpoint over the network (including the NaN -> 422 regression and the static
# frontend), then tears the server down. Exits non-zero on the first failure.
#
# Run from the project root:  bash scripts/integration_smoke.sh
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python}"
PORT="${SMOKE_PORT:-8137}"
BASE="http://127.0.0.1:${PORT}"
TMP="$(mktemp -d)"
export DATABASE_URL="sqlite:///${TMP}/smoke.db"

pass=0
fail() { echo "  ✗ $1"; exit 1; }
ok()   { echo "  ✓ $1"; pass=$((pass+1)); }

cleanup() {
  [[ -n "${SERVER_PID:-}" ]] && kill "${SERVER_PID}" 2>/dev/null || true
  wait "${SERVER_PID}" 2>/dev/null || true
  rm -rf "${TMP}"
}
trap cleanup EXIT

echo "== integration smoke: starting uvicorn on :${PORT} (temp DB) =="
"${PYTHON}" -m uvicorn app.main:app --host 127.0.0.1 --port "${PORT}" \
  >"${TMP}/server.log" 2>&1 &
SERVER_PID=$!

# Wait for readiness (deep health).
for i in $(seq 1 50); do
  if curl -fsS "${BASE}/api/health" >/dev/null 2>&1; then break; fi
  if ! kill -0 "${SERVER_PID}" 2>/dev/null; then
    echo "--- server log ---"; cat "${TMP}/server.log"; fail "server exited during boot"
  fi
  sleep 0.2
done

# --- helpers: capture body + status code ---
req() { # method path [data] [content-type]
  local method="$1" path="$2" data="${3:-}" ctype="${4:-application/json}"
  if [[ -n "${data}" ]]; then
    curl -s -o "${TMP}/body" -w "%{http_code}" -X "${method}" \
      -H "Content-Type: ${ctype}" -d "${data}" "${BASE}${path}"
  else
    curl -s -o "${TMP}/body" -w "%{http_code}" -X "${method}" "${BASE}${path}"
  fi
}

echo "== assertions =="

# 1. Deep health.
[[ "$(req GET /api/health)" == "200" ]] && grep -q '"status":"ok"' "${TMP}/body" \
  && ok "GET /api/health -> 200 {status:ok}" || fail "health check"

# 2. Create valid expense.
[[ "$(req POST /api/expenses '{"amount":12.50,"category":"food","note":"lunch"}')" == "201" ]] \
  && ok "POST /api/expenses (valid) -> 201" || fail "create valid"

# 3. NaN must be rejected with 422 (regression: previously 500).
code="$(req POST /api/expenses '{"amount": NaN, "category": "food"}')"
[[ "${code}" == "422" ]] && ok "POST NaN -> 422 (not 500)" || fail "NaN returned ${code}, expected 422"

# 4. Negative amount -> documented 422 contract.
code="$(req POST /api/expenses '{"amount":-5,"category":"food"}')"
[[ "${code}" == "422" ]] && grep -q "amount must be positive" "${TMP}/body" \
  && ok "POST negative -> 422 {error: amount must be positive}" || fail "negative amount"

# 5. Second valid expense + exact aggregation.
req POST /api/expenses '{"amount":0.10,"category":"food"}' >/dev/null
req POST /api/expenses '{"amount":0.20,"category":"food"}' >/dev/null
req GET /api/summary >/dev/null
"${PYTHON}" - "${TMP}/body" <<'PY' || fail "summary aggregation"
import json, sys
body = json.load(open(sys.argv[1]))
# 12.50 + 0.10 + 0.20 = 12.80 exactly (integer-cent aggregation).
assert body["by_category"]["food"] == 12.80, body
assert body["total"] == 12.80, body
PY
ok "GET /api/summary -> exact total 12.80 (no float drift)"

# 6. List endpoint.
[[ "$(req GET /api/expenses)" == "200" ]] && ok "GET /api/expenses -> 200" || fail "list"

# 7. Static frontend served.
[[ "$(req GET /)" == "200" ]] && grep -qi "expense" "${TMP}/body" \
  && ok "GET / -> 200 (frontend shell)" || fail "frontend root"
[[ "$(req GET /app.js)" == "200" ]] && ok "GET /app.js -> 200" || fail "app.js"

echo "== integration smoke: ${pass} checks passed =="
