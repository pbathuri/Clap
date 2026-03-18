#!/usr/bin/env bash
# M52.6 — Single canonical meeting launch (Vite + live + presenter + static fallback).
set -euo pipefail

INV="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$INV/.." && pwd)"

export EDGE_DESKTOP_REPO_ROOT="${EDGE_DESKTOP_REPO_ROOT:-$REPO}"

if [[ -f "$INV/.env.meeting" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$INV/.env.meeting"
  set +a
fi

export VITE_EDGE_LIVE="${VITE_EDGE_LIVE:-1}"
export VITE_PRESENTER_OVERLAY="${VITE_PRESENTER_OVERLAY:-1}"

if [[ -f "$INV/public/edge-desktop-snapshot.json" ]]; then
  export VITE_EDGE_STATIC_SNAPSHOT="${VITE_EDGE_STATIC_SNAPSHOT:-/edge-desktop-snapshot.json}"
else
  echo "WARN: No public/edge-desktop-snapshot.json — run: npm run demo:preflight"
fi

cd "$INV"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Edge Operator Desktop — MEETING LAUNCH"
echo "═══════════════════════════════════════════════════════════"
echo "  EDGE_DESKTOP_REPO_ROOT=$EDGE_DESKTOP_REPO_ROOT"
echo "  Static fallback: ${VITE_EDGE_STATIC_SNAPSHOT:-(none)}"
echo ""
echo "  When Vite is up, open ONE of:"
echo "    • First run / clean slate:"
echo "      http://localhost:5173/?live=1&presenter=1&resetDemo=1"
echo "    • Normal entry:"
echo "      http://localhost:5173/?live=1&presenter=1"
echo "═══════════════════════════════════════════════════════════"
echo ""
exec npm run dev
