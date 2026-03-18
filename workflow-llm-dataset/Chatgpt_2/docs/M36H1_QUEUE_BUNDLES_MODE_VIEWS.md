# M36H.1 — Queue Bundles + Mode-Aware Queue Views

First-draft support for bundled queue views by mode, queue sections by project/episode, and stronger queue summaries for overloaded states. Extends the M36E–M36H unified work queue (no rebuild).

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `queue_group` and commands: `queue list`, `queue view --mode focus\|review\|operator\|wrap-up`, `queue summary` (with `--threshold`, `--json`). |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/unified_queue/__init__.py` | Package exports: models, collect, prioritize, views, summary. |
| `src/workflow_dataset/unified_queue/prioritize.py` | `rank_unified_queue`, `build_sections_by_project`, `build_sections_by_episode`; assigns `section_id` and `mode_tags`. |
| `src/workflow_dataset/unified_queue/views.py` | `build_mode_view`, `build_mode_aware_view_bundle` (focus, review, operator, wrap-up). |
| `src/workflow_dataset/unified_queue/summary.py` | `build_queue_summary` with overload threshold, by_section, by_mode, overflow_message, suggested_action. |
| `tests/test_unified_queue.py` | Tests for models, rank, sections by project/episode, mode view, overloaded summary. |
| `docs/samples/M36H1_sample_mode_aware_queue_view.json` | Sample mode-aware queue view (focus, by project). |
| `docs/samples/M36H1_sample_overloaded_queue_summary.json` | Sample overloaded-queue summary. |
| `docs/M36H1_QUEUE_BUNDLES_MODE_VIEWS.md` | This deliverable doc. |

Existing (from prior M36E–M36H work): `unified_queue/models.py`, `unified_queue/collect.py`.

## 3. Sample mode-aware queue view

See `docs/samples/M36H1_sample_mode_aware_queue_view.json`. Example:

```json
{
  "mode": "focus",
  "label": "Focus mode",
  "description": "Items suited for current project / focus.",
  "item_ids": ["uq_rs_a1", "uq_rs_a2", "uq_auto_b1"],
  "sections": [
    { "section_id": "project_founder_case_alpha", "label": "founder_case_alpha", "count": 2, "item_ids": ["uq_rs_a1", "uq_rs_a2"] },
    { "section_id": "project_", "label": "No project", "count": 1, "item_ids": ["uq_auto_b1"] }
  ],
  "total_count": 3,
  "generated_at_utc": "2025-03-16T12:00:00.000000+00:00"
}
```

CLI: `queue view --mode focus --by-project` or `queue view --mode review --json`.

## 4. Sample overloaded-queue summary

See `docs/samples/M36H1_sample_overloaded_queue_summary.json`. Example:

```json
{
  "total_count": 28,
  "is_overloaded": true,
  "overload_threshold": 20,
  "by_section": { "review_ready": 15, "approval": 6, "blocked": 4, "automation": 3 },
  "by_mode": { "review_ready": 22, "focus_ready": 10, "operator_ready": 7, "wrap_up": 5 },
  "top_blocked_item_id": "uq_auto_blocked_1",
  "top_blocked_summary": "Automation run failed: timeout; requires operator review.",
  "overflow_message": "Queue has 28 items (over threshold 20). Consider using a mode view to narrow: queue view --mode focus | review | operator | wrap-up.",
  "suggested_action": "queue view --mode focus  # or review | operator | wrap-up"
}
```

CLI: `queue summary` or `queue summary --threshold 20 --json`.

## 5. Exact tests run

```bash
cd /Users/prady/Desktop/Clap/workflow-llm-dataset
python -m pytest tests/test_unified_queue.py -v
```

## 6. Next recommended step for the pane

- **Route/explain**: Add `unified_queue/route.py` (accept_item, defer_item, dismiss_item, escalate_item, route_item) and `unified_queue/explain.py` (explain_item) that resolve unified item_id to source subsystem and call existing automation_inbox/review_studio flows.
- **Mission control**: Add unified queue state and a “[Unified queue]” section in `mission_control/state.py` and `report.py` (count, overload flag, suggested view).
- **Store**: Optional persistence for deferrals/dismissals under `data/local/unified_queue/`.
- **CLI**: Add `queue explain --id <item_id>`, `queue accept`, `queue defer`, `queue dismiss`, `queue route` once route/explain exist.
