# M45L.1 — Supervision Presets + Takeover Playbooks (Deliverable)

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/supervisory_control/models.py` | Added SupervisionPreset, TakeoverPlaybook, OperatorLoopSummary. |
| `src/workflow_dataset/supervisory_control/store.py` | Added load/save for supervision_presets, takeover_playbooks, current_preset_id. |
| `src/workflow_dataset/supervisory_control/__init__.py` | Exported SupervisionPreset, TakeoverPlaybook, OperatorLoopSummary. |
| `src/workflow_dataset/cli.py` | Added supervision presets, set-preset, playbooks, summary. |
| `tests/test_supervisory_control.py` | Added 6 tests for presets, playbooks, operator summary, current preset, list presets/playbooks. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/supervisory_control/presets.py` | Default SupervisionPreset (conservative, balanced, operator_heavy) and TakeoverPlaybook (blocked_no_progress, repeated_handoff_failure, pending_stale, high_risk_pending); get_preset_by_id, get_playbook_by_id, get_playbooks_for_trigger. |
| `src/workflow_dataset/supervisory_control/summaries.py` | build_operator_summary(loop_id, preset_id), list_presets_with_current, list_playbooks; when to continue/intervene/terminate + suggested playbook. |
| `docs/M45L1_SUPERVISION_PRESETS_AND_PLAYBOOKS.md` | This deliverable. |

## 3. Sample supervision preset

```json
{
  "preset_id": "balanced",
  "label": "Balanced",
  "description": "Suggest pause on blocked; require approval for real; suggest takeover after several failures.",
  "auto_pause_on_blocked": false,
  "require_approval_before_real": true,
  "max_pending_before_escalation": 5,
  "suggest_takeover_on_repeated_failure": true,
  "repeated_failure_count": 3,
  "when_to_continue_hint": "Continue when the loop is making progress and you are comfortable with the next proposed action.",
  "when_to_intervene_hint": "Intervene when the loop is stuck, confidence is low, or you want to redirect the next step.",
  "when_to_terminate_hint": "Terminate when the loop is no longer aligned with current priorities or cannot make progress."
}
```

## 4. Sample takeover playbook

```json
{
  "playbook_id": "blocked_no_progress",
  "label": "Blocked with no progress",
  "trigger_condition": "blocked_no_progress",
  "description": "Loop is blocked and not advancing; cycle status blocked or handoff failed.",
  "suggested_actions": [
    "Pause and inspect: supervision show --id <loop_id>",
    "Review blocked_reason and next proposed action",
    "Redirect with a different next step, or take over to complete manually"
  ],
  "when_to_continue": "Continue only if you have unblocked the loop (e.g. by approving a different action or resolving the blocker).",
  "when_to_intervene": "Intervene now: pause, then redirect or takeover. Do not let the loop retry the same failing step.",
  "when_to_terminate": "Terminate if the goal cannot be achieved with the current plan or the blocker is permanent."
}
```

## 5. Exact tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_supervisory_control.py -v
```

**Result:** 20 passed (14 existing + 6 M45L.1).

New tests:

- test_supervision_preset_defaults
- test_takeover_playbook_defaults
- test_build_operator_summary
- test_build_operator_summary_with_playbook
- test_save_load_current_preset
- test_list_presets_and_playbooks

## 6. Next recommended step for the pane

- **Apply preset in panel** — When building the loop view or mission_control slice, use the current preset (e.g. auto_pause_on_blocked) so that “pause on blocked” is actually applied by the supervisory layer when the cycle becomes blocked (e.g. call pause_loop from a periodic or post-handoff check when preset says auto_pause_on_blocked and gates.blocked_reason is set).
- **Surface summary in CLI by default** — For `supervision show --id X`, optionally print the operator summary (continue/intervene/terminate) and suggested playbook inline, or add a `--summary` flag so operators see when to continue/intervene/terminate without a separate command.
- **Playbook actions as runnable hints** — In UI or CLI, turn suggested_actions into one-click or copy-paste commands (e.g. substitute loop_id into “supervision pause --id <loop_id>”) so operators can follow the playbook quickly.
- **Custom presets/playbooks** — Allow storing operator-defined presets and playbooks (already supported by store); add CLI commands to add/edit presets and playbooks so teams can define their own conservative/operator-heavy variants and failure playbooks.
