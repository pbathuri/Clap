#!/usr/bin/env bash
# Edge Desktop hardening — CLI snapshot smoke test (dev API adjacent).
set -euo pipefail

INV="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$INV/.." && pwd)"

OUT1="${TMPDIR:-/tmp}/edge_desktop_snapshot.json"
OUT2="${TMPDIR:-/tmp}/edge_desktop_live_adapter_snapshot.json"

if ! command -v workflow-dataset &>/dev/null; then
  echo "ERROR: workflow-dataset not found on PATH. Activate venv or install -e."
  exit 1
fi

echo ">>> Repo root: $REPO"
echo ">>> Writing edge-desktop-snapshot..."
workflow-dataset demo edge-desktop-snapshot --repo-root "$REPO" -o "$OUT1"
[[ -s "$OUT1" ]] || { echo "ERROR: snapshot missing or empty: $OUT1"; exit 1; }

echo ">>> Writing live-adapter snapshot (presenter-fast)..."
workflow-dataset demo live-adapter-snapshot --repo-root "$REPO" --presenter-fast -o "$OUT2"
[[ -s "$OUT2" ]] || { echo "ERROR: live adapter snapshot missing or empty: $OUT2"; exit 1; }

python3 - "$OUT2" <<'PY'
import json
import sys

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)
meta = data.get("adapter_meta") or {}
field_status = meta.get("field_status") if isinstance(meta, dict) else None
if not meta:
    print(f"ERROR: adapter_meta missing in {path}")
    sys.exit(1)
if not field_status:
    print(f"ERROR: adapter_meta.field_status missing in {path}")
    sys.exit(1)
PY

echo ">>> OK: snapshots written"
echo "    $OUT1 ($(wc -c < "$OUT1") bytes)"
echo "    $OUT2 ($(wc -c < "$OUT2") bytes)"
