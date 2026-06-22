#!/usr/bin/env bash
#
# One-command end-to-end verification of the D2 stack.
#   build → up --wait (health-gated) → integration E2E → worker log proof → teardown.
# Exits non-zero on the first failed assertion. Always tears the stack down
# unless --keep is passed (then it leaves the stack running for inspection).
#
# Usage:  scripts/verify-stack.sh [--keep]
# Requires: docker (with the compose plugin), curl, python3.
set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE="docker compose"
KEEP=0
[ "${1:-}" = "--keep" ] && KEEP=1

fail() { echo "❌ $*" >&2; exit 1; }
pass() { echo "✅ $*"; }

cleanup() {
  if [ "$KEEP" = "1" ]; then
    echo "==> --keep set: leaving the stack running (tear down with: docker compose down -v)"
  else
    echo "==> Teardown"
    $COMPOSE down -v >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

command -v docker >/dev/null 2>&1 || fail "docker not found on PATH"

# Ensure a .env exists (demo defaults) so compose interpolation resolves.
if [ ! -f .env ]; then
  echo "==> No .env found — seeding demo values from .env.example"
  cp .env.example .env
fi

echo "==> Clean slate (down -v) so the init-seed runs from zero"
$COMPOSE down -v >/dev/null 2>&1 || true

echo "==> Build + start the stack (wait for healthy)"
$COMPOSE up -d --build --wait || fail "stack did not become healthy"
pass "all services healthy (DB gated api/worker startup)"

echo "==> Run the end-to-end integration test"
./scripts/integration-test.sh || fail "integration-test.sh did not PASS"
pass "E2E: POST /jobs → worker → status=done HELLO-D2"

echo "==> Prove the worker never hit a missing-schema error (clean re-up from zero)"
missing=$($COMPOSE logs worker 2>/dev/null | grep -c "does not exist" || true)
[ "$missing" -eq 0 ] || fail "worker logged $missing 'does not exist' errors — seed mount regressed"
pass "worker log clean (0 'does not exist' — initdb seed worked)"

echo "==> Recent worker activity:"
$COMPOSE logs --tail=20 worker

echo ""
echo "🎉 D2 STACK VERIFIED — full API→DB→worker flow healthy."
