# M45A–M45D Adaptive Execution — Deliverable

First-draft bounded multi-step adaptive execution layer: plans, loops, step progression, stop/escalation, CLI, mission control.

---

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/mission_control/state.py` | Added `adaptive_execution_state` via `adaptive_execution_slice(repo_root)` and `local_sources["adaptive_execution"]`. |
| `src/workflow_dataset/mission_control/report.py` | Added `[Adaptive execution]` section: active_loop_id, running/awaiting counts, next_step, remaining_safe_steps, branch, next_takeover, stop/escalation reason. |
| `src/workflow_dataset/cli.py` | New group `adaptive-execution` with commands: plans, show, explain, step, stop. |

---

## 2. Files created

| File | Purpose |
|------|--------|
| `docs/M45_ADAPTIVE_EXECUTION_READ_FIRST.md` | Pre-coding: existing behavior, gaps, file plan, safety, loop-boundary principles, what this block will NOT do. |
| `src/workflow_dataset/adaptive_execution/models.py` | AdaptiveExecutionPlan, BoundedExecutionLoop, ExecutionStep, PlanBranch, StepOutcome, AdaptationTrigger, StopCondition, EscalationCondition, HumanTakeoverPoint. |
| `src/workflow_dataset/adaptive_execution/generator.py` | generate_plan_from_goal, create_bounded_loop, generate_loop_from_goal (with optional memory prior cases). |
| `src/workflow_dataset/adaptive_execution/store.py` | save_loop, load_loop, list_active_loops; persist under data/local/adaptive_execution/active_loops.json. |
| `src/workflow_dataset/adaptive_execution/progression.py` | advance_step, stop_loop, escalate_loop, record_takeover_decision; adaptation (blocked/confidence) before next-step. |
| `src/workflow_dataset/adaptive_execution/mission_control.py` | adaptive_execution_slice for mission control. |
| `src/workflow_dataset/adaptive_execution/__init__.py` | Public exports. |
| `tests/test_adaptive_execution.py` | Tests: plan creation, bounded loop enforcement, branch/fallback, stop/escalation, no-loop/invalid, blocked-step, list, mission-control slice. |
| `docs/M45_ADAPTIVE_EXECUTION_DELIVERABLE.md` | This file. |

---

## 3. Exact CLI usage

```bash
# List loops or create plan+loop from goal
workflow-dataset adaptive-execution plans
workflow-dataset adaptive-execution plans --goal "Weekly summary" --max-steps 20
workflow-dataset adaptive-execution plans --goal "Run report" -n 10 -r /path/to/repo

# Show loop state
workflow-dataset adaptive-execution show --id loop_abc123
workflow-dataset adaptive-execution show -i loop_abc123 --json

# Explain loop state (branches, stop/escalation, takeover)
workflow-dataset adaptive-execution explain --id loop_abc123

# Advance one step (record outcome: status, confidence)
workflow-dataset adaptive-execution step --id loop_abc123
workflow-dataset adaptive-execution step --id loop_abc123 --status blocked --confidence 0.3

# Stop the loop
workflow-dataset adaptive-execution stop --id loop_abc123
workflow-dataset adaptive-execution stop --id loop_abc123 --reason manual_stop
```

---

## 4. Sample adaptive execution plan

From `generate_plan_from_goal("Weekly summary").to_dict()` (minimal):

```json
{
  "plan_id": "aplan_...",
  "goal_text": "Weekly summary",
  "steps": [
    {
      "step_index": 0,
      "step_id": "step_...",
      "label": "Weekly summary step",
      "action_type": "job_run",
      "action_ref": "job_id",
      "trust_level": "",
      "approval_required": false,
      "checkpoint_before": false,
      "allowed": true,
      "blocked_reason": ""
    }
  ],
  "branches": [
    { "branch_id": "main", "label": "Main", "step_indices": [0], "is_fallback": false, "is_human_only": false },
    { "branch_id": "fallback", "label": "Fallback", "step_indices": [0], "is_fallback": true, "is_human_only": true }
  ],
  "default_branch_id": "main",
  "fallback_branch_id": "fallback",
  "stop_conditions": [
    { "condition_id": "max_steps", "kind": "max_steps_reached", "description": "Max steps reached." },
    { "condition_id": "manual", "kind": "manual_stop", "description": "Operator stopped the loop." }
  ],
  "escalation_conditions": [
    { "condition_id": "blocked_esc", "kind": "blocked", "handoff_reason": "blocked" },
    { "condition_id": "approval", "kind": "approval_required", "handoff_reason": "approval_required" }
  ]
}
```

---

## 5. Sample loop progression output

After `advance_step(loop_id, outcome=StepOutcome(step_index=0, status="success", confidence=0.9))`:

```python
{
  "loop": <BoundedExecutionLoop status=running current_step_index=1 ...>,
  "status": "running",
  "message": "Advanced to step 1.",
  "stopped": False,
  "escalated": False,
  "branch_switched": False
}
```

When outcome is `blocked` and fallback is triggered:

```python
{
  "status": "running",
  "message": "Switched to fallback branch fallback.",
  "branch_switched": True
}
```

---

## 6. Sample stop/escalation output

**Stop:**

```python
stop_loop(loop_id, reason="manual_stop")
# -> {"loop": <BoundedExecutionLoop status=stopped stop_reason=manual_stop>, "status": "stopped", "message": "manual_stop"}
```

**Escalate:**

```python
escalate_loop(loop_id, reason="blocked")
# -> {"loop": <BoundedExecutionLoop status=escalated escalation_reason=blocked>, "status": "escalated", "message": "blocked"}
```

---

## 7. Exact tests run

```bash
pytest tests/test_adaptive_execution.py -v
```

- test_adaptive_plan_creation
- test_bounded_loop_enforcement
- test_branch_fallback_behavior
- test_stop_escalation_logic
- test_no_loop_invalid_loop_behavior
- test_blocked_step_handling
- test_list_active_loops
- test_mission_control_slice

**8 passed.**

---

## 8. Exact remaining gaps for later refinement

- **Execution wiring**: Step advancement does not yet invoke the executor (`run_with_checkpoints` or `run_job`); it only updates loop state. A later pass should run the current step via executor when calling `step` (or a separate `run-step` command).
- **Routine/job source**: generate_plan_from_goal uses planner when available; generation from operator-mode responsibilities or a specific routine_id/job_id (without goal text) is not yet implemented.
- **Takeover decision**: record_takeover_decision is implemented but not exposed in CLI; add `adaptive-execution takeover --id loop_123 --decision proceed|cancel|defer`.
- **Multi-step plans**: When planner returns multiple steps, fallback branch currently reuses the same step indices; richer branching (e.g. alternate step sequence) can be added.
- **Audit**: No audit log yet for loop start/stop/escalation/branch-switch; should append to existing audit layer when present.
- **Supervision vs adaptive**: Clarify relationship with supervisory_control (panel/loops); adaptive_execution is a separate bounded-loop layer that could feed or be monitored by supervision.
