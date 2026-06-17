#!/usr/bin/env bash
#
# D6 load generator (Phase 6).
# Issues a realistic mix of traffic against the instrumented service so that
# request, error, and latency metrics move dynamically. Includes intentionally
# flawed requests (422 validation + 500 synthetic + 404 not-found) to drive the
# error-rate metric.
#
# Usage:  ./scripts/generate-load.sh [BASE_URL] [TOTAL_REQUESTS] [CONCURRENCY]
# Default: http://localhost:8000  600 requests  20-way concurrency
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
TOTAL="${2:-600}"
CONCURRENCY="${3:-20}"

echo "==> Target:        ${BASE_URL}"
echo "==> Total requests: ${TOTAL}  (concurrency ${CONCURRENCY})"

# Weighted endpoint mix: mostly healthy traffic, a steady minority of errors.
hit() {
  local n="$1"
  local mod=$(( n % 10 ))
  case "$mod" in
    0|1|2) curl -s -o /dev/null "${BASE_URL}/health" ;;
    3|4)   curl -s -o /dev/null "${BASE_URL}/ready" ;;
    5|6)   curl -s -o /dev/null "${BASE_URL}/add?a=${n}&b=$(( n + 1 ))" ;;
    7)     curl -s -o /dev/null "${BASE_URL}/" ;;
    8)     curl -s -o /dev/null "${BASE_URL}/add?a=oops&b=2" ;;   # 422 validation error
    9)     # Alternate 500 / 404. Use the tens digit's parity: the ones digit is
           # fixed at 9 (always odd), so divide it out before testing parity.
           if (( (n / 10) % 2 == 0 )); then
             curl -s -o /dev/null "${BASE_URL}/error"             # 500 synthetic error
           else
             curl -s -o /dev/null "${BASE_URL}/does-not-exist"    # 404 not found
           fi ;;
  esac
}
export -f hit
export BASE_URL

echo "==> Phase A: sequential warm-up (50 requests)"
for n in $(seq 1 50); do hit "$n"; done

echo "==> Phase B: concurrent burst ($(( TOTAL - 50 )) requests)"
seq 51 "${TOTAL}" | xargs -P "${CONCURRENCY}" -I {} bash -c 'hit "$@"' _ {}

echo "==> Load complete: ${TOTAL} requests issued."
