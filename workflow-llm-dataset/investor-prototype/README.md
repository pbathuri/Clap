# Investor demo prototype · Edge Operator Desktop (M52 shell)

## Meeting launch (M52.6 — use this in the room)

1. **`npm run demo:preflight`** (from `investor-prototype/`, venv active) — snapshot fallback  
2. **`npm run demo:launch`** — dev server + env  
3. Browser: **`http://localhost:5173/?live=1&presenter=1&resetDemo=1`** (first run)  

Full operator steps: **[demo/OPERATOR_MEETING_PLAYBOOK.md](./demo/OPERATOR_MEETING_PLAYBOOK.md)** · bundle index **[demo/README.md](./demo/README.md)** · validate **`npm run demo:validate`**

---

## M53 deploy (one-command dev / build / deploy)

```bash
# Dev
npm install && npm run dev

# Build
npm run build

# Prebake static snapshot for deploy
npm run demo:prebake
```

**Static hosting**

- **Vercel**: set project root to `investor-prototype/` and deploy (uses `vercel.json`).  
- **Netlify**: set base to `investor-prototype/`, build `npm run build`, publish `dist/` (uses `netlify.toml`).  
- **GitHub Actions**: workflow uploads `investor-prototype/dist` artifact.

**Env template:** copy `.env.example` and adjust for staging/prod.

**Presenter checklist (before the room)**

1. `npm run demo:preflight`  
2. `npm run demo:launch`  
3. Open `?live=1&presenter=1&resetDemo=1`  
4. Confirm top bar shows **Connected**, **Last sync**, or **Demo story** (all honest)  

---

**M52:** Three-region mission layout — **left rail** · **central AI workspace** · **right mission panel** — plus boot readiness tiers, dock, multi-window toggle. See `docs/M52_EDGE_OPERATOR_DESKTOP_SHELL.md`.

**Tests:** `npm run test` (shell transitions, motion tokens, **view model**, **mission walkthrough**).

**Consolidated demo (M52 UI integration):** After role select, a **4-step investor story** runs (ready/memory → overview → first value → supervised). **`?freeMission=1`** skips to full rails. **`?presenter=1`** shows presenter script overlay. See `docs/M52_UI_CONSOLIDATION_DELIVERABLE.md`.

Glass UI with **optional live wiring** to `workflow-dataset` CLI outputs.

## Run (mock only)

```bash
npm install && npm run dev
```

Open `/` — full story with **mock** mission data.

## Run with **live** product snapshot

1. From **`workflow-llm-dataset`** repo root (venv active, package importable):

   ```bash
   # Optional: refresh presenter cache file for instant load
   workflow-dataset demo edge-desktop-snapshot -o investor-prototype/public/edge-desktop-snapshot.json
   ```

2. From **`investor-prototype`**:

   ```bash
   export EDGE_DESKTOP_REPO_ROOT=/absolute/path/to/workflow-llm-dataset
   # optional: export EDGE_DESKTOP_PYTHON=/path/to/.venv/bin/python
   npm run dev
   ```

3. Open mission control with live fetch:

   **`http://localhost:5173/?phase=mission&live=1`**

   Or set in `.env`: `VITE_EDGE_LIVE=1`

### Data flow

| Source | When |
|--------|------|
| **Session cache** | **120s** default; **`?presenter=1`** → **45 min** (rehearsal) |
| **Prefetch timing** | Load begins on **role** screen; mission reuses data (no extra round-trip) |
| **Stale-while-revalidate** | Last session snapshot shows immediately while refresh runs |
| **`GET /api/edge-desktop-snapshot`** | Vite dev server runs Python `build_edge_desktop_snapshot` (~timeout 28s) |
| **`/edge-desktop-snapshot.json`** | If API fails: set `VITE_EDGE_STATIC_SNAPSHOT=/edge-desktop-snapshot.json` |
| **Mock** | No `live=1`, or timeout / API error |

**Optional live adapter path (dev API):**
- Set `EDGE_DESKTOP_USE_ADAPTER=1` (or `VITE_EDGE_USE_ADAPTER=1`) before `npm run dev`.
- The API returns `adapter_meta` with per-field provenance (`live`, `stale_cache`, `timeout`).

Top bar: **Connected · Last sync · Demo story · Connecting / Refreshing** — **Refresh** clears cache and refetches. See `docs/DESKTOP_REHEARSAL_HARDENING.md`.

## CLI: export snapshot only

```bash
cd workflow-llm-dataset
workflow-dataset demo edge-desktop-snapshot --repo-root .
workflow-dataset demo edge-desktop-snapshot -o /tmp/edge.json
```

Wired surfaces: **readiness**, **bootstrap_last**, **onboarding ready-state**, **workspace home** (+ text), **day status** (+ text), **guidance next-action**, **operator summary**, **inbox list**.

**M52.5 rehearsal:** Canonical 5-min / 2-min paths → `docs/INVESTOR_DEMO_CANONICAL_PATH.md` · scorecard → `docs/REHEARSAL_SCORECARD.md` · **`?resetDemo=1`** cold reset · **Reset demo** (top bar, with **`?presenter=1`**).
