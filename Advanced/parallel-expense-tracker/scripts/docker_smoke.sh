#!/usr/bin/env bash
# Optional Docker smoke test: build the image, run the container, wait for the
# HEALTHCHECK to report healthy, POST an expense, verify the summary, tear down.
# Skips cleanly (exit 0) if Docker is not available, so it never blocks a verify
# run on machines without Docker.
#
# Run from the project root:  bash scripts/docker_smoke.sh
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v docker >/dev/null 2>&1; then
  echo "== docker smoke: SKIPPED (docker not found) =="
  exit 0
fi
if ! docker info >/dev/null 2>&1; then
  echo "== docker smoke: SKIPPED (docker daemon not running) =="
  exit 0
fi

IMAGE="expense-tracker:smoke"
NAME="expense-tracker-smoke-$$"
PORT="${DOCKER_SMOKE_PORT:-8138}"
BASE="http://127.0.0.1:${PORT}"

cleanup() {
  docker rm -f "${NAME}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "== docker smoke: building image =="
docker build -t "${IMAGE}" . >/dev/null

echo "== docker smoke: running container on :${PORT} =="
docker run -d --name "${NAME}" -p "${PORT}:8000" "${IMAGE}" >/dev/null

# Wait for the container's own HEALTHCHECK to flip to healthy.
echo "== docker smoke: waiting for healthy =="
for i in $(seq 1 60); do
  status="$(docker inspect -f '{{.State.Health.Status}}' "${NAME}" 2>/dev/null || echo unknown)"
  if [[ "${status}" == "healthy" ]]; then break; fi
  if [[ "${status}" == "unhealthy" ]]; then
    docker logs "${NAME}"; echo "✗ container became unhealthy"; exit 1
  fi
  sleep 1
done
[[ "${status}" == "healthy" ]] || { docker logs "${NAME}"; echo "✗ never became healthy"; exit 1; }
echo "  ✓ container healthy (deep /api/health passed inside container)"

# Exercise the API through the published port.
code="$(curl -s -o /dev/null -w '%{http_code}' -X POST "${BASE}/api/expenses" \
  -H 'Content-Type: application/json' -d '{"amount":99.00,"category":"utilities"}')"
[[ "${code}" == "201" ]] && echo "  ✓ POST /api/expenses -> 201" || { echo "✗ POST got ${code}"; exit 1; }

curl -fsS "${BASE}/api/summary" | grep -q '"total":99' \
  && echo "  ✓ GET /api/summary -> total 99.0" || { echo "✗ summary mismatch"; exit 1; }

curl -fsS -o /dev/null "${BASE}/" && echo "  ✓ GET / (frontend in container) -> 200" || { echo "✗ frontend"; exit 1; }

echo "== docker smoke: PASSED =="
