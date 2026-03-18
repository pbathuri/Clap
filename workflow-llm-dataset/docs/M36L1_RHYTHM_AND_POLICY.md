# M36L.1 — Daily Rhythm Templates + Carry-Forward Policies

First-draft support for daily rhythm templates, carry-forward policies, and clearer next-day operating recommendations.

## Daily rhythm templates

Templates define a sequence of phases (e.g. morning check → inbox → deep work → review → wrap-up) with suggested duration and default first action per phase.

- **List:** `workflow-dataset continuity rhythm [--repo PATH] [--json]`
- **Show:** `workflow-dataset continuity rhythm-show [--template-id ID] [--repo PATH] [--json]`
- **Set active:** `workflow-dataset continuity rhythm-set-active <template_id> [--repo PATH]`

Data: `data/local/continuity_engine/rhythm_templates.json` (optional override), `active_rhythm_template_id.txt`.

### Sample daily rhythm template (JSON)

```json
{
  "template_id": "default",
  "name": "Default day",
  "description": "Morning check → inbox → deep work → review → wrap-up",
  "default_first_phase_id": "morning_check",
  "phases": [
    {
      "phase_id": "morning_check",
      "label": "Morning check",
      "suggested_duration_min": 15,
      "default_first_action_command": "workflow-dataset continuity morning",
      "order": 0
    },
    {
      "phase_id": "inbox_review",
      "label": "Inbox & approvals",
      "suggested_duration_min": 20,
      "default_first_action_command": "workflow-dataset inbox list",
      "order": 1
    },
    {
      "phase_id": "deep_work",
      "label": "Deep work",
      "suggested_duration_min": 90,
      "default_first_action_command": "workflow-dataset workspace open",
      "order": 2
    },
    {
      "phase_id": "review",
      "label": "Review & queue",
      "suggested_duration_min": 30,
      "default_first_action_command": "workflow-dataset queue view",
      "order": 3
    },
    {
      "phase_id": "wrap_up",
      "label": "Wrap-up",
      "suggested_duration_min": 15,
      "default_first_action_command": "workflow-dataset continuity shutdown",
      "order": 4
    }
  ]
}
```

## Carry-forward policy

Items are classified into:

- **Urgent** — approvals/blocked that should be addressed first (e.g. approval_queue + high/urgent, blocked runs).
- **Optional** — normal queue items carried forward.
- **Automated follow-up** — automation inbox follow-ups that can be batched or deferred.

Shutdown flow applies the policy when building carry-forward; the result is persisted and used for next-day recommendation.

- **Show policy for current queue:** `workflow-dataset continuity carry-forward-policy [--repo PATH] [--json]`
- **List carry-forward (with class):** `workflow-dataset continuity carry-forward [--repo PATH] [--json]`

### Sample carry-forward policy output (JSON)

```json
{
  "generated_at_utc": "2025-03-17T18:05:00.123456+00:00",
  "rationale_lines": [
    "1 urgent carry-forward (approvals/blocked).",
    "2 optional carry-forward.",
    "1 automated follow-up item(s)."
  ],
  "urgent_items": [
    {
      "item_id": "cf_abc123",
      "kind": "unresolved",
      "carry_forward_class": "urgent",
      "label": "Approve PR #42 — dashboard fix",
      "ref": "pr_42",
      "command": "workflow-dataset queue view",
      "created_at_utc": "2025-03-17T18:05:00Z",
      "priority": "high"
    }
  ],
  "optional_items": [
    {
      "item_id": "cf_def456",
      "kind": "unresolved",
      "carry_forward_class": "optional",
      "label": "Review experiment results",
      "ref": "exp_1",
      "command": "workflow-dataset queue view",
      "created_at_utc": "2025-03-17T18:05:00Z",
      "priority": "medium"
    }
  ],
  "automated_follow_up_items": [
    {
      "item_id": "cf_ghi789",
      "kind": "unresolved",
      "carry_forward_class": "automated_follow_up",
      "label": "Automation completed: sync_run_01",
      "ref": "sync_run_01",
      "command": "workflow-dataset queue view",
      "created_at_utc": "2025-03-17T18:05:00Z",
      "priority": "low"
    }
  ]
}
```

## Next-day operating recommendation

After shutdown, the engine stores a **next-session recommendation** with:

- `operating_mode` — e.g. `review_first` when there are urgent items, else `startup`.
- `first_action_label` / `first_action_command` — e.g. "Review urgent carry-forward" and `workflow-dataset continuity carry-forward`.
- `urgent_carry_forward_count`, `optional_carry_forward_count`, `automated_follow_up_count`.
- `rationale_lines` — short reasons for the recommendation.

Morning flow uses this: when `urgent_carry_forward_count > 0`, it recommends the stored first action (e.g. run carry-forward first).

## Tests

Run fast continuity tests (includes M36L.1 rhythm and policy tests):

```bash
pytest tests/test_continuity_engine.py -v -m "not slow"
```

New tests: `test_rhythm_list_returns_default`, `test_rhythm_recommended_first_phase`, `test_carry_forward_policy_empty_queue`, `test_build_next_day_operating_recommendation`, `test_next_session_recommendation_m36l1_fields_roundtrip`.
