#!/usr/bin/env bash
# Run the dataset build using the project venv (has workflow_dataset + pyarrow).
# Usage: from project root: ./scripts/run_build.sh
#    or: bash scripts/run_build.sh
set -e
cd "$(dirname "$0")/.."
if [[ ! -d .venv ]]; then
  echo "No .venv found. Create one with: python3 -m venv .venv && .venv/bin/pip install -e ."
  exit 1
fi
.venv/bin/python -m workflow_dataset.cli build --config configs/settings.yaml
