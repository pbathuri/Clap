#!/usr/bin/env bash
# M53 — prebake static snapshot for deploy builds.
set -euo pipefail

INV="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$INV/.." && pwd)"
OUT="$INV/public/edge-desktop-snapshot.json"

if ! command -v workflow-dataset &>/dev/null; then
  echo "ERROR: workflow-dataset not found on PATH. Activate venv or install -e."
  exit 1
fi

cd "$REPO"
echo ">>> Prebaking snapshot for deploy..."
workflow-dataset demo edge-desktop-snapshot --repo-root "$REPO" -o "$OUT"

if [[ ! -s "$OUT" ]]; then
  echo "ERROR: snapshot missing or empty: $OUT"
  exit 1
fi

echo ">>> OK: $(wc -c < "$OUT") bytes -> $OUT"
