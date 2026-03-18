#!/usr/bin/env bash
# M51: Launch USB investor demo from repo root (or set WORKFLOW_DEMO_BUNDLE_ROOT).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
export PYTHONPATH="${ROOT}/src:${PYTHONPATH:-}"
export WORKFLOW_DEMO_BUNDLE_ROOT="${WORKFLOW_DEMO_BUNDLE_ROOT:-$ROOT}"
cd "$ROOT"
if [[ $# -eq 0 ]]; then
  exec python3 -m workflow_dataset.cli demo bootstrap
fi
exec python3 -m workflow_dataset.cli demo "$@"
