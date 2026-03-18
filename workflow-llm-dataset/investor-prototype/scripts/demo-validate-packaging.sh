#!/usr/bin/env bash
# M52.6 — Packaging smoke check (CI or pre-flight).
set -euo pipefail
INV="$(cd "$(dirname "$0")/.." && pwd)"
cd "$INV"

echo ">>> npm run test"
npm run test

echo ">>> npm run build"
npm run build

if [[ -f public/edge-desktop-snapshot.json ]]; then
  echo ">>> OK: edge-desktop-snapshot.json present ($(wc -c < public/edge-desktop-snapshot.json) bytes)"
else
  echo ">>> WARN: public/edge-desktop-snapshot.json missing — run npm run demo:preflight before the room"
fi

for f in demo/OPERATOR_MEETING_PLAYBOOK.md scripts/demo-preflight.sh scripts/demo-prebake.sh scripts/demo-launch-meeting.sh .env.example vercel.json netlify.toml; do
  [[ -f "$f" ]] || { echo "ERROR: missing $f"; exit 1; }
done
echo ">>> Packaging validation OK"
