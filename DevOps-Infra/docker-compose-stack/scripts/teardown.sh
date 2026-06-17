#!/usr/bin/env bash
# Stop and remove the stack (containers, network, volumes).
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose down -v
echo "[teardown] stack removed"
