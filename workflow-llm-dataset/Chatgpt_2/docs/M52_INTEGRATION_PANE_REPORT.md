# M52 — Integration Pane Report (Shell + Mission Control + Live Adapter)

**Role:** Integrate Pane 1 (M52A–D), Pane 2 (M52E–H), and Pane 3 (M52I–L) **safely** in that order.

**Repo reality:** This branch may not expose three separate remote branches named per pane. Treat integration as **logical layering**: base shell → workspace meaning → live/presenter adapter. When merging parallel branches, use the same order.

---

## 1. Merge steps executed (prescribed order)

| Step | Pane | Scope | Intent |
|------|------|-------|--------|
| **M1** | Pane 1 | `investor-prototype` shell: `ShellLayout`, `TopBar`, dock, boot/role flow, motion tokens, transitions | Establishes premium chrome and phase machine (`boot` → `role` → `mission`) without binding to live data. |
| **M2** | Pane 2 | Mission surfaces: `CentralWorkspace`, `MultiWindowDesktop`, `mapSnapshotToMission`, mock + narrative-shaped panels | Fills shell with investor-safe copy and role/memory/demo semantics. |
| **M3** | Pane 3 | `edge_desktop/fetchers.py`, `live_desktop_adapter/*`, CLI `demo live-adapter-snapshot` / `live-desktop-prefetch`, `DemoFlowContext` live path, `adapter_meta` typing | Connects mission UI to shaped JSON; preserves mock/cached fallback. |

**Operational merge (git):** Merge Pane 1 branch into integration base → resolve → test. Repeat with Pane 2, then Pane 3. Never merge Pane 3 before Pane 2 if both touch `DemoFlowContext` or snapshot mapping—Pane 2 owns mission **shape**; Pane 3 owns **hydration**.

---

## 2. Files with conflicts (expected hotspots)

| Area | Typical conflicting files |
|------|---------------------------|
| Shell vs workspace | `DemoFlowContext.tsx`, `MissionControlScreen.tsx`, `App.tsx`, `TopBar.tsx` |
| Layout | `ShellLayout.tsx`, `CentralWorkspace.tsx`, `MultiWindowDesktop.tsx`, `DesktopDock.tsx` |
| Data contract | `edgeDesktopTypes.ts`, `mapSnapshotToMission.ts`, `loadEdgeDesktopState.ts` |
| Backend demo | `cli.py` (demo / investor-demo blocks), `investor_demo/*`, `edge_desktop/*` |
| Docs | `M52_*.md`, `investor-prototype/README.md` |

---

## 3. How each conflict should be resolved

| Principle | Resolution |
|-----------|------------|
| **Additive modular UI** | Keep Pane 1 layout components; Pane 2 injects content via props/slots; Pane 3 adds optional live fetch + `adapter_meta`—do not replace shell with raw tables or CLI dumps. |
| **Single source for flow** | `DemoFlowContext`: merge by **extending** context (e.g. `edgeAdapterMeta`, refresh) rather than duplicating phase state. |
| **Snapshot shape** | Prefer **widening** `EdgeDesktopSnapshot` + `mapSnapshotToMission` with optional fields; avoid breaking mock-only paths. |
| **CLI** | Append demo commands in dedicated sections; avoid reordering unrelated command groups in massive conflict—take both sides and sort locally. |
| **Presenter / cache** | Pane 3 wins on timeout, cache merge, and `presenter_fast_path`; Pane 2 wins on **what** panels show when data is missing (mock narrative). |
| **Privacy / approval** | Do not merge changes that expose internal engineering UIs or bypass simulate/approval language in investor copy. |

---

## 4. Tests run after each merge (recommended matrix)

### After Pane 1 (shell)

```bash
cd workflow-llm-dataset/investor-prototype && npm test -- --run
```

Validates: shell transitions, presenter phase order, motion tokens.

### After Pane 2 (mission workspace)

```bash
cd workflow-llm-dataset/investor-prototype && npm test -- --run
python3 -m pytest tests/test_investor_mission_control_m52h1.py -q   # if present; may be slower
python3 -m pytest tests/test_investor_demo.py tests/test_investor_demo_presenter_m51l1.py -q
```

Validates: mission-control narrative, presenter mode store.

### After Pane 3 (live adapter)

```bash
python3 -m pytest tests/test_live_desktop_adapter.py -q -k "not prefetch"
# Optional integration prefetch (slow):
# python3 -m pytest tests/test_live_desktop_adapter.py::test_prefetch_populates_cache -q
```

**Integration validation (manual / smoke):**

| Check | How |
|-------|-----|
| Boot → role → mission | Default flow in prototype; `?skipBoot=1&phase=mission&live=1` for shortcut |
| Role switching | Top bar “Switch role” |
| Single vs multi | Dock / layout toggle per shell state |
| Live shaping | `?live=1` + Vite proxy or static snapshot; Top bar shows Live / Cached / Demo |
| Fallback | Stop API → expect mock or static file per `loadEdgeDesktopState` |
| Presenter-safe | `investor-demo presenter-mode --on` + `demo live-adapter-snapshot --presenter-fast` |

**Latest run on integration pane pass (subset):**

- `investor-prototype`: **Vitest** — 2 files, **13 tests passed** (`motionTokens`, `shell/transitions`).
- `tests/test_live_desktop_adapter.py` — **4 passed**, 1 deselected (`-k 'not prefetch'`).

---

## 5. Final integrated desktop demo command / surface

1. **Prefetch cache (before room):**  
   `workflow-dataset demo live-desktop-prefetch --timeout 30`  
   → writes `data/local/live_desktop/last_good_snapshot.json`

2. **Presenter + session (CLI narrative):**  
   `workflow-dataset investor-demo presenter-mode --on`  
   `workflow-dataset investor-demo session start --presenter`  
   `workflow-dataset investor-demo cue`

3. **Browser prototype:**  
   `cd investor-prototype && npm run dev`  
   - Mock: default URL.  
   - Live-shaped: `?live=1` (and `VITE_EDGE_LIVE=1` if configured) + `/api/edge-desktop-snapshot` or `VITE_EDGE_STATIC_SNAPSHOT` pointing at prefetched JSON.

4. **One-shot adapter JSON:**  
   `workflow-dataset demo live-adapter-snapshot --presenter-fast -o /tmp/snap.json`

---

## 6. Remaining risks before investor use

| Risk | Mitigation |
|------|------------|
| Live snapshot latency / timeout | Prefetch + `--presenter-fast` + static snapshot path |
| Partial `adapter_meta` (stale_cache) | Narrate “mixed freshness”; UI chip/tooltip if implemented |
| API absent in browser dev | Rely on static file or mock—rehearse both |
| Mission-control Python tests slow/heavy | Run narrowed pytest in CI; full suite pre-release |
| Branch drift | Re-run this merge order if panes rebase independently |

---

## 7. Exact recommendation for rehearsal and polishing

1. **T−24h:** `demo live-desktop-prefetch`; copy snapshot into prototype `public/` if using static path.  
2. **T−1h:** `presenter-mode --on`; run `demo live-adapter-snapshot --presenter-fast` once to verify field_status counts on stderr.  
3. **Rehearsal script:** Walk boot → role → mission once in **mock**, once in **live/static**; toggle multi-window; switch roles; trigger refresh and confirm fallback label.  
4. **Polish:** Align Top bar / degraded copy with `adapter_meta`; keep approval-gated language in mission panels; avoid new surfaces—tighten motion and timing only.

---

*Generated for M52 integration pane — logical merge order and validation; adjust file lists if your pane branches differ.*
