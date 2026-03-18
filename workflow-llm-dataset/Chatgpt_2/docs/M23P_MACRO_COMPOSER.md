# M23P — Macro Composer + Checkpointed Multi-App Execution

## Overview

M23P adds a **macro composer** that combines trusted job packs and routines into multi-step macros with explicit **checkpoints**, **simulate** end-to-end, and **narrow real execution** only where already trusted and approved. Behavior is **pause/resume/stop** with a presentable, human-like but controlled operator flow.

## What Was Reused (M23O/M23V)

- **Job packs**: schema, execute (preview_job, run_job), policy (check_job_policy)
- **Routines**: Routine, get_ordered_job_ids, list_routines, get_routine
- **Plan**: PlanPreview, build_plan_for_routine, build_plan_for_job
- **Run**: run_plan (non-checkpointed), list_plan_runs, get_runs_dir
- **Macro (M23V)**: list_macros, macro_preview, macro_run, get_blocked_steps (routine 1:1)

## Gaps Addressed by M23P

1. **Checkpoint markers**: Pause after specified steps or before the next trusted_real step; persist state.
2. **Run state**: `macro_run_state.json` with status (paused | awaiting_approval | blocked | completed), current_step_index, executed, blocked, errors.
3. **Step classification**: safe_inspect, sandbox_write, trusted_real, blocked (and human_checkpoint for future use).
4. **Macro schema**: checkpoint_after_step_indices, stop_conditions, expected_outputs; MacroStep with step_type, trust_requirement, approval_requirement, checkpoint_before.
5. **Mission control**: macros summary (available, last run, paused, awaiting approval, blocked).

---

## Macro Schema (Phase 1)

- **macro_id**, **title**, **description**
- **routine_id** (when set, steps = get_ordered_job_ids(routine)); **job_pack_ids** (explicit when no routine)
- **steps**: optional list of **MacroStep** (job_pack_id, step_type, trust_requirement, approval_requirement, simulate_eligible, real_mode_eligible, checkpoint_before, expected_outputs)
- **checkpoint_after_step_indices**: after running step at this index, pause for approval
- **stop_conditions**: human-readable stop conditions
- **expected_outputs**: macro-level
- **mode**, **stop_on_first_blocked**, **required_approvals**, **simulate_only**

Step types: `safe_inspect` | `sandbox_write` | `trusted_real` | `blocked` | `human_checkpoint`.

---

## Checkpointed Runner (Phase 2)

- **Preview**: `macro preview --id ID --mode simulate|real` (unchanged; report now includes step classification).
- **Run (no checkpoints)**: `macro run --id ID --mode simulate|real` — same as before (run_plan in one go).
- **Run (checkpoints)**: `macro run --id ID --mode real --stop-at-checkpoints` — runs step-by-step; pauses after checkpoint steps or before the next trusted_real step; persists state; returns run_id and message to resume.
- **Resume**: `macro resume --run-id RUN_ID` — loads state, continues from current_step_index.
- **Status**: `macro status` — lists available macros, paused runs, awaiting approval, last macro runs.

Run state is stored under `data/local/copilot/runs/<run_id>/macro_run_state.json` and `plan_run.json`.

---

## Step Classification (Phase 3)

- **safe_inspect**: simulate allowed, read-only / inspect style (e.g. benchmark_only/experimental/simulate_only, no real eligibility).
- **sandbox_write**: simulate allowed, writes in sandbox.
- **trusted_real**: real mode allowed by policy.
- **blocked**: not allowed in current mode (job missing, simulate not supported, or real refused).
- **human_checkpoint**: reserved for steps that require explicit human checkpoint (checkpoint_before set by macro definition).

The macro preview and report explain these categories via `explain_step_categories()`.

---

## Mission Control / Dashboard (Phase 4)

`get_mission_control_state()` now includes **macros**:

- **available_count**: number of macros (routines)
- **macro_trust_levels**: mode per macro
- **last_macro_run**: run_id, macro_id, status, executed_count
- **paused_runs_count**, **paused_run_ids**
- **awaiting_approval_count**, **awaiting_approval_run_ids**
- **blocked_run_ids**

---

## CLI Usage

```bash
# List macros (from routines)
workflow-dataset macro list [--repo-root PATH]

# Preview with step types
workflow-dataset macro preview --id ROUTINE_ID [--mode simulate|real] [--repo-root PATH]

# Run (no checkpoints)
workflow-dataset macro run --id ROUTINE_ID [--mode simulate|real] [--continue-on-blocked] [--repo-root PATH]

# Run with checkpoints (pause before next trusted_real or at checkpoint indices)
workflow-dataset macro run --id ROUTINE_ID --mode real --stop-at-checkpoints [--repo-root PATH]

# Resume paused / awaiting-approval run
workflow-dataset macro resume --run-id RUN_ID [--repo-root PATH]

# Status: paused, awaiting approval, last runs
workflow-dataset macro status [--repo-root PATH]
```

