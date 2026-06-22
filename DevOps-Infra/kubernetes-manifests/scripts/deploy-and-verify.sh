#!/usr/bin/env bash
# End-to-end kind proof: build → side-load → apply (kustomize) → rollout →
# port-forward → curl every endpoint → report. This is the automation behind
# the manual steps in the README and the validation record.
#
# Usage:
#   scripts/deploy-and-verify.sh            # deploy + verify, leave cluster up
#   scripts/deploy-and-verify.sh --teardown # ...then delete the cluster at the end
#
# Requires: docker, kind, kubectl. Safe to re-run (idempotent on the cluster).
set -euo pipefail

cd "$(dirname "$0")/.."

CLUSTER="${CLUSTER:-d4-cluster}"
IMAGE="${IMAGE:-d4-sample:v1}"
NS="d4-sample"
OVERLAY="${OVERLAY:-k8s/overlays/dev}"
LOCAL_PORT="${LOCAL_PORT:-18080}"
TEARDOWN=0
PF_PID=""

[[ "${1:-}" == "--teardown" ]] && TEARDOWN=1

log() { printf '\n\033[1;36m== %s ==\033[0m\n' "$*"; }
fail() { printf '\033[1;31mFAIL: %s\033[0m\n' "$*" >&2; exit 1; }

cleanup() {
  [[ -n "$PF_PID" ]] && kill "$PF_PID" 2>/dev/null || true
  if [[ "$TEARDOWN" == "1" ]]; then
    log "Teardown: deleting kind cluster '$CLUSTER'"
    kind delete cluster --name "$CLUSTER" || true
  fi
}
trap cleanup EXIT

for tool in docker kind kubectl; do
  command -v "$tool" >/dev/null 2>&1 || fail "$tool not found on PATH"
done

# --- 1. cluster -------------------------------------------------------------
if kind get clusters 2>/dev/null | grep -qx "$CLUSTER"; then
  log "Reusing existing kind cluster '$CLUSTER'"
else
  log "Creating kind cluster '$CLUSTER'"
  kind create cluster --name "$CLUSTER" --wait 120s
fi
kubectl config use-context "kind-$CLUSTER" >/dev/null

# --- 2. build + side-load ---------------------------------------------------
log "Building image $IMAGE"
docker build -t "$IMAGE" .
log "Side-loading $IMAGE into kind (no registry)"
kind load docker-image "$IMAGE" --name "$CLUSTER"

# --- 3. apply via kustomize -------------------------------------------------
log "Applying $OVERLAY"
kubectl apply -k "$OVERLAY"

# --- 4. rollout -------------------------------------------------------------
log "Waiting for rollout"
kubectl rollout status "deployment/d4-sample" -n "$NS" --timeout=120s \
  || { kubectl describe deploy/d4-sample -n "$NS"; fail "rollout did not complete"; }

# --- 5. report --------------------------------------------------------------
log "Cluster state"
kubectl get deploy,pods,svc,hpa,pdb,netpol,sa -n "$NS"
READY=$(kubectl get deploy/d4-sample -n "$NS" -o jsonpath='{.status.readyReplicas}')
RESTARTS=$(kubectl get pods -n "$NS" -l app.kubernetes.io/name=d4-sample \
  -o jsonpath='{range .items[*]}{.status.containerStatuses[0].restartCount}{"\n"}{end}' | paste -sd+ - | bc)
echo "ready replicas: ${READY:-0} | total restarts: ${RESTARTS:-0}"
[[ "${READY:-0}" -ge 1 ]] || fail "no ready replicas"

# --- 6. port-forward + curl proof ------------------------------------------
log "Port-forward svc/d4-sample $LOCAL_PORT->80 and curl every endpoint"
kubectl port-forward -n "$NS" "service/d4-sample" "$LOCAL_PORT:80" >/dev/null 2>&1 &
PF_PID=$!
# Wait for the tunnel to come up.
for _ in $(seq 1 20); do
  curl -fsS "http://127.0.0.1:$LOCAL_PORT/health" >/dev/null 2>&1 && break
  sleep 0.5
done

check() { # url  expected_status  label
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' "$1")
  if [[ "$code" == "$2" ]]; then
    echo "  ✓ $3 -> $code"
  else
    fail "$3 expected $2 got $code"
  fi
}
check "http://127.0.0.1:$LOCAL_PORT/health"        200 "GET /health"
check "http://127.0.0.1:$LOCAL_PORT/ready"         200 "GET /ready"
check "http://127.0.0.1:$LOCAL_PORT/"              200 "GET /"
check "http://127.0.0.1:$LOCAL_PORT/metrics"       200 "GET /metrics"
check "http://127.0.0.1:$LOCAL_PORT/add?a=2&b=3"   200 "GET /add (valid)"
check "http://127.0.0.1:$LOCAL_PORT/add?a=x&b=3"   422 "GET /add (invalid)"

echo "  ConfigMap injection over HTTP:"
curl -s "http://127.0.0.1:$LOCAL_PORT/" | sed 's/^/    /'

echo ""
echo "✅ D4 verified online on kind (rollout healthy, all endpoints proven)."
