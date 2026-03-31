# Investor Path vs Product Path (Repo-Grounded)

## Investor path (current)
**Primary surfaces:**
- Browser-based Edge Operator Desktop (`investor-prototype/`)
- Presenter overlay and walkthrough (`investor-prototype/src/components/shell/PresenterDemoOverlay.tsx`)
- Investor demo CLI (`src/workflow_dataset/investor_demo/*`)
- Preflight/prebake scripts (`investor-prototype/scripts/*`)

**Narrative stages:**
1. Boot / readiness
2. Role selection
3. Bounded onboarding / memory
4. Mission overview
5. First value
6. Supervised posture

**Live vs mock:**
The desktop UI supports live/cached/mock via `loadEdgeDesktopState.ts`; live data is available through `/api/edge-desktop-snapshot` in dev and via prebaked JSON in deploy.

## Product path (current)
**Core CLI/product surfaces:**
- Demo bootstrap/readiness/env-report (`demo_usb`)
- Demo onboarding (`demo_onboarding`)
- Workspace home (`workspace`)
- Day status (`workday`)
- Guidance next-action + operator summary (`quality_guidance`)
- Inbox list (`review_studio`)
- Trust / approvals / governance (`trust`, `supervised_loop`, `governance`)

**Operating stance:**
Local-first, approval-gated, session-trusted execution with explicit provenance.

## Convergence points (already real)
- **Edge desktop snapshot** aggregates real product surfaces (`edge_desktop/snapshot.py`).
- **Live adapter pipeline** provides per-field provenance (`live_desktop_adapter/*`).
- **Investor UI mapping** uses real snapshot fields when available (`desktopDemoViewModel.ts`).

## Drift risks (current)
- Boot readiness tiers are presentation-only in the UI.
- Dev API still defaults to the non-adapter snapshot unless the adapter flag is enabled.
- Static deploy does not include a live backend API.

## Principle
Investor mode should remain a polished slice of the product path, never an unrelated demo theater.
