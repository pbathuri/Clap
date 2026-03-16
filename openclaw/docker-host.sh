#!/usr/bin/env bash
# Run OpenClaw in Docker from the workspace root.
# This script changes into the openclaw repo directory and runs docker-setup.sh.
set -euo pipefail
REPO_DIR="${OPENCLAW_REPO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/openclaw" && pwd)}"
if [[ ! -f "$REPO_DIR/docker-setup.sh" ]]; then
  echo "ERROR: docker-setup.sh not found at $REPO_DIR" >&2
  echo "Set OPENCLAW_REPO_DIR to the repo root that contains Dockerfile and docker-setup.sh." >&2
  exit 1
fi
exec "$REPO_DIR/docker-setup.sh" "$@"
