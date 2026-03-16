# M23K — Operator-Approved Workday Copilot — Final Output

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `copilot_group` and commands: recommend, plan, run, reminders, report. |
| `src/workflow_dataset/mission_control/state.py` | Added block 8: **copilot** (recommended_jobs_count, recommended_job_ids, blocked_jobs_count, routines_count, recent_plan_runs_count, reminders_count, upcoming_reminders, next_copilot_action); local_sources["copilot"]. |
| `src/workflow_dataset/mission_control/report.py` | Added **[Copilot]** section: recommended_jobs, blocked, routines, plan_runs, reminders, next. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/copilot/__init__.py` | Package exports. |
| `src/workflow_dataset/copilot/config.py` | get_copilot_root, get_routines_dir, get_runs_dir, get_reminders_path (data/local/copilot). |
| `src/workflow_dataset/copilot/recommendations.py` | recommend_jobs(repo_root, limit) — explicit reasons (recent_successful_run, trusted_for_real, approval_blocked, simulate_only_available). |
| `src/workflow_dataset/copilot/routines.py` | Routine dataclass; list_routines, get_routine, save_routine, get_ordered_job_ids. |
| `src/workflow_dataset/copilot/plan.py` | PlanPreview; build_plan_for_job, build_plan_for_routine (no execution). |
| `src/workflow_dataset/copilot/run.py` | run_plan(plan, repo_root, stop_on_first_blocked, continue_on_blocked); list_plan_runs. Persist plan_run.json under runs/<plan_run_id>. |
| `src/workflow_dataset/copilot/reminders.py` | list_reminders, add_reminder, reminders_due; store reminders.yaml; no auto-run. |
| `src/workflow_dataset/copilot/report.py` | copilot_report, format_copilot_report. |
| `src/workflow_dataset/copilot/seed_copilot.py` | seed_morning_routine (weekly_status_from_notes). |
| `docs/M23K_READ_FIRST.md` | Pre-coding analysis. |
| `docs/M23K_COPILOT_OPERATOR.md` | Operator guide. |
| `docs/M23K_FINAL_OUTPUT.md` | This file. |
| `tests/test_copilot.py` | Tests: recommend, routine CRUD, plan for job/routine, run plan simulate, reminders, report. |

## 3. Exact CLI usage

```bash
workflow-dataset copilot recommend [--limit N] [--repo-root PATH]
workflow-dataset copilot plan --job <id> | --routine <id> [--mode simulate|real] [--repo-root PATH]
workflow-dataset copilot run --job <id> | --routine <id> [--mode simulate|real] [--repo-root PATH]
workflow-dataset copilot reminders list [--repo-root PATH]
workflow-dataset copilot reminders add [--routine ID] [--job ID] [--due-at ...] [--title ...] [--repo-root PATH]
workflow-dataset copilot reminders due [--repo-root PATH]
workflow-dataset copilot report [--repo-root PATH]
```

## 4. Sample recommendation output

```
Copilot recommendations
  weekly_status_from_notes  reason=recent_successful_run  mode=simulate_only
  replay_cli_demo  reason=simulate_only_available  mode=simulate_only
```

(With blocking: `job_id  reason=approval_blocked  mode=simulate_only` and below `blocking_issues` lines.)

## 5. Sample routine definition

```yaml
routine_id: morning_reporting
title: Morning reporting
description: Run weekly status from notes (single job).
job_pack_ids:
  - weekly_status_from_notes
ordering: null
stop_on_first_blocked: true
required_approvals: []
simulate_only: true
expected_outputs: []
```

## 6. Sample plan preview

```
Plan plan_abc123  mode=simulate
  job_pack_ids: ['weekly_status_from_notes']
  blocked: []
  Run with: copilot run --job ... or --routine ... --mode simulate
```

## 7. Sample copilot run output

```
Plan run cprun_xyz  executed=1  blocked=0
  run_path: .../data/local/copilot/runs/cprun_xyz
```

## 8. Sample reminder output

**reminders list:**
```
Reminders
  rem_0_2026-03-16  Morning check-in  due=09:00  routine=morning_reporting job=
```

**reminders due:** Same structure, limited to “due” list (currently returns up to limit reminders).

## 9. Exact tests run

```bash
pytest tests/test_copilot.py -v
```

7 passed: test_recommend_jobs, test_routine_crud, test_build_plan_for_job, test_build_plan_for_routine, test_run_plan_simulate, test_reminders, test_copilot_report.

## 10. What remains manual or simulate-only

- **Manual:** All copilot runs are triggered by the operator (copilot run, jobs run). Reminders do not auto-run.
- **Simulate-only by default:** Routines are created with simulate_only=true; real mode requires job-level eligibility and approval registry.
- **Task-demo-backed jobs:** Remain simulate-only; real mode refused for them.

## 11. Exact recommended next phase after M23K

- **Optional:** Add “recommended next action” in mission_control next_action when copilot has recommended_jobs and no higher-priority signal (e.g. “run copilot recommend” or “run copilot run --routine morning_reporting”).
- **Optional:** Parameter overrides for copilot run (e.g. `--param path=custom`) passed into plan and run_plan so multi-job plans can override params per job.
- **Optional:** Stale-reminder logic (e.g. due_at in the past) and “reminders due” filter by date if you add a simple local clock check.
- **Continue:** Use the copilot in daily workflows; keep all execution explicit and local; do not add background automation or cloud orchestration.
