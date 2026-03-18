# M23P — Macro Composer + Checkpointed Multi-App Execution (pre-coding)

## 1. Existing chain/routine/job structures to reuse

- **JobPack** (job_packs/schema.py): job_pack_id, title, trust_level, simulate_support, real_mode_eligibility, required_approvals, expected_outputs, parameter_schema. Load/save from data/local/job_packs/.
- **Routine** (copilot/routines.py): routine_id, title, job_pack_ids, ordering, stop_on_first_blocked, simulate_only, required_approvals. get_ordered_job_ids(routine). Stored under data/local/copilot/routines/.
- **Macro (M23V)** (macros/schema.py): macro_id, title, routine_id, job_pack_ids, mode, stop_on_first_blocked, simulate_only. Currently 1:1 with routine; steps = get_ordered_job_ids(routine).
- **PlanPreview** (copilot/plan.py): plan_id, job_pack_ids, mode, blocked, blocked_reasons, step_previews. build_plan_for_routine(), build_plan_for_job().
- **run_plan** (copilot/run.py): Executes plan job-by-job, stop_on_first_blocked, persists to data/local/copilot/runs/<run_id>/plan_run.json. No explicit checkpoints or pause/resume.
- **macro_run** (macros/runner.py): build_plan_for_routine + run_plan. No checkpoint markers or run state for pause/resume.
- **check_job_policy** (job_packs/policy.py): (allowed, message) for simulate/real. Uses approval registry and get_trusted_real_actions.
- **preview_job / run_job** (job_packs/execute.py): resolve_params, check policy, run via task_demos or desktop_bench.

## 2. Gap between current routines and checkpointed macro system

- **No checkpoint markers**: run_plan runs all steps in one go; no "pause after step N and ask before continuing."
- **No run state for pause/resume**: plan_run.json records executed/blocked but no status like "paused" or "awaiting_approval"; no resume command.
- **No step classification**: Steps are not labeled as safe_inspect, sandbox_write, trusted_real, blocked, human_checkpoint for clear operator explanation.
- **No explicit macro definition with checkpoints**: Macro is routine 1:1; no field like checkpoint_after_step_indices or per-step trust/approval/checkpoint.
- **Dashboard/mission control**: No surface for "paused macros", "awaiting approval", "last macro run", "blocked by capability."

## 3. Exact file plan

| Action | Path |
|--------|------|
| Modify | `src/workflow_dataset/macros/schema.py` — Add MacroStep (job_pack_id, step_type, trust_requirement, approval_requirement, checkpoint_before, expected_outputs). Extend Macro with steps (optional), checkpoint_after_step_indices, stop_conditions; keep routine_id 1:1 compat. |
| Create | `src/workflow_dataset/macros/step_classifier.py` — classify_step(job, mode, repo_root) → step_type (safe_inspect \| sandbox_write \| trusted_real \| blocked \| human_checkpoint). |
| Create | `src/workflow_dataset/macros/run_state.py` — MacroRunState (run_id, macro_id, status, current_step_index, executed, blocked, paused_at_checkpoint, approval_required_before_step). save_run_state, load_run_state, list_paused_runs, list_awaiting_approval. |
| Modify | `src/workflow_dataset/macros/runner.py` — Checkpointed run: run until checkpoint or blocked; persist state; resume_run(run_id). Preview includes step classification. |
| Modify | `src/workflow_dataset/macros/report.py` — Format preview with step types; format run state (paused/resume hint). |
| Modify | `src/workflow_dataset/cli.py` — macro run --stop-at-checkpoints; macro resume --run-id; macro status. |
| Modify | `src/workflow_dataset/mission_control/state.py` — Add macros summary (available, last_run, paused, awaiting_approval, blocked). |
| Create | `tests/test_macros_m23p.py` — Macro definition, preview, checkpoint handling, simulate run, pause/resume, blocked step. |
| Create | `docs/M23P_MACRO_COMPOSER.md` — Usage, sample macro, preview, checkpoint flow, tests. |

## 4. Safety/risk note

- **No autonomous execution**: Checkpoints require explicit operator approval to continue; resume is explicit CLI command. No background or auto-resume.
- **Reuse existing gates**: check_job_policy and approval registry unchanged; macro runner calls run_job per step. Real mode only where job is already trusted and approved.
- **Local-only**: Run state and plan runs under data/local/copilot/runs/. No cloud or remote execution.
- **Simulate-first**: Default mode remains simulate; real mode only when macro and steps allow and operator chooses.
