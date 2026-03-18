# M34A–M34D — Trigger Engine + Recurring Workflow Definitions: Before Coding

## 1. What scheduling / trigger / automation-adjacent pieces already exist

- **context/triggers.py (M23L)**  
  - `TriggerResult`, `evaluate_trigger_for_job`, `evaluate_trigger_for_routine`, `evaluate_all_triggers`.  
  - Job/routine-level evaluation only: `previous_job_succeeded`, `approval_blocked`, `approval_present`, `simulate_only`, `reminder_due`, `intake_available`, `routine_defined`.  
  - Driven by `WorkState` (job packs, reminders, routines, approvals). No trigger *definition* model; no schedule or project-state triggers.

- **background_run (M34E–M34H)**  
  - `QueuedRecurringJob` (automation_id, plan_source, plan_ref, trigger_type, schedule_or_trigger_ref, allowed_modes, require_approval_before_real).  
  - `BackgroundRun`, `RunSourceTrigger` (recurring_match, manual, cron, reminder_due).  
  - Queue load/save, run save/load/list, gating (`evaluate_background_policy`).  
  - **Consumes** a recurring/trigger contract; does **not** define triggers or recurring workflows. No “automation definition” or “trigger definition” store.

- **edge schedule-checks**  
  - Writes `data/local/edge/schedule.json` with interval; “use cron to run workflow-dataset edge check-now”. No daemon; no trigger definitions.

- **copilot reminders**  
  - `list_reminders`, `add_reminder`, `reminders_due`; feed `WorkState.reminders_due_sample`. No cron; “due” is currently “all listed” (no real time-based due).

- **daily/inbox**  
  - `build_daily_digest` (relevant jobs/routines, blocked, reminders_due). No schedule or trigger definitions.

- **planner, executor, action_cards, live_workflow, policy, trust, project_case, progress, portfolio, observe, mission_control**  
  - All exist; we will **connect** to them, not rebuild.

**Summary:** Context triggers evaluate job/routine *state* (WorkState). Background_run *consumes* queued jobs with a trigger_type. There is **no** explicit trigger-definition model (time, event, project-state, idle, approval-available, artifact-updated, digest), no recurring-workflow *definition* model (workflow id, triggers, goal, execution mode, stop conditions, approval points), and no evaluation layer that *matches* definitions to produce “which triggers fired and why” or “next scheduled recurring workflow”.

---

## 2. What is missing for a true recurring workflow definition layer

- **Trigger definition model**  
  - First-class definitions: time-based, event-based, project-state, idle-time/resume, approval-available, artifact-updated, recurring-digest.  
  - Each with: scope (project/pack/routine/global), enabled/disabled, condition (e.g. cron expression, project_id, artifact path pattern), debounce/repeat limits, required policy/trust mode, retention/history metadata.

- **Recurring workflow definition model**  
  - Workflow id, label, associated project/pack/routine, list of trigger refs, planner goal or action sequence, execution mode, stop conditions, artifact expectations, approval points, review destination.  
  - Stored and loadable (e.g. `data/local/automations/`); inspectable.

- **Trigger evaluation / matching**  
  - Evaluate which *defined* triggers are active at a point in time; explain why a trigger matched; identify blocked or suppressed triggers; connect matched triggers to workflow definitions.  
  - Output: matched triggers, blocked/suppressed, “next scheduled” for recurring workflows.

- **CLI and visibility**  
  - `automations list`, `automations triggers`, `automations define`, `automations explain`, `automations simulate-trigger`.  
  - Mission control: active triggers, suppressed/blocked, last matched, next scheduled recurring, automations awaiting review.

- **Bridge to background_run**  
  - Matched trigger + workflow definition can produce a `QueuedRecurringJob` (or equivalent) for the background runner to consume; we do not implement the runner loop here, only definitions and matching/explanation.

---

## 3. Exact file plan

| Action | Path |
|--------|------|
| Create | `src/workflow_dataset/automations/__init__.py` — exports |
| Create | `src/workflow_dataset/automations/models.py` — trigger types (time, event, project_state, idle_resume, approval_available, artifact_updated, recurring_digest), TriggerDefinition, RecurringWorkflowDefinition, scope/enabled/condition/debounce/policy/retention |
| Create | `src/workflow_dataset/automations/store.py` — load/save definitions under `data/local/automations/` (triggers, workflows) |
| Create | `src/workflow_dataset/automations/evaluate.py` — evaluate_active_triggers, explain_trigger_match, list_blocked_suppressed, match_triggers_to_workflows |
| Modify | `src/workflow_dataset/cli.py` — add `automations_group` with list, triggers, define, explain, simulate-trigger |
| Modify | `src/workflow_dataset/mission_control/state.py` — add automations_state (active triggers, suppressed/blocked, last_matched, next_scheduled, awaiting_review) |
| Modify | `src/workflow_dataset/mission_control/report.py` — add [Automations] section |
| Create | `tests/test_automations.py` — trigger creation, workflow definition, matching, blocked/suppressed, explain, no-trigger/conflict cases |
| Create | `docs/M34A_M34D_TRIGGER_ENGINE.md` — models, store, evaluation, CLI, samples, tests, gaps |

---

## 4. Safety / risk note

- **Do:** Keep all trigger and workflow definitions explicit and inspectable. No hidden execution from this layer; matching produces “what would run” and can feed background_run only via explicit queue. Respect policy/trust in conditions and required_modes.  
- **Do not:** Auto-execute workflows from trigger match without going through the bounded runner/policy checks (background_run, executor, approval). No hidden daemon; evaluation is on-demand (CLI or mission control).  
- **Risk:** Misconfigured schedules or conditions could suggest runs at unexpected times; mitigation: explain why a trigger matched; default to disabled or simulate-only; all definitions in versionable files.

---

## 5. What this block will NOT do

- **Auto-execute** workflows when a trigger fires; execution remains via planner/executor/background_run with policy checks.  
- **Implement** a persistent daemon or OS-wide scheduler; evaluation is invoked by CLI or mission control.  
- **Replace** context/triggers.py or background_run; we add a *definition* and *matching* layer that can feed both.  
- **Add** cloud or distributed job queues.  
- **Polish** UI beyond CLI and mission-control report; first-draft only.