---

## Sample Macro Definition

Macros are currently 1:1 with routines. A routine is defined in `data/local/copilot/routines/<id>.yaml`:

```yaml
routine_id: morning_ops
title: Morning operations
description: Daily morning check
job_pack_ids: [job_a, job_b]
ordering: null
stop_on_first_blocked: true
required_approvals: []
simulate_only: true
expected_outputs: []
```

The macro layer adds checkpoint behavior at run time via `--stop-at-checkpoints` and (in future) optional `checkpoint_after_step_indices` in a macro definition file.

---

## Sample Preview

```
=== Macro preview: morning_ops ===

Plan ID: ...
Mode: simulate
Jobs: job_a, job_b

Step types: safe_inspect (read-only simulate), sandbox_write (simulate writes in sandbox), trusted_real (real mode allowed), blocked (not allowed in current mode), human_checkpoint (pause before step).

[Steps (classified)]
  1. job_a — sandbox_write (simulate_ok=True, real_ok=False)
  2. job_b — blocked (simulate_ok=False, real_ok=False)

(No execution. Use: workflow-dataset macro run --id morning_ops --mode simulate [--stop-at-checkpoints])
```

---

## Sample Checkpoint Flow

1. Operator runs: `macro run --id my_routine --mode real --stop-at-checkpoints`.
2. Runner executes step 0 (e.g. safe); step 1 is classified trusted_real → pause, save state with status=awaiting_approval, current_step_index=1.
3. Output: `Run: abc123  status=awaiting_approval  executed=1  blocked=0` and message: `Paused for approval before next step. Use: workflow-dataset macro resume --run-id abc123`.
4. Operator runs: `macro resume --run-id abc123`.
5. Runner continues from step 1; runs to completion or next checkpoint.

---

## Sample Paused/Resumed Run Output

**After run with --stop-at-checkpoints (paused):**

```
Run: xyz789  status=awaiting_approval  executed=1  blocked=0
Paused for approval before next step. Use: workflow-dataset macro resume --run-id xyz789
```

**After resume:**

```
Resumed run: xyz789  status=completed  executed=2  blocked=0
```

---

## Tests

- **test_macros_m23p.py**: macro schema (MacroStep, checkpoint fields), classify_step (missing job → blocked), explain_step_categories, run_state save/load, list_paused/awaiting empty, get_macro_steps (empty + with routine), resume not found, macro_run simulate no stop_at_checkpoints, macro_run stop_at_checkpoints with empty routine (completes).

Run:

```bash
pytest tests/test_macros_m23p.py -v
pytest tests/test_macros.py tests/test_macros_m23p.py -v
```

---

## Files Modified / Created

| Action | Path |
|--------|------|
| Modified | `src/workflow_dataset/macros/schema.py` — MacroStep, checkpoint/stop/expected_outputs |
| Modified | `src/workflow_dataset/macros/runner.py` — get_macro_steps, run_macro_checkpointed, resume_macro_run, _write_plan_run_record, _checkpointed_result |
| Modified | `src/workflow_dataset/macros/report.py` — format_macro_preview with step classification |
| Modified | `src/workflow_dataset/cli.py` — macro run --stop-at-checkpoints, macro resume, macro status |
| Modified | `src/workflow_dataset/mission_control/state.py` — macros section (available, last run, paused, awaiting, blocked) |
| Modified | `src/workflow_dataset/macros/__init__.py` — exports |
| Created | `src/workflow_dataset/macros/step_classifier.py` — classify_step, explain_step_categories |
| Created | `src/workflow_dataset/macros/run_state.py` — save/load_run_state, list_paused_runs, list_awaiting_approval_runs, list_all_macro_runs |
| Created | `tests/test_macros_m23p.py` — M23P tests |
| Created | `docs/M23P_MACRO_ANALYSIS.md` — pre-coding analysis |
| Created | `docs/M23P_MACRO_COMPOSER.md` — this doc |

---

## Safety / Risk Note

- No autonomous execution: checkpoints require explicit operator approval; resume is an explicit CLI command.
- Existing gates (check_job_policy, approval registry) unchanged; macro runner calls run_job per step.
- Local-only: run state and plan runs under `data/local/copilot/runs/`.
- Simulate-first: default mode remains simulate; real only when macro and steps allow and operator chooses.

---

## Recommended Next Phase

- **Explicit macro definition files** (e.g. `data/local/copilot/macros/<macro_id>.yaml`) with `checkpoint_after_step_indices` and optional overrides, so macros can diverge from a single routine and define checkpoints declaratively.
- **Dashboard UI**: surface macros.macros (available, last run, paused, awaiting approval) in the mission control / dashboard view.
- **human_checkpoint** step type: allow marking a step as requiring a human checkpoint in the macro definition and enforce pause before that step in the runner.
