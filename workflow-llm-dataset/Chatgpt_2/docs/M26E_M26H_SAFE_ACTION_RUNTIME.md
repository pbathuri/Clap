# M26E–M26H — Safe Action Runtime + Checkpointed Executor

## Objective

First-draft execution core that:

1. Takes a compiled plan (PlanPreview from routine/job)
2. Maps steps to safe runtime actions (action envelopes)
3. Executes simulate-first; supports narrow trusted-real where already allowed
4. Stops at checkpoints for explicit approval
5. Persists run state, blocked state, and artifacts under `data/local/executor/`
6. Keeps execution explicit, inspectable, and pauseable (no bypass of trust/approval)

## Action envelope (execution model)

Each step is wrapped in an **ActionEnvelope**:

| Field | Description |
|-------|-------------|
| step_id | Unique step id (e.g. `step_0_<job_pack_id>`) |
| step_index | 0-based index in plan |
| action_type | `job_run` \| adapter_action \| macro_step |
| action_ref | job_pack_id or adapter/macro ref |
| mode | simulate \| trusted_real_candidate |
| approvals_required | List of approval types from job |
| capability_required | Trust/capability from classifier |
| expected_artifact | Expected outputs (summary) |
| reversible | Whether step can be rolled back |
| checkpoint_required | Pause for approval before this step (e.g. before trusted_real in real mode) |
| blocked_reason | If not executable, reason |
| label | Human-readable label (e.g. job_pack_id) |

## Plan-to-action mapping

- **Input**: PlanPreview (plan_id, job_pack_ids, mode, blocked, blocked_reasons) from `build_plan_for_routine` / `build_plan_for_job`.
- **Output**: `list[ActionEnvelope]` via `plan_preview_to_envelopes()` in `executor/mapping.py`.
- Uses existing `classify_step()` (macros) and `get_job_pack()`; sets checkpoint_required before next trusted_real step in real mode or at configured checkpoint_after indices.

## Checkpointed runner

- **Entry**: `run_with_checkpoints(plan_source, plan_ref, mode, repo_root, stop_at_checkpoints, ...)` in `executor/runner.py`.
- Resolves plan via `resolve_plan()` (routine | job).
- Builds envelopes; runs steps in order with existing `run_job()`.
- **Blocked**: step in plan.blocked or run_job error → status=blocked, persist, return.
- **Checkpoint**: after a step that is in checkpoint_after or before next trusted_real step → status=awaiting_approval, persist, return with resume hint.
- **Resume**: `resume_run(run_id, decision)` with decision=proceed | cancel | defer; on proceed, continues from approval_required_before_step.

## Artifact / run hub

- **Location**: `data/local/executor/runs/<run_id>/`
- **Files**: `run_state.json` (ExecutionRun serialized), `artifacts.json` (list of artifact paths).
- **API**: `save_run`, `load_run`, `list_runs`, `save_artifacts_list`, `load_artifacts_list`, `record_checkpoint_decision`.

## CLI

| Command | Description |
|---------|-------------|
| `workflow-dataset executor run --plan latest --mode simulate` | Run plan (use last run’s plan_ref if no --plan-ref) |
| `workflow-dataset executor run --plan-ref <routine_id\|job_id> --mode simulate` | Run plan by ref |
| `workflow-dataset executor run --plan-ref <id> --mode real --stop-at-checkpoints` | Run in real mode, pause at checkpoints |
| `workflow-dataset executor status --run latest` | Show run status, current step, next checkpoint, blocked |
| `workflow-dataset executor artifacts --run latest` | List artifacts for run |
| `workflow-dataset executor resume --run <run_id> --decision proceed` | Resume after checkpoint |
| `workflow-dataset executor resume --run <run_id> --decision cancel` | Cancel at checkpoint |

## Mission control

- **State slice**: `state["executor"]` with active_run_id, plan_ref, status, current_step_index, next_checkpoint, blocked_action, produced_artifacts_count, executed_count, blocked_count, next_action.
- **Report**: `[Executor]` section with run, plan, status, step, next_checkpoint, blocked, artifacts/executed/blocked counts, next command.

## Safety

- No new execution paths: uses existing `run_job` and approval checks.
- Simulate-first; trusted-real only where policy allows.
- No hidden background looping; resume is explicit.
- Run state and checkpoint decisions are persisted and visible.

## Remaining gaps (for later refinement)

- Plan source “latest” from planner store (Plan) not yet wired; “latest” currently means last executor run’s plan_ref.
- No adapter_action / macro_step action types in mapping yet (only job_run).
- Run summary could include step-level logs and artifact paths in CLI output.
- Trusted-real refusal when approval/capability missing is enforced by existing run_job/policy; executor does not add extra gates.
- Tests for checkpoint pause/resume (multi-step plan with checkpoint) and resume cancel/defer can be added with a small 2-step routine.
