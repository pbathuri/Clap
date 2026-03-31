# Shot 2 — Implementation Report

## Files created
- `investor-prototype/scripts/demo-dev-api-smoke.sh`
- `docs/SHOT2_IMPLEMENTATION_REPORT.md`

## Files modified
- `src/workflow_dataset/edge_desktop/snapshot.py`
- `src/workflow_dataset/live_desktop_adapter/pipeline.py`
- `investor-prototype/docs/DESKTOP_REHEARSAL_HARDENING.md`

## What was implemented
- **Hardening CLI smoke script** to validate `demo edge-desktop-snapshot` and `demo live-adapter-snapshot --presenter-fast`.
- **Edge desktop snapshot hardening**: switched `build_edge_desktop_snapshot` to use the live adapter pipeline with a bounded global budget, then add investor mission control home with a timeout.
- **Daemonized live adapter worker threads** to prevent hanging CLI processes after timeouts.
- **Hardening doc note** describing the new smoke check.

## Failures fixed
- `demo edge-desktop-snapshot` exceeded 60s and blocked the smoke script.
  - Fixed by using the bounded live adapter pipeline for snapshot aggregation.
- CLI smoke script failed because `rg` was not available in PATH.
  - Replaced checks with a Python JSON read.

## Tests run (exact outputs)
- `npm --prefix investor-prototype run test`
  - 8 files, 31 tests passed.
- `npm --prefix investor-prototype run build`
  - Vite build succeeded.
- `npm --prefix investor-prototype run demo:prebake`
  - Snapshot prebaked to `investor-prototype/public/edge-desktop-snapshot.json`.
- `./investor-prototype/scripts/demo-dev-api-smoke.sh`
  - Both snapshots produced; live adapter output contains `adapter_meta.field_status`.

## Remaining risks
- Dev API is not productionized; static deploy relies on prebaked JSON.
- Boot readiness tiers are still presentation-only.
- Live adapter pipeline can still return `stale_cache` under timeout pressure.
- Multiple doc trees (`docs/` vs `Chatgpt_2/docs/`) can drift.

## Recommended next step
**Investor rehearsal pass**: run the meeting playbook and scorecard once with live + fallback to validate narrative timing and top‑bar states.
