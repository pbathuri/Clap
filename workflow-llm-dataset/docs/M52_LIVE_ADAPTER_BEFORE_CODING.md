# M52I–M52L — Live Data Adapter + Presenter Mode: Before Coding

## 1. What live outputs should be wired first

| Priority | Output | Already wired | Notes |
|----------|--------|---------------|-------|
| P0 | Demo readiness | `build_readiness_report` in `edge_desktop/snapshot.py` | Fast; investor-safe headline. |
| P0 | Onboarding ready-state | `build_ready_to_assist_state` + completion | Core demo narrative. |
| P0 | Workspace home (dict) | `build_workspace_home_snapshot` | Structured; avoid blocking on full text. |
| P1 | Day status (dict) | `build_daily_operating_surface` | Workday surface. |
| P1 | Guidance next-action | `next_best_action_guidance` | Shaped dict. |
| P1 | Operator summary | `build_operator_summary` | May be heavier. |
| P2 | Inbox | `build_inbox` limit 25 | Bounded. |
| P2 | workspace_home_text / day_status_text | CLI string builders | **Slower** — optional / lower timeout in fast path. |

## 2. Safe vs risky for live demo

- **Safe**: Readiness dict, onboarding ready dict, workspace home dict, guidance dict (when they complete), inbox with low limit.
- **Risky / slow**: `cmd_home` / `cmd_day_status` full text formatting; full mission-control aggregation; any unbounded scan.
- **Presenter**: Prefer dict snapshots over text; merge last-good cache for timed-out fields; never block UI on slow path.

## 3. Exact file plan

| Path | Purpose |
|------|---------|
| `docs/M52_LIVE_ADAPTER_BEFORE_CODING.md` | This document. |
| `src/workflow_dataset/edge_desktop/fetchers.py` | Isolated fetch per source (return partial). |
| `src/workflow_dataset/live_desktop_adapter/models.py` | Adapter meta, refresh policy, per-field status. |
| `src/workflow_dataset/live_desktop_adapter/cache.py` | Last-good JSON cache under `data/local/live_desktop/`. |
| `src/workflow_dataset/live_desktop_adapter/pipeline.py` | Timed parallel fetch, merge cache, presenter flags. |
| `src/workflow_dataset/cli.py` | `demo live-adapter-snapshot`, `demo live-desktop-prefetch`. |
| `investor-prototype/src/adapters/edgeDesktopTypes.ts` | Optional `adapter_meta` on snapshot. |
| `tests/test_live_desktop_adapter.py` | Timeout merge, presenter, cache roundtrip. |
| `docs/M52_LIVE_ADAPTER_DELIVERABLE.md` | Final output. |

## 4. Safety/risk note

- Per-source timeouts prevent one slow subsystem from stalling the whole snapshot.
- Cache merge must label fields as **stale** / **from_cache** so the UI stays honest.
- Presenter mode does not fabricate data — it prefers prefetch cache and shorter live windows for volatile fields only where documented.
- Raw CLI text surfaces remain optional and deprioritized under tight budgets.

## 5. Adapter-layer principles

- **Shaped first**: Same JSON contract as `EdgeDesktopSnapshot`; enrich with `adapter_meta`, not raw terminals.
- **Degraded honesty**: `errors` + `adapter_meta.field_status` explain timeout vs live vs cache.
- **Premium UI unchanged**: Prototype merges snapshot + mock as today; adapter improves fill-rate and predictability.
- **Deterministic presenter**: Prefetch writes known-good file; presenter flow can load static file.

## 6. What this block will NOT do

- Full frontend rewrite or remove mock fallback.
- Remove simulation safety net.
- Broad generic integration framework.
- Unbounded subprocess or mission-control full state in this snapshot path.
