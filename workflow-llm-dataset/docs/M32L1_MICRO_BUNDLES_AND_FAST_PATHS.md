# M32L.1 — Micro-Assistance Bundles + Fast Review Paths

## 1. Files modified

- `src/workflow_dataset/action_cards/__init__.py` — Exported `UserMoment`, `MicroAssistanceBundle`, `FastReviewPath`, `GroupedCardFlow`.
- `src/workflow_dataset/action_cards/models.py` — Added `UserMoment` enum, `MicroAssistanceBundle`, `FastReviewPath`, `GroupedCardFlow` dataclasses with `to_dict`/`from_dict`.
- `src/workflow_dataset/cli.py` — Added commands: `action-cards bundles` (list | show | create | add-card | remove-card), `action-cards review-paths` (list | show | create | apply), `action-cards flows` (list | show | create | run).
- `tests/test_action_cards.py` — Added 5 tests for bundles, review paths, and flows.

## 2. Files created

- `src/workflow_dataset/action_cards/bundles.py` — load_all_bundles, load_bundle, save_bundle, list_bundles_by_moment, add_card_to_bundle, remove_card_from_bundle.
- `src/workflow_dataset/action_cards/review_paths.py` — load_all_review_paths, load_review_path, save_review_path, save_review_paths, apply_path.
- `src/workflow_dataset/action_cards/flows.py` — load_all_flows, load_flow, save_flow, get_flow_for_moment, run_flow.
- `docs/M32L1_MICRO_BUNDLES_AND_FAST_PATHS.md` — This doc (overview, CLI, samples, tests, next step).

## Overview

First-draft support for **reusable micro-assistance bundles**, **fast review paths** for common accepted cards, and **grouped card flows** for user moments: resume-work, blocked-review, end-of-day wrap, document handoff.

## Concepts

- **MicroAssistanceBundle**: Named group of action card ids for a user moment. Stored under `data/local/action_cards/bundles.json`. Reusable: add/remove cards, list by moment.
- **FastReviewPath**: Filter + sort + action (list_only | preview_first | execute_in_order | open_studio). Applied to cards (from store or from a bundle). Stored under `data/local/action_cards/review_paths.json`.
- **GroupedCardFlow**: Links a user moment to one optional bundle and one optional fast review path. Running a flow returns the ordered cards (path applied to bundle’s cards or all cards). Stored under `data/local/action_cards/flows.json`.
- **User moments**: `resume_work`, `blocked_review`, `end_of_day_wrap`, `document_handoff`.

## CLI

- **Bundles**: `action-cards bundles list [--moment M]` | `show --id <bundle_id>` | `create --name X --moment Y` | `add-card --id B --card-id C` | `remove-card --id B --card-id C`
- **Review paths**: `action-cards review-paths list [--moment M]` | `show --id <path_id>` | `create --name X --moment Y [--filter-state] [--action] [--limit]` | `apply --id <path_id>`
- **Flows**: `action-cards flows list` | `show --id <flow_id>` | `create --moment M --label L [--bundle-id] [--review-path-id]` | `run --moment M`

## Sample micro-assistance bundle

```json
{
  "bundle_id": "bundle_resume_work_001",
  "name": "Resume work — pending & accepted",
  "description": "Cards to quickly resume: current project, first pending task, any blocked item.",
  "moment_kind": "resume_work",
  "card_ids": ["card_focus_project", "card_first_pending", "card_blocked_review"],
  "created_utc": "2025-03-16T14:00:00Z",
  "updated_utc": "2025-03-16T14:00:00Z"
}
```

## Sample fast review path

```json
{
  "path_id": "path_blocked_review_001",
  "name": "Blocked items first",
  "description": "Show blocked and approval-required cards, newest first; then open studio.",
  "moment_kind": "blocked_review",
  "filter_state": "blocked",
  "filter_handoff_target": "",
  "filter_source_type": "",
  "sort_by": "updated_utc",
  "sort_order": "desc",
  "action": "open_studio",
  "limit": 10,
  "created_utc": "2025-03-16T14:00:00Z",
  "updated_utc": "2025-03-16T14:00:00Z"
}
```

## Sample grouped flow

```json
{
  "flow_id": "flow_resume_work_001",
  "moment_kind": "resume_work",
  "label": "Resume work",
  "bundle_id": "bundle_resume_work_001",
  "review_path_id": "path_resume_pending_001",
  "created_utc": "2025-03-16T14:00:00Z",
  "updated_utc": "2025-03-16T14:00:00Z"
}
```

Running `action-cards flows run --moment resume_work` loads this flow, resolves the bundle and path, applies the path to the bundle’s cards, and returns the ordered list (and in future UI can preview/execute in order).

## 5. Exact tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_action_cards.py -v
```

M32L.1 tests (5): `test_bundle_create_save_load`, `test_bundle_add_remove_card`, `test_fast_review_path_apply`, `test_flow_get_for_moment_and_run`, `test_run_flow_no_flow_for_moment`. All 16 tests in `test_action_cards.py` (11 existing + 5 M32L.1) should pass.

## 6. Next recommended step for this pane

- **Wire flows into mission control or assist UI**: Add a “suggested flow” or “run flow for moment” entry (e.g. in mission control report or a small assist panel) so operators can trigger `flows run --moment resume_work` or `blocked_review` from one click.
- **Implement path actions**: Today `apply_path` only returns ordered cards; `action` (preview_first, execute_in_order, open_studio) is stored but not executed. Implement “preview first N” and “open studio” as optional follow-ups after apply.
- **Seed default flows**: Add `action-cards seed-defaults` (or similar) that creates one bundle, one path, and one flow per moment so new repos have working examples.
