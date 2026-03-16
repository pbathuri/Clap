# M23J — Personal Job Packs + Specialization Memory — Final Output

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `jobs_group` and commands: list, show, run, report, diagnostics, specialization-show, save-as-preferred, seed. |
| `src/workflow_dataset/mission_control/state.py` | Added block 7: **job_packs** (total, job_pack_ids, simulate_only_count, trusted_for_real_count, approval_blocked_count, recent_successful_count); local_sources["job_packs"]. |
| `src/workflow_dataset/mission_control/report.py` | Added **[Job packs]** section: total, simulate_only, trusted_for_real, approval_blocked, recent_successful. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/job_packs/__init__.py` | Package exports. |
| `src/workflow_dataset/job_packs/config.py` | get_job_packs_root, get_job_pack_path, get_specialization_path, get_job_runs_dir (data/local/job_packs). |
| `src/workflow_dataset/job_packs/schema.py` | JobPack, JobPackSource; load_job_pack, list_job_packs, get_job_pack; job_pack_to_dict. |
| `src/workflow_dataset/job_packs/specialization.py` | SpecializationMemory; load_specialization, save_specialization; update_from_successful_run, update_from_operator_override, save_as_preferred. |
| `src/workflow_dataset/job_packs/policy.py` | check_job_policy(job, mode, params, repo_root); TrustLevel; refuse real for simulate_only, require registry for real. |
| `src/workflow_dataset/job_packs/execute.py` | resolve_params, preview_job, run_job (via task_demo replay or benchmark run); optional update_specialization_on_success. |
| `src/workflow_dataset/job_packs/store.py` | save_job_pack. |
| `src/workflow_dataset/job_packs/report.py` | job_packs_report, job_diagnostics, format_job_packs_report. |
| `src/workflow_dataset/job_packs/seed_jobs.py` | seed_example_job_pack (weekly_status_from_notes), seed_task_demo_job_pack (replay_cli_demo). |
| `docs/M23J_READ_FIRST.md` | Pre-coding analysis. |
| `docs/M23J_JOB_PACKS_OPERATOR.md` | Operator guide. |
| `docs/M23J_FINAL_OUTPUT.md` | This file. |
| `tests/test_job_packs.py` | Tests for job packs and specialization. |

## 3. Exact CLI usage

```bash
workflow-dataset jobs list [--repo-root PATH]
workflow-dataset jobs show --id <job_pack_id> [--repo-root PATH]
workflow-dataset jobs run --id <job_pack_id> --mode simulate|real [--param k=v ...] [--update-specialization] [--repo-root PATH]
workflow-dataset jobs report [--repo-root PATH]
workflow-dataset jobs diagnostics --id <job_pack_id> [--repo-root PATH]
workflow-dataset jobs specialization-show --id <job_pack_id> [--repo-root PATH]
workflow-dataset jobs save-as-preferred --id <job_pack_id> --param k=v [--param k2=v2 ...] [--repo-root PATH]
workflow-dataset jobs seed [--repo-root PATH]
```

## 4. Sample job pack definition

```yaml
job_pack_id: weekly_status_from_notes
title: Weekly status from notes
description: Inspect local folder and list contents; backed by benchmark inspect_folder_basic.
category: reporting
source:
  kind: benchmark_case
  ref: inspect_folder_basic
required_adapters: [file_ops]
required_approvals: []
simulate_support: true
real_mode_eligibility: true
parameter_schema:
  path:
    type: string
    default: data/local
    required: true
trust_level: experimental
trust_notes: Backed by desktop benchmark inspect_folder_basic.
version: "1"
```

## 5. Sample specialization memory state

```yaml
job_pack_id: weekly_status_from_notes
preferred_params:
  path: data/local
preferred_paths: []
preferred_apps: []
operator_notes: ""
last_successful_run:
  run_id: abc123
  timestamp: "2026-03-16T12:00:00Z"
  params_used: { path: data/local }
  outcome: pass
recurring_failure_notes: []
confidence_notes: ""
updated_at: "2026-03-16T12:00:00Z"
update_history:
  - at: "2026-03-16T12:00:00Z"
    source: successful_run
    summary: "run_id=abc123 outcome=pass"
```

## 6. Sample job run output

```
Resolved params: {'path': 'data/local'}
Policy: allowed
Job weekly_status_from_notes outcome=pass run_id=3e1474e003106cae6db4
```

## 7. Sample diagnostics/report output

**jobs report:**
```
=== Job packs report (M23J) ===

Total jobs: 2
Simulate-only: ['replay_cli_demo']
Trusted for real: []
Approval-blocked (real): []
Jobs with failure notes: []

Recent successful:
  weekly_status_from_notes run=3e14... 2026-03-16T...
```

**jobs diagnostics --id weekly_status_from_notes:**
```
Weekly status from notes (weekly_status_from_notes)
  trust_level: experimental  real_mode_eligibility: True
  policy_simulate: allowed=True  
  policy_real: allowed=False  Real mode requires approval registry...
```

## 8. Exact tests run

```bash
pytest tests/test_job_packs.py -v
```

10 passed, 1 skipped (replay_cli_demo when task cli_demo not present). Tests: seed/list, get_job_pack, specialization persistence, update_from_successful_run, resolve_params, check_job_policy (simulate_only), preview_job, run_job (simulate benchmark), run_job task_demo (skipped if no task), job_packs_report, job_diagnostics.

## 9. What remains benchmark-only or simulate-only

- **Benchmark-only:** Desktop benchmark cases are still the canonical definitions for desktop_bridge_core; job packs reference them and do not replace them.
- **Simulate-only:** Task-demo-backed jobs (source kind task_demo); jobs with trust_level=simulate_only or real_mode_eligibility=false; browser_open and app_launch adapter actions.

## 10. Exact recommended next phase after M23J

- **Optional:** Map job parameter_schema to benchmark step params so that `jobs run --param path=custom` overrides step params when the source is a benchmark_case (e.g. inject path into steps that have a `path` param).
- **Optional:** Add “recommended personal jobs” or “jobs needing approval refresh” to mission_control next_action when job_packs.approval_blocked_count > 0.
- **Continue:** Use job packs in operator workflows; keep specialization updates explicit and local; do not add hidden learning or autonomous scheduling.
