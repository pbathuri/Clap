# M36L.1 — Daily Rhythm Templates + Carry-Forward Policies

First-draft extension to the continuity engine (M36I–M36L):

- **Daily rhythm templates** — named sequences of phases (e.g. morning check → inbox → deep work → review → wrap-up) with suggested duration and first-action commands.
- **Carry-forward policies** — classify queue items into **urgent**, **optional**, and **automated follow-up** for clearer next-day operating recommendations.

## 1. Daily rhythm templates

Templates live in `data/local/continuity_engine/rhythm_templates.json` or fall back to built-in defaults. The **active** template is stored in `active_rhythm_template_id.txt`.

### Sample daily rhythm template (default)

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

### CLI

- **List templates:** `workflow-dataset continuity rhythm --list` (or `-l`)
- **Show active template:** `workflow-dataset continuity rhythm`
- **Set active template:** `workflow-dataset continuity rhythm --set default` (or `-s default`)
- **JSON:** add `--json` to any of the above

## 2. Carry-forward policy

At shutdown, the engine runs **apply_carry_forward_policy** on the current queue and classifies items into:

- **Urgent** — approvals (high/urgent), blocked items. Recommend starting next day with “Review urgent carry-forward.”
- **Optional** — other unresolved queue items. Can be reviewed after urgent or in wrap-up.
- **Automated follow-up** — automation_inbox / routing_target automation_follow_up. Can be batched or deferred.

This drives:

- **Carry-forward list** persisted with `carry_forward_class` (urgent | optional | automated_follow_up).
- **Next-session recommendation** with `operating_mode` (e.g. `review_first` | `startup`), `urgent_carry_forward_count`, `optional_carry_forward_count`, `automated_follow_up_count`, and `rationale_lines`.

### Sample carry-forward policy output

(Current queue classified; e.g. from `workflow-dataset continuity carry-forward-policy --json`.)

```json
{
  "generated_at_utc": "2025-03-17T14:00:00.000000Z",
  "rationale_lines": [
    "1 urgent carry-forward (approvals/blocked).",
    "2 optional carry-forward.",
    "No automated follow-up."
  ],
  "urgent_items": [
    {
      "item_id": "cf_...",
      "kind": "unresolved",
      "carry_forward_class": "urgent",
      "label": "Approve PR #42 — backend auth",
      "ref": "approval_42",
      "command": "workflow-dataset queue view",
      "created_at_utc": "2025-03-17T14:00:00Z",
      "priority": "high"
    }
  ],
  "optional_items": [
    {
      "item_id": "cf_...",
      "kind": "unresolved",
      "carry_forward_class": "optional",
      "label": "Review staging report",
      "ref": "review_abc",
      "command": "workflow-dataset queue view",
      "created_at_utc": "2025-03-17T14:00:00Z",
      "priority": "medium"
    }
  ],
  "automated_follow_up_items": []
}
```

### CLI

- **Policy for current queue:** `workflow-dataset continuity carry-forward-policy` (or `--json`)
- **List stored carry-forward (from last shutdown):** `workflow-dataset continuity carry-forward` — items now show `[urgent]`, `[optional]`, or `[automated_follow_up]`

## 3. Next-day operating recommendation

After shutdown, the engine builds a **NextSessionRecommendation** with:

- `operating_mode` — e.g. `review_first` when there are urgent items, else `startup`
- `first_action_label` / `first_action_command` — e.g. “Review urgent carry-forward” + `workflow-dataset continuity carry-forward`, or “Run morning flow” + `workflow-dataset continuity morning`
- `urgent_carry_forward_count`, `optional_carry_forward_count`, `automated_follow_up_count`
- `rationale_lines` — short reasons for the recommendation

Morning and resume flows can use this to suggest the first action of the day.

## 4. Tests run

- **Fast (default):** `pytest tests/test_continuity_engine.py -m "not slow"`
  - Includes: `test_rhythm_list_returns_default`, `test_rhythm_recommended_first_phase`, `test_carry_forward_policy_empty_queue`, `test_build_next_day_operating_recommendation`, `test_next_session_recommendation_m36l1_fields_roundtrip`
- **All (including slow):** `pytest tests/test_continuity_engine.py`

## 5. Next recommended step for this pane

- **Wire rhythm into morning/resume:** Use the active rhythm template in the morning flow to suggest the first phase and command (e.g. “Start with: Morning check — workflow-dataset continuity morning”) and optionally show the rest of the day’s phases.
- **Expose operating recommendation in Mission Control:** Surface `operating_mode`, `first_action_command`, and `rationale_lines` from the last NextSessionRecommendation in the mission control report so the operator sees the recommended start-of-day action and reason.
- **Optional:** Allow custom rhythm templates (e.g. “focus day”, “review-heavy day”) and persist them under `data/local/continuity_engine/rhythm_templates.json`.
