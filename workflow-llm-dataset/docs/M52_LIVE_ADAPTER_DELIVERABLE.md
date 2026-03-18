# M52I–M52L — Live Data Adapter + Presenter Mode: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `pyproject.toml` | Registered `integration` pytest marker. |
| `tests/test_live_desktop_adapter.py` | Presenter test patches `edge_desktop.fetchers.FETCHERS` (correct import site). |

## 2. Files created (this milestone)

| File | Purpose |
|------|---------|
| `docs/M52_LIVE_ADAPTER_BEFORE_CODING.md` | Pre-build analysis. |
| `docs/M52_LIVE_ADAPTER_DELIVERABLE.md` | This checklist. |
| `src/workflow_dataset/edge_desktop/fetchers.py` | Per-source shaped fetchers + `FETCHERS` list (`presenter_ok` flags). |
| `src/workflow_dataset/live_desktop_adapter/__init__.py` | Package. |
| `src/workflow_dataset/live_desktop_adapter/models.py` | `RefreshPolicy`, `AdapterMeta`, field provenance. |
| `src/workflow_dataset/live_desktop_adapter/cache.py` | `data/local/live_desktop/last_good_snapshot.json`. |
| `src/workflow_dataset/live_desktop_adapter/pipeline.py` | Parallel bounded wait, cache merge, presenter fast path. |
| `investor-prototype/src/adapters/edgeDesktopTypes.ts` | Optional `adapter_meta` on snapshot type. |

CLI hooks live in existing `src/workflow_dataset/cli.py` (`demo live-adapter-snapshot`, `demo live-desktop-prefetch`).

## 3. Live outputs wired

Via `FETCHERS` → shaped patches merged into one snapshot:

- Readiness / bootstrap last
- Onboarding ready-state
- Workspace home (dict) + optional `workspace_home_text`
- Day status (dict) + optional `day_status_text`
- Guidance next-action
- Operator summary
- Inbox (bounded)

## 4. Fallback / caching behavior

- **`merge_last_good_cache`**: On error, timeout, or skipped slow path, fields pull from `last_good_snapshot.json` when present; `adapter_meta.field_status` marks `stale_cache` vs `live` vs `timeout` vs `skipped_slow_path`.
- **Global wall clock**: `wait(..., timeout=global_budget)`; pending futures cancelled; executor `shutdown(wait=False, cancel_futures=True)`.
- **`RefreshPolicy.max_parallel_wait_seconds`**: Caps wait for tests / tight demos.
- **`demo live-desktop-prefetch`**: High-timeout full run + write cache for investor walkthrough.

## 5. Presenter mode behavior

- If `data/local/investor_demo/presenter_mode.json` has `enabled: true` **and** `RefreshPolicy.presenter_fast_path` is true (default when presenter on in pipeline path — see CLI flags), **slow text fetchers** (`presenter_ok=False`) are skipped; cache fills those slots if available.
- `adapter_meta.presenter_fast_path` and `presenter_mode_active` surface in JSON for UI honesty.

## 6. Remaining latency risks

- Fetchers that exceed `global_budget` still run in background threads until process exit (orphan work under load).
- Operator summary / heavy inbox paths may still be slow on large trees.
- Text formatters (`*_text`) remain the slowest; presenter path intentionally deprioritizes them.

## 7. Next hardening step before live investor use

1. Run **`workflow-dataset demo live-desktop-prefetch`** on the demo machine/repo copy before the session (warms `last_good_snapshot.json`).
2. During demo, prefer **`demo live-adapter-snapshot --presenter-fast`** (or presenter config + default policy) and a **15–25s** prefetch-backed cache so timeouts show **stale_cache** not empty panels.
3. Optionally serve the prefetch JSON to the investor prototype static path or a thin API so the browser never blocks on subprocess.
