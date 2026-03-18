#!/usr/bin/env bash
# M52.6 — Canonical prefetch before investor meeting.
# Run from anywhere; requires workflow-dataset on PATH (venv active).
set -euo pipefail

INV="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$INV/.." && pwd)"
OUT="$INV/public/edge-desktop-snapshot.json"

mkdir -p "$INV/public"

if ! command -v workflow-dataset &>/dev/null; then
  echo "ERROR: workflow-dataset not found. From repo root:"
  echo "  cd $REPO && source .venv/bin/activate  # or your venv"
  echo "  pip install -e .  # if needed"
  exit 1
fi

cd "$REPO"
echo ">>> Writing snapshot (repo-root: $REPO) ..."
workflow-dataset demo edge-desktop-snapshot --repo-root "$REPO" -o "$OUT"

if [[ ! -s "$OUT" ]]; then
  echo "ERROR: snapshot missing or empty: $OUT"
  exit 1
fi

echo ">>> OK: $(wc -c < "$OUT") bytes -> $OUT"
echo ">>> Next: cd $INV && npm run demo:launch"
echo ">>> Browser: http://localhost:5173/?live=1&presenter=1"
