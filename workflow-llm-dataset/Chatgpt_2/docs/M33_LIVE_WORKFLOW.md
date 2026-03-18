# M33E–M33H — Supervised Real-Time Workflow Runner + Assist Escalation

First-draft real-time workflow assistance layer: map active workflow to a supervised plan, sequence steps, escalate assist tiers, hand off to planner/executor/review. All explicit and supervised.

## Model (Phase A)

- **EscalationTier** (enum): `hint_only`, `action_card_suggestion`, `draft_handoff_prep`, `planner_goal_prefill`, `simulated_execution_handoff`, `review_approval_routing`.
- **WorkflowRunState**: `active`, `paused`, `awaiting_checkpoint`, `blocked`, `completed`, `cancelled`, `no_workflow`.
- **ExpectedHandoff**: label, path_or_type, step_index, handoff_target.
- **LiveStepSuggestion**: step_index, label, description, step_class, approval_required, checkpoint_before, expected_handoff, escalation_tier, hint_text, plan_ref, provenance.
- **BlockedRealTimeStep**: step_index, label, blocked_reason, approval_scope, handoff_suggestion, plan_ref, run_id.
- **SupervisedLiveWorkflow**: run_id, goal_text, plan_id, plan_ref, plan_source, steps, current_step_index, next_step_index, alternate_path_summary, escalation_path_summary, current_escalation_tier, checkpoint_required_before, blocked_step, state, project_hint, session_hint, created_utc, updated_utc.

## Step generation (Phase B)

- **generate_live_workflow_steps(goal_text=, routine_id=, plan_ref=, project_hint=, session_hint=, repo_root=, mode=)**  
  Uses planner **compile_goal_to_plan** when goal/routine is provided. Converts Plan steps to LiveStepSuggestion; sets current_step_index=0, next_step_index=1 if multiple steps; fills escalation_path_summary; detects first blocked condition and sets blocked_step and state=blocked. With no goal, returns state=no_workflow and empty steps.

## Escalation (Phase C)

- **get_escalation_tiers()** — ordered list hint → … → review.
- **next_escalation_tier(current)** — next tier or None at top.
- **build_handoff_for_tier(tier, step, run)** — returns `{ handoff_target, handoff_params }` aligned with HandoffTarget (prefill_command, compile_plan, queue_simulated, approval_studio, create_draft). No hidden execution; handoff is explicit.

## State (Phase D)

- **get_live_workflow_run(repo_root)** — load current run from `data/local/live_workflow/current_run.json`.
- **save_live_workflow_run(run, repo_root)** — persist run (JSON).

## CLI

- **workflow-dataset live-workflow now** [--goal \<goal\>] [--routine \<id\>] [--repo-root \<path\>] [--json] [--save/--no-save]  
  Generate supervised live workflow from goal/routine; optionally save as current run.
- **workflow-dataset live-workflow steps** [--latest] [--goal \<goal\>] [--repo-root \<path\>] [--json]  
  Show step sequence for latest saved run or from --goal.
- **workflow-dataset live-workflow escalate** [--latest] [--repo-root \<path\>] [--json]  
  Show next escalation tier and handoff for current step.
- **workflow-dataset live-workflow preview-next** [--latest] [--repo-root \<path\>] [--json]  
  Preview current step, next step, blocked (if any), recommended assist.

## Mission control

- **live_workflow_state** in mission control state: active_run_id, goal_text, plan_ref, current_step_index, next_step_index, escalation_level, blocked_real_time_step, next_recommended_assist, state, steps_count, next_action.
- Report section **[Live workflow]**: run_id, state, current_step, escalation, blocked reason, next_assist, next action.

---

## Sample outputs

### Sample live workflow record (JSON excerpt)

```json
{
  "run_id": "lwr_abc123",
  "goal_text": "Weekly report",
  "plan_ref": "weekly_report",
  "plan_source": "routine",
  "steps": [
    {
      "step_index": 0,
      "label": "Run weekly report job",
      "escalation_tier": "hint_only",
      "hint_text": "Run weekly report job"
    }
  ],
  "current_step_index": 0,
  "next_step_index": 1,
  "state": "active",
  "current_escalation_tier": "hint_only"
}
```

### Sample step sequence (CLI)

```
Steps run_id=lwr_abc123  current=0  next=1
  -> [0] Run weekly report job  tier=hint_only
     [1] Export to sheet  tier=hint_only
```

### Sample escalation output (CLI)

```
Escalate current_tier=hint_only -> next_tier=action_card_suggestion
  handoff_target=prefill_command  params={'command': '...', 'goal': 'Weekly report', ...}
```

### Sample blocked-step handoff

When a step is blocked (e.g. policy), the run has:

- **state**: `blocked`
- **blocked_step**: `{ step_index, label, blocked_reason, handoff_suggestion: "Open planner or approval studio to resolve.", ... }`

CLI **preview-next** and mission control report show the blocked reason and next recommended assist (e.g. open planner or approval studio).

---

## Tests

- **tests/test_live_workflow.py**: escalation tier order and next_tier; build_handoff_for_tier (hint, planner prefill, review); generate no goal → no_workflow; generate with goal (planner); to_dict serialization; blocked step handoff; state save/load; get_live_workflow_run when no file → None; safe handoff targets explicit.

Run: `pytest tests/test_live_workflow.py -v`

---

## Remaining gaps (for later refinement)

- **Episode tracker integration**: When Pane 1 workflow-episode tracker is available, consume episode_id / stage to seed goal or routine and align current_step with episode progress.
- **Current step advancement**: No automatic “mark step done” or advance current_step_index; could be driven by executor completion or explicit user command.
- **Stalled detection**: No automatic “user stalled” detection to suggest escalation; currently user or UI must call escalate/preview-next.
- **Action card creation from escalate**: build_handoff_for_tier returns params; a separate flow (e.g. action_cards builder) can create an ActionCard from that; not wired in this block.
- **Mission control next_action**: recommend_next_action() does not yet prioritize “live-workflow steps” or “live-workflow escalate” when live_workflow_state is active; can be added in mission_control/next_action.py.
