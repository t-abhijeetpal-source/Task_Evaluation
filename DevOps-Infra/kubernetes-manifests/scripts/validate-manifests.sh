#!/usr/bin/env bash
# Offline, cluster-free structural validation of the Kubernetes manifests.
#
#   1. kustomize build (dev + prod overlays)         — overlays compose cleanly
#   2. kubeconform -strict                           — every object matches its
#                                                      upstream API schema
#   3. kube-score (best-effort, non-blocking)        — production-readiness lint
#   4. kubectl server dry-run (only if a cluster is  — apiserver admission check
#      reachable)
#
# Exit non-zero on any kustomize/kubeconform failure. kube-score and the server
# dry-run are advisory (the first two gates are the hard contract).
set -euo pipefail

cd "$(dirname "$0")/.."

OVERLAYS=(dev prod)
K8S_VERSION="${K8S_VERSION:-1.32.0}" # schema set kubeconform validates against

# --- kustomize: prefer standalone, fall back to `kubectl kustomize` ----------
build() {
  if command -v kustomize >/dev/null 2>&1; then
    kustomize build "$1"
  else
    kubectl kustomize "$1"
  fi
}

echo "== 1/4 kustomize build (dev + prod overlays) =="
for ov in "${OVERLAYS[@]}"; do
  build "k8s/overlays/$ov" >/dev/null
  echo "  ✓ k8s/overlays/$ov builds"
done

echo "== 2/4 kubeconform (-strict, k8s $K8S_VERSION) =="
if ! command -v kubeconform >/dev/null 2>&1; then
  echo "  ✗ kubeconform not installed — install: brew install kubeconform" >&2
  echo "    (CI installs it; this gate is required)" >&2
  exit 1
fi
for ov in "${OVERLAYS[@]}"; do
  echo "  -- overlay: $ov"
  build "k8s/overlays/$ov" | kubeconform \
    -strict -summary \
    -kubernetes-version "$K8S_VERSION" \
    -schema-location default
done

echo "== 3/4 kube-score (advisory) =="
if command -v kube-score >/dev/null 2>&1; then
  # Don't fail the build on kube-score: the deliberate design choices it flags
  # (e.g. annotation-based scrape vs ServiceMonitor) are documented.
  build "k8s/overlays/dev" | kube-score score - || true
else
  echo "  (kube-score not installed — skipped; CI runs it)"
fi

echo "== 4/4 server-side dry-run (only if a cluster is reachable) =="
if kubectl cluster-info >/dev/null 2>&1; then
  build "k8s/overlays/dev" | kubectl apply --dry-run=server -f - || {
    echo "  (server dry-run reported issues — see above)" >&2
  }
else
  echo "  (no cluster reachable — skipped; offline schema validation above is authoritative)"
fi

echo ""
echo "✅ Manifest validation passed (kustomize + kubeconform strict)."
