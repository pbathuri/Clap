# M26E–M26H Safe Action Runtime + Checkpointed Executor — Pre-coding analysis

## 1. What execution-capable pieces already exist

- **copilot/run.py**: `run_plan(PlanPreview)` runs `job_pack_ids` in order via `run_job`; records executed/blocked in `data/local/copilot/runs/<run_id>/plan_run.json`; `stop_on_first_blocked`; no step envelopes, no checkpoints.
- **macros/runner.py**: `macro_run(macro_id, mode, stop_at_checkpoints)` builds `PlanPreview` from routine, runs step-by-step; `_run_macro_checkpointed` pauses after checkpoint steps or before next trusted_real step; persists state via `save_run_state` (running/paused/awaiting_approval/blocked/completed); `resume_macro_run(run_id)` continues from `current_step_index`. State in `data/local/copilot/runs/<run_id>/macro_run_state.json` and `plan_run.json`.
- **macros/run_state.py**: `save_run_state`, `load_run_state`, `list_paused_runs`, `list_awaiting_approval_runs` with statuses.
- **desktop_adapters**: Contracts (ActionSpec, AdapterContract); `execute.run_execute(adapter_id, action_id, params)` with `check_execution_allowed`; simulate/real via adapter support.
- **desktop_bench/harness.py**: `run_benchmark(case_id, mode)` runs cases (including task replay in simulate); records step results and output_artifacts.
- **task_demos**: TaskDefinition (steps = adapter_id, action_id, params); `replay_task_simulate(task_id)` for simulate-only replay.
- **coordination_graph**: Advisory graph from task definition; no execution.
- **planner (schema)**: Plan, PlanStep, Checkpoint, ExpectedArtifact, BlockedCondition; step_class (reasoning_only, local_inspect, trusted_real_candidate, etc.). Planner __init__ references compile, store, explain, preview—only schema/sources present in current glob; plan contract exists.
- **approval_check**: `check_execution_allowed(adapter_id, action_id, params, repo_root)` gates execution.
- **job_packs**: `run_job(job_pack_id, mode, params)`, policy check via `check_job_policy`.

## 2. What is missing for a plan-driven runtime

- **Single execution entry point**: No unified "executor" that takes a compiled plan (from planner or routine) and runs it with one contract; today macro_run and run_plan are separate.
- **Explicit action envelope per step**: No step-level envelope (step id, action type, mode, approvals required, capability, expected artifact, reversible, checkpoint requirement, blocked reason) that is inspectable before/after run.
- **Plan-to-action mapping layer**: No explicit mapping from "plan step" to "runtime action" (adapter action vs job run vs macro step); jobs are run directly from PlanPreview.job_pack_ids.
- **Dedicated run/artifact hub**: Runs live under copilot/runs; no single executor hub for run state, artifacts, checkpoint decisions, and run summary in one place.
- **CLI**: No `executor run | status | artifacts | resume`; macro has its own resume.
- **Mission control**: No slice for "active plan run, current step, next checkpoint, blocked action, produced artifacts, run status."

## 3. Exact file plan

| Action | Path |
|--------|------|
| **Create** | `src/workflow_dataset/executor/models.py` — ActionEnvelope, ExecutionRun, RunState, CheckpointDecision |
| **Create** | `src/workflow_dataset/executor/mapping.py` — plan_to_envelopes (PlanPreview or Plan → list[ActionEnvelope]), uses job policy + step classifier |
| **Create** | `src/workflow_dataset/executor/runner.py` — run_with_checkpoints(plan_source, mode, stop_at_checkpoints), pause/resume/cancel, persist to executor hub |
| **Create** | `src/workflow_dataset/executor/hub.py` — get_runs_dir, save_run, load_run, list_runs, save_artifacts_list, checkpoint_decision |
| **Create** | `src/workflow_dataset/executor/__init__.py` — exports |
| **Modify** | `src/workflow_dataset/cli.py` — add executor_group: run, status, artifacts, resume |
| **Modify** | `src/workflow_dataset/mission_control/state.py` — add executor slice (active_run, current_step, next_checkpoint, blocked, artifacts, status) |
| **Modify** | `src/workflow_dataset/mission_control/report.py` — add [Executor] section |
| **Create** | `docs/M26E_M26H_SAFE_ACTION_RUNTIME.md` — design, envelope, runner, hub, CLI |
| **Create** | `tests/test_executor.py` — envelope creation, simulate run, checkpoint pause/resume, blocked handling, trusted-real refusal, run summary |

## 4. Safety/risk note

- Executor does **not** bypass trust/approval: it uses existing `run_job` (which uses `check_job_policy`) and adapter `check_execution_allowed`. No new execution paths that skip gates.
- **Simulate-first**: Default and explicit; real mode only when plan is allowed and operator has approved.
- **Checkpoints**: Explicit pause before next trusted-real or at configured indices; resume requires explicit CLI call (no auto-resume).
- **State and artifacts** under `data/local/executor/` are inspectable; no hidden state.

## 5. What this block will NOT do

- Will **not** implement new desktop adapters or change adapter contracts.
- Will **not** replace macro_run or run_plan; executor will **call** them or share the same run loop and persist to executor hub.
- Will **not** auto-resume or run in background; resume is explicit.
- Will **not** execute planner Plan steps directly if planner compile/store are missing; will consume PlanPreview (routine/job-based) as primary plan source and optionally Plan.from_dict if plan JSON is provided.
- Will **not** add new approval types; uses existing approval registry and job policy.
