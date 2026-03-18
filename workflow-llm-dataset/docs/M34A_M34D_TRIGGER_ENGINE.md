# M34A–M34D — Trigger Engine + Recurring Workflow Definitions

First-draft local trigger and recurring workflow definition layer: bounded automation triggers, recurring workflows tied to project/pack/routine, conditions/schedules/stop rules, and connection to planner/executor/action-card flows. Explicit, inspectable, policy-aware.

## Phase A — Trigger model

- **TriggerKind**: `time_based`, `event_based`, `project_state`, `idle_resume`, `approval_available`, `artifact_updated`, `recurring_digest`.
- **TriggerDefinition**: trigger_id, kind, label, scope (global | project:id | pack:id | routine:id), enabled, condition (dict: cron_expression, time_window, project_id, artifact_pattern, idle_seconds, event_type), debounce_seconds, repeat_limit_per_day, required_policy_trust (simulate | approval_required | trusted), retention_days, created_utc, updated_utc, last_matched_utc, match_count.

## Phase B — Recurring workflow model

- **RecurringWorkflowDefinition**: workflow_id, label, description, project_id, pack_id, routine_id, trigger_ids[], planner_goal, plan_ref, plan_source (goal | routine | job), execution_mode (simulate | real | simulate_then_real), stop_conditions[], artifact_expectations[], approval_points[] (step indices), review_destination, enabled, created_utc, updated_utc.

## Phase C — Trigger evaluation / matching

- **evaluate_active_triggers(repo_root, work_state, now_utc)** → (matches: list[TriggerMatchResult], summary: TriggerEvaluationSummary). Evaluates all defined triggers; returns active, suppressed, blocked; last_matched, next_scheduled_workflow.
- **explain_trigger_match(trigger_id, repo_root, work_state, now_utc)** → dict with matched, reason, blocked, suppressed, workflow_id.
- **list_blocked_suppressed_triggers(repo_root, work_state)** → {blocked: [{trigger_id, reason}], suppressed: [...]}.
- **match_triggers_to_workflows(matched_trigger_ids, repo_root)** → list[(trigger_id, workflow_id)].

## Store

- **Location**: `data/local/automations/triggers/*.json`, `data/local/automations/workflows/*.json`.
- **API**: list_trigger_ids, get_trigger, save_trigger, list_workflow_ids, get_workflow, save_workflow.

## CLI

- **workflow-dataset automations list** [--repo-root] [--json] — List triggers and recurring workflows.
- **workflow-dataset automations triggers** [--repo-root] [--json] — Evaluate active triggers and show match summary.
- **workflow-dataset automations define --id \<id\>** [--kind trigger|workflow] [--label] [--trigger-kind] [--goal] [--plan-ref] [--trigger-ids] — Define trigger or workflow (first-draft overwrite).
- **workflow-dataset automations explain --id \<id\>** [--repo-root] [--json] — Explain trigger match or show workflow definition.
- **workflow-dataset automations simulate-trigger --id \<trigger_id\>** [--repo-root] [--json] — Simulate trigger evaluation.

## Mission control

- **automations_state**: active_trigger_ids, suppressed_trigger_ids, blocked_trigger_ids, last_matched_trigger_id, last_matched_utc, next_scheduled_workflow_id, next_scheduled_utc, awaiting_review_workflow_ids.
- **Report**: [Automations] active=N suppressed=N blocked=N last_matched=… next_scheduled_workflow=…

---

## Sample trigger definition

**data/local/automations/triggers/morning_project_digest.json**:

```json
{
  "trigger_id": "morning_project_digest",
  "kind": "recurring_digest",
  "label": "Morning project digest",
  "scope": "global",
  "enabled": true,
  "condition": { "time_window": "morning" },
  "debounce_seconds": 0,
  "repeat_limit_per_day": 1,
  "required_policy_trust": "simulate",
  "retention_days": 30,
  "created_utc": "",
  "updated_utc": "",
  "last_matched_utc": "",
  "match_count": 0
}
```

## Sample recurring workflow definition

**data/local/automations/workflows/morning_project_digest.json**:

