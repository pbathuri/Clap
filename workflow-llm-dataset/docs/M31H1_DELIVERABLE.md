# M31H.1 — Routine Confirmation + Graph Review Inbox (Deliverable)

## 1. Files modified

| File | Changes |
|------|--------|
| `src/workflow_dataset/review_studio/models.py` | Added `ITEM_GRAPH_ROUTINE_CONFIRMATION`, `ITEM_GRAPH_PATTERN_REVIEW` and included them in `INTERVENTION_ITEM_KINDS`. |
| `src/workflow_dataset/review_studio/inbox.py` | Added `_items_from_graph_review(root)`; extended `build_inbox()` to include graph review items. |
| `src/workflow_dataset/personal/graph_store.py` | Added `graph_review` table (item_id, kind, payload, status, created_utc, updated_utc); added `save_graph_review_item`, `get_graph_review_item`, `list_graph_review_items`, `update_graph_review_status`. |
| `src/workflow_dataset/cli.py` | Added `personal review-inbox`, `personal suggest-review`, `personal routine` (accept \| reject \| edit), `personal pattern` (accept \| reject). |
| `src/workflow_dataset/mission_control/state.py` | Added `graph_review_pending_routines` and `graph_review_pending_patterns` to `personal_graph_summary`. |
| `src/workflow_dataset/mission_control/report.py` | Added graph_review pending line in `[Personal graph]` section. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/personal/graph_review_inbox.py` | Suggested routines/patterns for review; `suggest_routines_for_review`, `suggest_patterns_for_review`; `list_pending_routines`, `list_pending_patterns`; `accept_routine`, `reject_routine`, `edit_routine`; `accept_pattern`, `reject_pattern`; `build_graph_review_inbox_items` for review_studio. |
| `tests/test_graph_review_inbox.py` | Tests for graph_review store, accept/reject/edit routine, accept/reject pattern, build_graph_review_inbox_items. |
| `docs/M31H1_DELIVERABLE.md` | This deliverable. |

## 3. Sample suggested-routine item

**Stored in `graph_review` table (payload):**

```json
{
  "item_id": "gr_abc123",
  "kind": "routine_confirmation",
  "status": "pending",
  "payload": {
    "routine_id": "routine_xyz",
    "label": "User frequently works in project 'my_project'",
    "confidence": 0.65,
    "supporting_signals": ["project_touches=5"],
    "routine_type": "frequent_project",
    "project": "my_project"
  },
  "created_utc": "2025-03-16T14:00:00Z",
  "updated_utc": "2025-03-16T14:00:00Z"
}
```

**As intervention item (review_studio inbox):**

- `item_id`: `gr_abc123`
- `kind`: `graph_routine_confirmation`
- `summary`: `Routine: User frequently works in project 'my_project' (conf=0.65)`
- `entity_refs`: `{"routine_id": "routine_xyz", "item_id": "gr_abc123"}`
- `source_ref`: `routine_xyz`

## 4. Sample graph review flow

1. **Seed review queue**  
   `workflow-dataset personal suggest-review`  
   → Adds low-confidence routines and uncertain patterns into `graph_review` (pending).

2. **View inbox**  
   `workflow-dataset personal review-inbox`  
   → Lists pending routines and patterns.  
   Or use unified inbox: review_studio `build_inbox()` now includes these as `graph_routine_confirmation` / `graph_pattern_review` items.

3. **Routine: accept**  
   `workflow-dataset personal routine accept --item gr_abc123`  
   → Sets item status to `accepted`; sets `operator_confirmed` and `confirmed_at` on the corresponding graph node.

4. **Routine: reject**  
   `workflow-dataset personal routine reject --item gr_abc123`  
   → Sets item status to `rejected`.

5. **Routine: edit**  
   `workflow-dataset personal routine edit --item gr_abc123 --label "Weekly project sync"`  
   → Sets item status to `edited`, stores `edited_label` in payload, and updates the graph node’s `label` and `operator_edited`.

6. **Pattern: accept / reject**  
   `workflow-dataset personal pattern accept --item gr_pat_1`  
   `workflow-dataset personal pattern reject --item gr_pat_1`  
   → Marks pattern review item as accepted or rejected.

7. **Mission control**  
   State includes `graph_review_pending_routines` and `graph_review_pending_patterns`; report shows e.g. `graph_review: 2 routines, 1 patterns pending`.

## 5. Exact tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_graph_review_inbox.py -v
```

Tests: `test_save_and_get_graph_review_item`, `test_list_graph_review_items`, `test_update_graph_review_status`, `test_list_pending_routines_empty`, `test_accept_reject_routine`, `test_reject_routine`, `test_edit_routine`, `test_accept_reject_pattern`, `test_build_graph_review_inbox_items`.

## 6. Next recommended step for the pane

- **Review studio / trust surfaces**: In the UI that renders the unified inbox (review_studio), add explicit handling for `graph_routine_confirmation` and `graph_pattern_review`: show “Routine” / “Pattern” badges, and actions “Accept”, “Reject”, “Edit” (routine only) that call the same logic as the CLI (`accept_routine`, `reject_routine`, `edit_routine`, `accept_pattern`, `reject_pattern`).
- **Trust cockpit**: Optionally add a small “Graph review” block (e.g. pending count and link to “Review” or to the inbox filtered by graph kinds) so operators see graph review alongside other trust/review items.
- **Periodic suggest-review**: Run `personal suggest-review` after `personal graph ingest` or on a schedule so new low-confidence routines and uncertain patterns are continuously added to the inbox for confirmation.
