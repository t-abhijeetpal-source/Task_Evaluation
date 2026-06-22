#!/usr/bin/env bash
#
# End-to-end verification of the D6 observability stack.
# Brings the stack up, drives traffic, and asserts the full telemetry chain:
#   load → app /metrics → Prometheus scrape (target UP) → PromQL rate non-empty.
# Exits non-zero on the first failed assertion. Always tears the stack down.
#
# Usage:  scripts/verify-stack.sh
# Requires: docker (with the compose plugin), curl.
set -euo pipefail

cd "$(dirname "$0")/.."

APP_URL="http://localhost:8000"
PROM_URL="http://localhost:9090"
COMPOSE="docker compose"

fail() { echo "❌ $*" >&2; exit 1; }
pass() { echo "✅ $*"; }

cleanup() {
  echo "==> Teardown"
  $COMPOSE down -v >/dev/null 2>&1 || true
}
trap cleanup EXIT

command -v docker >/dev/null 2>&1 || fail "docker not found on PATH"

echo "==> Bringing up the stack (build + wait for healthy)"
$COMPOSE up -d --build --wait || fail "docker compose up did not become healthy"

echo "==> Generating load (200 requests)"
./scripts/generate-load.sh "$APP_URL" 200 20 >/dev/null || fail "load generator failed"

echo "==> Assert /metrics exposes http_requests_total"
metrics_body="$(curl -fsS "$APP_URL/metrics")" || fail "could not scrape $APP_URL/metrics"
grep -q "http_requests_total" <<<"$metrics_body" || fail "http_requests_total missing from /metrics"
pass "/metrics exposes http_requests_total"

echo "==> Assert Prometheus target d6-app is UP (retrying)"
target_up=""
for _ in $(seq 1 20); do
  if curl -fsS "$PROM_URL/api/v1/targets?state=active" \
      | grep -q '"job":"d6-app"[^}]*"health":"up"' \
     || curl -fsS "$PROM_URL/api/v1/targets?state=active" \
      | python3 -c 'import sys,json; d=json.load(sys.stdin); sys.exit(0 if any(t["labels"].get("job")=="d6-app" and t["health"]=="up" for t in d["data"]["activeTargets"]) else 1)'; then
    target_up=1; break
  fi
  sleep 2
done
[ -n "$target_up" ] || fail "Prometheus target d6-app never reached health=up"
pass "Prometheus target d6-app is UP"

echo "==> Assert PromQL rate query returns a non-empty result"
query='sum by (status_code) (rate(http_requests_total{service="d6-sample"}[1m]))'
result_count=""
for _ in $(seq 1 20); do
  result_count="$(curl -fsS "$PROM_URL/api/v1/query" --data-urlencode "query=$query" \
    | python3 -c 'import sys,json; print(len(json.load(sys.stdin)["data"]["result"]))')"
  [ "${result_count:-0}" -gt 0 ] && break
  sleep 2
done
[ "${result_count:-0}" -gt 0 ] || fail "PromQL rate query returned no series"
pass "PromQL rate query returned $result_count series"

echo "==> Assert alerting + recording rules loaded"
curl -fsS "$PROM_URL/api/v1/rules" \
  | python3 -c 'import sys,json; d=json.load(sys.stdin); names={r["name"] for g in d["data"]["groups"] for r in g["rules"]}; req={"HighErrorRate","TargetDown","HighLatencyP95"}; sys.exit(0 if req <= names else 1)' \
  || fail "expected alert rules not loaded in Prometheus"
pass "alert + recording rules loaded"

echo ""
echo "🎉 D6 STACK VERIFIED — full telemetry chain healthy."