```json
{
  "workflow_id": "morning_project_digest",
  "label": "Morning project digest",
  "description": "Daily morning digest for active project; can feed planner/executor.",
  "project_id": "",
  "pack_id": "",
  "routine_id": "",
  "trigger_ids": ["morning_project_digest"],
  "planner_goal": "Daily project digest",
  "plan_ref": "",
  "plan_source": "goal",
  "execution_mode": "simulate",
  "stop_conditions": ["artifact_produced", "manual_stop"],
  "artifact_expectations": ["digest_report"],
  "approval_points": [],
  "review_destination": "",
  "enabled": true,
  "created_utc": "",
  "updated_utc": ""
}
```

## Sample trigger explanation output

```
Trigger explanation
  trigger_id=morning_project_digest  kind=recurring_digest  enabled=True
  matched=True  reason=Recurring digest trigger (time_window=morning); matched for digest generation.
  workflow_id=morning_project_digest
```

---

## Tests

- **tests/test_automations.py**: trigger/workflow models, save/load, evaluate empty, evaluate recurring_digest match, suppressed when disabled, explain match, explain not found, list_blocked_suppressed, match_triggers_to_workflows, no-trigger conflict (multiple active).

Run: `pytest tests/test_automations.py -v`

---

## M34D.1 — Automation templates + guardrail profiles

**Automation templates** (e.g. morning digest, blocked-work follow-up, approval sweep, end-of-day wrap): reusable shapes that produce a trigger + workflow pair. Stored under `data/local/automations/templates/*.json`. **AutomationTemplate**: template_id, kind (AutomationTemplateKind: morning_digest, blocked_work_follow_up, approval_sweep, end_of_day_wrap), label, description, default_trigger_kind, default_trigger_condition, default_planner_goal, default_execution_mode, default_stop_conditions. **instantiate_from_template(template_id, instance_id, repo_root, overrides)** → (TriggerDefinition, RecurringWorkflowDefinition).

**Guardrail profiles** (e.g. strict, supervised, bounded-recurring): control which triggers are allowed and when they are suppressed or blocked. Stored under `data/local/automations/guardrails/*.json`. **GuardrailProfile**: profile_id, kind (GuardrailProfileKind: strict, supervised, bounded_recurring), label, suppression_rules (list of SuppressionRule), allowed_trigger_kinds (empty = all), require_approval_for_real, max_recurring_per_day, is_default. **SuppressionRule**: rule_id, description, trigger_kind_filter (empty = all), condition_type (e.g. disabled, no_approval, exceeds_daily_cap), action (suppress | block), reason, params. **get_active_guardrail_profile(repo_root)** returns the profile with is_default=True, or the first profile.

**Clearer trigger suppression**: Evaluation applies the active guardrail profile after per-trigger logic. If profile.allowed_trigger_kinds is non-empty and trigger.kind is not in the list → suppressed with reason "Guardrail: trigger kind not in allowed list." Suppression rules are applied in order: condition_type disabled → suppress; no_approval (and work_state has no approval) → block or suppress; exceeds_daily_cap (match_count >= max_per_day) → suppress. explain_trigger_match and list_blocked_suppressed_triggers include these reasons.

**CLI (M34D.1)**: `automations templates` [--repo-root] [--json], `automations guardrails` [--repo-root] [--json], `automations from-template --template <id> --instance-id <id>` [--save/--no-save] [--json].

**Sample template**: `data/local/automations/templates/morning_digest.json`. **Sample guardrail**: `data/local/automations/guardrails/supervised.json` (no_approval block, recurring_daily_cap suppress); `guardrails/strict.json` (allowed_trigger_kinds = event_based, approval_available only).

---

## Remaining gaps for later refinement

- **Time-based semantics**: `time_based` and `recurring_digest` use time_window/cron_expression but do not yet compute “next fire time” from real clock; evaluation is “would match now” heuristic. Add next_scheduled_utc from cron or time_window.
- **Project-state**: `project_state` trigger needs current_project_id in context (e.g. from project_case); currently only matches if provided via work_state or future context param.
- **Artifact-updated**: `artifact_updated` is heuristic (pattern present); no file mtime or event subscription yet.
- **Idle/resume**: `idle_resume` is “consider matched when resume detected”; no actual idle detection or resume event yet.
- **Bridge to background_run**: Matched trigger + workflow should produce QueuedRecurringJob for background_run; not wired in this block.
- **Execution**: This block does not run workflows; it only defines and evaluates. Execution remains via planner/executor/background_run with policy checks.
- **Awaiting review**: awaiting_review_workflow_ids is not yet populated from run outcomes or review studio.
