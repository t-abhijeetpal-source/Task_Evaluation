#!/usr/bin/env bash
# Build and push the D4 image to GitHub Container Registry (GHCR), then print
# the immutable digest to pin into k8s/overlays/prod/kustomization.yaml.
#
# Usage:
#   echo "$GHCR_PAT" | docker login ghcr.io -u <user> --password-stdin
#   REGISTRY=ghcr.io/<owner> TAG=1.0.0 scripts/push-image.sh
#
# In CI, prefer docker/build-push-action with OIDC over a long-lived PAT.
set -euo pipefail

cd "$(dirname "$0")/.."

REGISTRY="${REGISTRY:-ghcr.io/example}"
NAME="${NAME:-d4-sample}"
TAG="${TAG:-1.0.0}"
REF="$REGISTRY/$NAME:$TAG"

echo "== Building $REF =="
docker build -t "$REF" .

echo "== Pushing $REF =="
docker push "$REF"

echo "== Immutable digest (pin this in the prod overlay) =="
DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' "$REF")
echo "  $DIGEST"
echo ""
echo "Update k8s/overlays/prod/kustomization.yaml images[].digest to:"
echo "  ${DIGEST#*@}"
