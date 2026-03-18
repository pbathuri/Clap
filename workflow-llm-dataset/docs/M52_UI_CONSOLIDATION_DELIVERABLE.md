# M52 — UI Consolidation Deliverable (Integration-First Pane)

## 1. Files modified

| File | Change |
|------|--------|
| `investor-prototype/src/state/DemoFlowContext.tsx` | Single `buildDesktopDemoViewModel` pipeline; `demoViewModel`; mission walkthrough step; edge snapshot retention |
| `investor-prototype/src/adapters/mapSnapshotToMission.ts` | Delegates to view model; re-exports builder |
| `investor-prototype/src/components/MissionControlScreen.tsx` | `--shell-top` for degraded bar; `InvestorWalkthrough` |
| `investor-prototype/src/components/layout/TopBar.tsx` | `top-bar__row` + degraded strip |
| `investor-prototype/src/components/mission/MultiWindowDesktop.tsx` | Top offset when degraded |
| `investor-prototype/src/App.tsx` | `PresenterDemoOverlay` |
| `investor-prototype/src/styles/global.css` | Top bar layout, walkthrough, presenter overlay, `--shell-top` |

## 2. Files created

| File | Purpose |
|------|---------|
| `docs/M52_UI_CONSOLIDATION_BEFORE_CODING.md` | Inventory, duplication map, plan |
| `docs/M52_UI_CONSOLIDATION_DELIVERABLE.md` | This summary |
| `investor-prototype/src/viewModels/desktopDemoViewModel.ts` | **Single** snapshot→UI + provenance + degraded |
| `investor-prototype/src/demo/missionWalkthrough.ts` | Deterministic mission story steps |
| `investor-prototype/src/components/shell/InvestorWalkthrough.tsx` | 4-step investor path + Enter workspace |
| `investor-prototype/src/components/shell/PresenterDemoOverlay.tsx` | `?presenter=1` script cues |
| `investor-prototype/tests/viewModels/desktopDemoViewModel.test.ts` | View model + degraded |
| `investor-prototype/tests/demo/missionWalkthrough.test.ts` | Step machine |

## 3. Duplication removed / consolidated

- **Snapshot → panels:** All live/mock merge logic lives in `desktopDemoViewModel.ts` (was only in `mapSnapshotToMission`; context now uses the same builder for provenance).
- **Mission narrative:** One linear **walkthrough** (ready/memory → overview → first value → supervised) before free rail navigation; avoids expecting investors to discover rails cold.
- **Degraded / timeout:** One `degradedSummary` string + `staleFieldCount` from `adapter_meta.field_status`.

## 4. Final UI architecture

```
DemoFlowProvider
├── demoViewModel (source of truth for mission + provenance + degraded)
├── mission (= missionSurfaceOnly for legacy consumers)
├── missionWalkthroughStep 0–3 | 4 (free)
├── Desktop shell state (phase, rail, layout, dock)
└── Phases: boot → role_select → mission
    └── Mission: InvestorWalkthrough (steps 0–3) → full ShellLayout / MultiWindow
PresenterDemoOverlay (?presenter=1)
```

## 5. Final investor click path

1. **Boot** — Enter → readiness tier story  
2. **Role select** — One of three presets  
3. **Mission · Story 1** — Ready & memory  
4. **Mission · Story 2** — Role / context overview  
5. **Mission · Story 3** — First value  
6. **Mission · Story 4** — Supervised posture + next action  
7. **Enter workspace** (or **Continue** through step 4) → **Home / Work / Guidance / Inbox** rails + dock  

Shortcuts: `?freeMission=1` → skip story; `?walkthrough=2` → start at step 2 (debug).

## 6. Live / cached / mock flow

| Condition | `dataProvenance` | UI |
|-----------|------------------|-----|
| No `live=1` / no `VITE_EDGE_LIVE` | `mock` | Role mocks only |
| `live` + loading, no snapshot yet | `mock` + “Syncing…” | Mock + banner |
| API/static returns JSON | `live` / `cached` / `static_file` | Shaped merge + timeline |
| Timeout / empty API | `mock` + timeout copy | Last-good narrative from mocks |
| Partial `adapter_meta` | (unchanged source) | `degradedSummary` + optional stale count line |

## 7. Exact tests run

```bash
cd workflow-llm-dataset/investor-prototype && npm run build && npm test -- --run
```

**Result:** 16 tests passed (motion, shell transitions, desktopDemoViewModel ×3, missionWalkthrough ×4).

## 8. Remaining risks before rehearsal

- Walkthrough + dock overlap on short viewports (scroll inside sheet).  
- `presenter=1` overlay may cover refresh on small screens.  
- Live path still depends on API/static wiring outside this repo slice.  

## 9. Next hardening step

Run one **full dress** with `?live=1` + prefetched static JSON; narrate `degradedSummary` when it appears; trim copy if stale fields are common.
