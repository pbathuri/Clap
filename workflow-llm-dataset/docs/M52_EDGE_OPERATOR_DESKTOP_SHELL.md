# M52A–M52D — Edge Operator Desktop Shell

## Before coding (baseline)

### 1. Presentation / UI / shell surfaces already in repo

| Surface | Location |
|---------|----------|
| **Investor prototype (React)** | `investor-prototype/` — boot, role select, mission grid, multi-window, dock, top bar, live edge adapter |
| **CLI demo path** | `demo bootstrap/readiness`, `demo onboarding/*`, `workspace`, `day`, `guidance`, `inbox`, `investor-demo/*` |
| **Aggregated JSON for UI** | `workflow_dataset/edge_desktop/snapshot.py` + `demo edge-desktop-snapshot` |
| **Docs** | M51 integration pane, M51H.1 user presets, rehearsal scripts |

### 2. What can be reused

- Existing **glass CSS**, **TopBar**, **Dock**, **multi-window** layer.
- **DemoFlowContext** phase machine, **missionMock** / **mapSnapshotToMission**.
- **edge-desktop-snapshot** as future data spine (no change required for M52 shell).

### 3. What was missing for a premium desktop shell

- Explicit **shell state models** (not only implicit context fields).
- **Three-region mission layout**: left rail + central AI workspace + right mission strip.
- **Boot → readiness framing** aligned with USB story (visual tier, not only progress bar).
- **Presenter-oriented navigation** (rail sections, deterministic clicks).
- **Tests + doc** for transitions.

### 4. File plan (M52)

| Action | Path |
|--------|------|
| Create | `investor-prototype/src/shell/models.ts` |
| Create | `investor-prototype/src/shell/transitions.ts` |
| Create | `investor-prototype/src/components/shell/ShellLayout.tsx` |
| Create | `investor-prototype/src/components/shell/LeftRail.tsx` |
| Create | `investor-prototype/src/components/shell/CentralWorkspace.tsx` |
| Create | `investor-prototype/src/components/shell/RightMissionPanel.tsx` |
| Modify | `DemoFlowContext.tsx` — rail, right panel, boot readiness tier |
| Modify | `BootScreen.tsx` — readiness visual |
| Modify | `MissionControlScreen.tsx` — ShellLayout vs multi |
| Modify | `SingleWorkspace.tsx` — slim to legacy or remove from mission path |
| Create | `tests/shell/transitions.test.ts` |
| Create | This doc |

### 5. Safety / risk

- **No Python / CLI behavior change** in M52 shell work; prototype-only TS/React.
- **Risk:** layout refactor regressions — mitigated by keeping multi-window path separate.
- **Risk:** over-stuffing center column — constrained to four rail views + right panel.

### 6. Shell design principles

1. **OS feel** — chrome (bar, rail, dock) frames a single coherent workspace.
2. **Investor language** — no raw IDs, no debug tables as default.
3. **Calm motion** — soft transitions, one focal column.
4. **Modular data** — `MissionSurfaceState` + future live snapshot unchanged at boundaries.
5. **Deterministic clicks** — same path every rehearsal.

### 7. What M52 does NOT do

- No new product features or CLI commands.
- No mandatory live backend wiring.
- No admin dashboard expansion.
- No replacement of mission_control Python surfaces.

---

## Implementation summary

See repo `investor-prototype/` for components under `src/components/shell/` and `src/shell/`.

**Tests:** `npm run test` in `investor-prototype` — shell transition helpers.

**Next live step:** Hydrate `MissionSurfaceState` + `bootReadinessTier` from `demo edge-desktop-snapshot` / readiness JSON (already partially wired via `?live=1`).

---

## Final deliverable (M52)

### Files created

| File |
|------|
| `investor-prototype/src/shell/models.ts` |
| `investor-prototype/src/shell/transitions.ts` |
| `investor-prototype/src/components/shell/ShellLayout.tsx` |
| `investor-prototype/src/components/shell/LeftRail.tsx` |
| `investor-prototype/src/components/shell/CentralWorkspace.tsx` |
| `investor-prototype/src/components/shell/RightMissionPanel.tsx` |
| `investor-prototype/tests/shell/transitions.test.ts` |
| `investor-prototype/vitest.config.ts` |
| `docs/M52_EDGE_OPERATOR_DESKTOP_SHELL.md` |

### Files modified

| File |
|------|
| `investor-prototype/src/state/DemoFlowContext.tsx` — `desktopShell`, rail, right panel, boot tier |
| `investor-prototype/src/components/BootScreen.tsx` — readiness tiers + caption |
| `investor-prototype/src/components/MissionControlScreen.tsx` — three-column shell |
| `investor-prototype/src/components/layout/TopBar.tsx` — context hint |
| `investor-prototype/src/styles/global.css` — shell layout CSS |
| `investor-prototype/package.json` — `npm test` |

### Removed

- `SingleWorkspace.tsx` (replaced by rail + center + right panel)

### Component structure

```
App → DemoFlowProvider → DemoRouter
  BootScreen
  RoleScreen
  MissionControlScreen
    TopBar
    .shell-body → LeftRail | CentralWorkspace | RightMissionPanel
    DesktopDock
  MultiWindowDesktop (layout toggle)
```

### Click path

1. **Boot** → optional **Full / Degraded / Workspace** tier → **Continue** or **Skip** → **Role select**  
2. **Role** → card → **Mission** (rail **Home**, right mission panel open)  
3. **Rail** → Work · Guidance · Inbox (center only changes)  
4. **Dock** → layout **Single ↔ Multi**  
5. **Top bar** → Switch role · Reboot · Live refresh (if `?live=1`)

### Single vs multi-window

- **Single:** CSS grid rail + scrollable center + collapsible right mission strip.  
- **Multi:** Full-area floating windows (unchanged); dock toggles mode.

### Mocked today

- Boot tier selection (presenter story; wire to `demo readiness` JSON).  
- Mission copy via `missionMock` per role; optional live merge via existing edge adapter.

### Next integration step

Map `readiness.capability_level` + `degraded_mode` → `setBootReadinessTier` on boot when `?live=1`; keep shell models as the single place for layout + presenter phase.
