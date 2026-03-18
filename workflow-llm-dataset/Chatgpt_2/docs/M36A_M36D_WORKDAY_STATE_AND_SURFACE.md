# M36A–M36D Daily Operating Surface + Workday State Machine

First-draft daily operating layer: workday state machine, daily operating surface, state transitions, CLI, mission control visibility, tests and docs.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `day` group: `day status`, `day start`, `day mode --set`, `day wrap-up`, `day shutdown`, `day resume`. |
| `src/workflow_dataset/mission_control/state.py` | Added `workday_state`: current_workday_mode, pending_state_transition_recommendation, blocked_mode_transitions, day_progress_snapshot, next_best_operating_action. |
| `src/workflow_dataset/mission_control/report.py` | Added [Workday] section: mode, day_id, pending_transition, next action, blocked. |

---

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/workday/__init__.py` | Public API exports. |
| `src/workflow_dataset/workday/models.py` | WorkdayState enum, WorkdayStateRecord, StateTransition, ActiveDailyContext, DaySummarySnapshot, BlockedStateInfo. |
| `src/workflow_dataset/workday/state_machine.py` | VALID_TRANSITIONS, can_transition, apply_transition, gather_context, entry/exit conditions. |
| `src/workflow_dataset/workday/store.py` | load/save_workday_state (data/local/workday/state.json), load/save_day_summary (data/local/workday/summaries/<day_id>.json). |
| `src/workflow_dataset/workday/surface.py` | DailyOperatingSurface, build_daily_operating_surface(), format_daily_operating_surface(). |
| `src/workflow_dataset/workday/cli.py` | cmd_day_status, cmd_day_start, cmd_day_mode, cmd_day_wrap_up, cmd_day_shutdown, cmd_day_resume. |
| `tests/test_workday.py` | State model, valid/invalid transitions, surface, store roundtrip, start/mode/shutdown/resume. |
| `docs/M36A_M36D_WORKDAY_BEFORE_CODING.md` | Pre-coding analysis. |
| `docs/M36A_M36D_WORKDAY_STATE_AND_SURFACE.md` | This document. |

---

## 3. Exact CLI usage

```bash
workflow-dataset day status
workflow-dataset day start
workflow-dataset day mode --set focus_work
workflow-dataset day mode --set review_and_approvals
workflow-dataset day mode --set operator_mode
workflow-dataset day mode --set wrap_up
workflow-dataset day mode --set shutdown
workflow-dataset day wrap-up
workflow-dataset day shutdown
workflow-dataset day resume
```

Optional `--repo-root` on all commands.

---

## 4. Sample workday state record

`data/local/workday/state.json`:

```json
{
  "state": "focus_work",
  "entered_at_iso": "2025-03-16T09:15:00Z",
  "previous_state": "startup",
  "day_started_at_iso": "2025-03-16T08:00:00Z",
  "transition_history": [
    { "from_state": "not_started", "to_state": "startup", "at_iso": "2025-03-16T08:00:00Z", "trigger": "cli_start" },
    { "from_state": "startup", "to_state": "focus_work", "at_iso": "2025-03-16T09:15:00Z", "trigger": "cli_mode_set" }
  ],
  "day_id": "2025-03-16"
}
```

---

## 5. Sample daily operating surface output

```
=== Daily operating surface ===
  State: focus_work  (entered: 2025-03-16T09:15:00Z)
  Day: 2025-03-16  started: 2025-03-16T08:00:00Z

[Context]
  Project: founder_case_alpha  Founder ops case
  Focus: Complete weekly report draft
  Top queue: approval_001
  Approvals: 2 pending approval(s)
  Automation: Background: queue=1 active=0; Inbox unseen=0
  Trust: Preset: supervised_operator

[Transitions]
  Allowed next: review_and_approvals, operator_mode, wrap_up, shutdown
  Recommended: review_and_approvals
  Reason: Pending approvals; shift to review: workflow-dataset day mode --set review_and_approvals
```

---

## 6. Sample transition output

**day start (success):**
```
Day started. State: startup. Run: workflow-dataset day mode --set focus_work
```

**day mode --set focus_work (success):**
```
State set to focus_work.
```

**day shutdown (success):**
```
Day shut down. Summary saved. Next session: workflow-dataset day resume then day start
```

**day start (already started):**
```
Already in state startup. Use day mode --set to change, or day wrap-up / day shutdown.
```

---

## 7. Exact tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_workday.py -v
```

Test names:

- test_workday_state_enum
- test_valid_transitions_not_started_to_startup
- test_valid_transitions_startup_to_focus
- test_invalid_transition_not_started_to_focus
- test_apply_transition_startup
- test_store_roundtrip
- test_build_daily_operating_surface_empty
- test_cmd_day_start
- test_cmd_day_start_idempotent_after_start
- test_cmd_day_mode_focus
- test_cmd_day_shutdown_saves_summary
- test_cmd_day_resume_after_shutdown
- test_day_id_from_iso
- test_empty_state_load

---

## 8. Exact remaining gaps for later refinement

- **No auto-transitions**: State changes only via explicit CLI (or future API). No time-based or event-based auto transition.
- **Resume semantics**: Today “day resume” sets resume_pending after shutdown; “day start” then enters startup. A “resume to last state” (e.g. focus_work) could be added as an option.
- **Day boundary**: day_id is YYYY-MM-DD from current date; no explicit “start of day” calendar or timezone; midnight rollover does not auto-reset state.
- **Operator-mode entry gate**: Only “operator_mode_paused” is checked; trust preset or approval readiness could be added as entry conditions.
- **Day summary content**: DaySummarySnapshot has states_visited, approvals_processed_count (not yet populated from real approval counts), top_actions (not yet filled from session/outcomes).
- **Mission control next_action**: recommend_next_action() is unchanged; workday “next best operating action” is separate and could be merged or prioritized in one place.
- **Workspace/home integration**: Workspace home does not yet show “current workday mode”; could add a line to workspace home or a quick “day status” callout.
- **Blocked transition UX**: Blocked reasons are in surface and mission_control; no CLI command to “explain why I can’t enter operator_mode” (could add `day explain-blocked --to operator_mode`).
