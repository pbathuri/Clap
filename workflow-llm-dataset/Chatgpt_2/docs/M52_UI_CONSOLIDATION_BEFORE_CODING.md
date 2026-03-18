# M52 UI Consolidation — Before Coding (Integration-First Pane)

## 1. Integration inventory

| Layer | Primary files | Responsibility |
|-------|---------------|----------------|
| Shell | `shell/models.ts`, `transitions.ts`, `BootScreen`, `RoleScreen`, `TopBar`, `DesktopDock`, `LeftRail` | Phase machine, layout, chrome |
| Mission workspace | `ShellLayout`, `CentralWorkspace`, `RightMissionPanel`, `MultiWindowDesktop`, `GlassSurface` | Content rails, side status |
| Mock data | `mocks/missionMock.ts` | `ROLE_OPTIONS`, `MissionSurfaceState`, per-role defaults |
| Live adapter | `mapSnapshotToMission.ts`, `loadEdgeDesktopState.ts`, `edgeDesktopTypes.ts` | Snapshot → mission merge |
| Context | `DemoFlowContext.tsx` | Phase, shell, mission resolution, edge fetch |

## 2. Duplication map

| Issue | Locations | Consolidation |
|-------|-----------|----------------|
| Role / memory / trust / first-value copy | `MissionSurfaceState` + `RightMissionPanel` + `CentralWorkspace` (split by rail) | Single **view model** builder; panels read same shape |
| Snapshot→UI mapping | Only `mapSnapshotToMission` — but context recomputes mission without provenance | **One builder** returns mission + `dataProvenance` + degraded meta |
| Presenter flow | `PRESENTER_PHASE_ORDER` (boot/role/mission) vs CLI narrative stages | **Walkthrough steps** (4 + free) aligned with investor script; overlay documents both |
| Dock vs rail | Dock maps to rail ids (duplicate nav concept) | Keep both; **document** dock as shortcuts to same rail sections |
| Live vs mock path | Context branches `edgeLiveEnabled` / loading / null snapshot | **Single `buildDesktopDemoViewModel(snapshot, role, mock, source)`** |

## 3. File plan

| Action | Path |
|--------|------|
| Create | `docs/M52_UI_CONSOLIDATION_BEFORE_CODING.md` (this) |
| Create | `docs/M52_UI_CONSOLIDATION_DELIVERABLE.md` |
| Create | `investor-prototype/src/viewModels/desktopDemoViewModel.ts` |
| Create | `investor-prototype/src/demo/missionWalkthrough.ts` |
| Create | `investor-prototype/src/components/shell/InvestorWalkthrough.tsx` |
| Create | `investor-prototype/src/components/shell/PresenterDemoOverlay.tsx` |
| Create | `investor-prototype/tests/viewModels/desktopDemoViewModel.test.ts` |
| Create | `investor-prototype/tests/demo/missionWalkthrough.test.ts` |
| Modify | `mapSnapshotToMission.ts` → delegate to view model |
| Modify | `DemoFlowContext.tsx` → view model, walkthrough step, snapshot retention |
| Modify | `MissionControlScreen.tsx` → walkthrough + overlay |
| Modify | `TopBar.tsx` → degraded / provenance strip |
| Modify | `App.tsx` | optional overlay mount |
| Modify | `global.css` → walkthrough + overlay tokens |

## 4. Safety / risk note

- Walkthrough is **additive**; `?freeMission=1` preserves power-user / rehearsal skip.
- No new backend; no raw CLI in UI.
- Mock path unchanged when `live` off or API missing.
- Role count unchanged (3).

## 5. What this block will NOT do

- New roles, new backend subsystems, broad visual redesign.
- Remove mock fallback or dock/rail.
- Replace MultiWindowDesktop internals.
