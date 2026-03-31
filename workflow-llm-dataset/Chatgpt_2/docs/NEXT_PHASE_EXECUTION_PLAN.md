# Next Phase Execution Plan (Shot 1)

## Chosen step
**Post‑build hardening pass for the Edge Operator Desktop integration.**

Goal: produce a deterministic validation path for live/cached/mock wiring without expanding architecture or UI.

## Scope
- Add a single **hardening script** to validate:
  - CLI snapshot (`demo edge-desktop-snapshot`)
  - Live adapter snapshot (`demo live-adapter-snapshot --presenter-fast`)
  - Investor prototype build/test and prebake (if feasible)
- Document exact outputs and failures in `docs/SHOT2_IMPLEMENTATION_REPORT.md`.

## Target files
**Create**
- `investor-prototype/scripts/demo-dev-api-smoke.sh` (or similarly named hardening script)
- `docs/SHOT2_IMPLEMENTATION_REPORT.md`

**Update**
- `investor-prototype/README.md` or `docs/DESKTOP_REHEARSAL_HARDENING.md` (brief mention of new hardening script)

## Acceptance criteria
1. `workflow-dataset demo edge-desktop-snapshot` produces valid JSON (non‑empty).
2. `workflow-dataset demo live-adapter-snapshot --presenter-fast` produces JSON containing `adapter_meta.field_status`.
3. Hardening script exits non‑zero on missing command or invalid output.
4. `docs/SHOT2_IMPLEMENTATION_REPORT.md` captures exact command outputs + failures fixed.

## Test plan
Minimum:
- Run the new hardening script once.
- If available, run:
  - `npm --prefix investor-prototype run test`
  - `npm --prefix investor-prototype run build`
  - `npm --prefix investor-prototype run demo:prebake`

## Out of scope
- UI redesign or new components.
- New backend services for production API.
- New runtime subsystems.
