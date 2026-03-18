# M41I–M41L — Sustained Deployment Ops + Jobized Maintenance Loops: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `ops_jobs_group` as `ops-jobs` with commands: `list`, `due`, `run --id`, `history --id`, `explain --id`, `report` (optional `--repo`, `--json`). |
| `src/workflow_dataset/mission_control/state.py` | Added `ops_jobs_state` block: `next_due_job_id`, `blocked_job_id`, `overdue_job_ids`, `highest_value_overdue_id`, `recent_outcome_*`, `recommended_action`; `local_sources["ops_jobs"]`. |
| `src/workflow_dataset/mission_control/report.py` | Added **[Ops jobs]** section: next_due, blocked, overdue, recent outcome, recommended action. |
| `src/workflow_dataset/ops_jobs/cadence.py` | Jobs with no prior run are treated as due (next_due_utc returns now). |

---

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/ops_jobs/models.py` | OpsJob, JobCadence, JobPrerequisite, JobBlockedReason, JobEscalationTarget, JobOutput, JobHealth. |
| `src/workflow_dataset/ops_jobs/registry.py` | BUILTIN_OPS_JOBS (reliability_refresh, queue_calmness_review, issue_cluster_review, adaptation_audit, production_cut_regression, vertical_value_review, supportability_refresh, operator_audit_review), get_ops_job, list_ops_job_ids. |
| `src/workflow_dataset/ops_jobs/store.py` | data/local/ops_jobs/history.json, last_run.json; append_run, get_last_run, list_run_history, get_ops_jobs_dir. |
| `src/workflow_dataset/ops_jobs/cadence.py` | next_due_utc, list_due, list_overdue. |
| `src/workflow_dataset/ops_jobs/runner.py` | run_ops_job(job_id, repo_root) → JobOutput; dispatches by run_command to reliability_run, queue_summary, triage_health, etc.; appends to history. |
| `src/workflow_dataset/ops_jobs/report.py` | build_ops_maintenance_report(repo_root): next_due_job_id, due_jobs, overdue_jobs, blocked_job_id, highest_value_overdue_id, recent_outcome, recommended_action. |
| `src/workflow_dataset/ops_jobs/__init__.py` | Re-exports models, registry, store, cadence, runner, report. |
| `tests/test_ops_jobs.py` | Model, cadence/due, run_ops_job, history, blocked, report, unknown job. |
| `docs/samples/M41_ops_job_sample.json` | Sample OpsJob (reliability_refresh) as JSON. |
| `docs/samples/M41_ops_due_history_sample.json` | Sample due list + one job’s run history. |
| `docs/samples/M41_ops_maintenance_report_sample.json` | Sample build_ops_maintenance_report output. |
| `docs/M41I_M41L_OPS_JOBS_BEFORE_CODING.md` | Pre-implementation analysis (existing structures, Karpathy patterns, adopted/rejected, file plan, safety, “what this block will NOT do”). |
| `docs/M41I_M41L_OPS_JOBS_DELIVERABLE.md` | This file. |

---

## 3. Exact mapping: Karpathy ideas → adopted / rejected

| Source | Idea | Adopted / Rejected | Notes |
|--------|------|--------------------|--------|
| karpathy/jobs | Staged pipeline with defined inputs/outputs | **Adopted** (pattern only) | Ops job = one unit of work with run_command and output contract (outcome, output_refs, linked_surfaces). |
| karpathy/jobs | Outputs in known paths | **Adopted** (pattern only) | output_refs and linked_surfaces point to triage, reliability, deploy_bundle, etc.; history in data/local/ops_jobs. |
| karpathy/jobs | Repeatable steps; same command → same-shaped output | **Adopted** | run_ops_job(id) always calls same underlying API; JobOutput shape is fixed. |
| karpathy/jobs | Single “job” abstraction (pipeline stage as unit) | **Adopted** | OpsJob is the unit; cadence + last_run → due/overdue. |
| karpathy/autoresearch | Fixed time budget per run | **Adopted** (advisory) | max_duration_seconds per job type; we do not kill runs. |
| karpathy/autoresearch | Result logging | **Adopted** | Append-only run history (run_id, started_utc, outcome, summary, output_refs). |
| karpathy/autoresearch | Keep/discard by metric | **Rejected** | No autonomous keep/revert; operator decides. |
| karpathy/autoresearch | Repeat loop: read → modify → run → check | **Rejected** (modify) | Ops jobs do not modify code or config; they only invoke read/run/check. |
| karpathy/autoresearch | Single file / bounded scope | **Adopted** (spirit) | Each job type maps to a bounded set of existing APIs. |
| Both | Cloud / external orchestration | **Rejected** | Local-first only; no K8s, Step Functions, or cloud queues. |
| Both | Unsupervised infinite loop | **Rejected** | Runs are operator- or cron-triggered; no hidden self-improvement. |
| N/A | Replace background_run/automations | **Rejected** | Ops layer calls existing systems; does not replace QueuedRecurringJob or RecurringWorkflowDefinition. |
| N/A | Generic “run any script” job | **Rejected** | Only defined job types with fixed surface linkage. |

---

## 4. Sample ops job

See `docs/samples/M41_ops_job_sample.json`. One full `OpsJob` (reliability_refresh) as produced by `to_dict()`: job_id, name, description, job_class, cadence, prerequisites, run_command, run_command_args, max_duration_seconds, output_surfaces, escalation_targets, blocked_reasons, retryable.

---

## 5. Sample due / history output

- **Due list**: `workflow-dataset ops-jobs due` (or `due --json`) yields list of jobs due now with job_id, next_due_utc, name.
- **History**: `workflow-dataset ops-jobs history --id reliability_refresh` yields run history for that job.

See `docs/samples/M41_ops_due_history_sample.json` for an example due list and one job’s run history (reliability_refresh with two past runs).

---

## 6. Sample ops maintenance report

See `docs/samples/M41_ops_maintenance_report_sample.json`. Structure matches `build_ops_maintenance_report(repo_root)`:

- `next_due_job_id`, `due_jobs`, `overdue_jobs`, `blocked_job_id`, `highest_value_overdue_id`, `recent_outcome`, `recommended_action`.

CLI: `workflow-dataset ops-jobs report` (or `report --json`). Mission control: `workflow-dataset mission-control report` includes **[Ops jobs]** with next_due, blocked, overdue, recent outcome, recommended action.

---

## 7. Exact tests run

```bash
cd workflow-llm-dataset && python3 -m pytest tests/test_ops_jobs.py -v
```

**Scope:**

- **test_ops_job_model**: get_ops_job("reliability_refresh"), job_class, cadence, prerequisites, run_command, to_dict.
- **test_cadence_and_due**: next_due_utc (temp dir, no prior run → due), list_due, list_overdue.
- **test_run_ops_job**: run_ops_job("queue_calmness_review") in temp dir; outcome in pass/fail/blocked; get_last_run.
- **test_history**: append_run + list_run_history for issue_cluster_review.
- **test_blocked_behavior**: reliability_refresh has retryable and blocked_reasons.
- **test_report**: build_ops_maintenance_report; keys next_due_job_id, due_jobs, recommended_action; recommended_action contains "workflow-dataset ops-jobs".
- **test_unknown_job**: get_ops_job("nonexistent") → None; run_ops_job("nonexistent") → outcome blocked, summary mentions not found/Unknown.

All 7 tests are expected to pass (no mocks; uses temp dirs for store).

---

## 8. Remaining gaps for later refinement

- **Overdue vs due**: Currently list_overdue is aligned with list_due (due now); a future refinement can treat “past next_due_utc” as strictly overdue for display/priority.
- **Priority ordering**: highest_value_overdue_id is “first overdue”; no explicit priority field on jobs yet; can add later (e.g. critical vs routine).
- **Cron/scheduler**: No cron or systemd unit included; operator or external scheduler can call `workflow-dataset ops-jobs run --id <job_id>`.
- **Prerequisite checks in runner**: reliability_refresh checks install via subprocess; other jobs do not yet run prerequisite checks before run (only blocked state from last run is used in report).
- **Job output refs**: Runner sets output_refs when underlying APIs return paths/ids; not all run_commands populate output_refs yet.
- **Council / learning-lab**: If Pane 1/Pane 2 add council or learning-lab surfaces, new job types or output_surfaces can be added without changing the ops_jobs model.
- **Rejected-pattern tests**: test_unknown_job covers “unknown job → blocked”; no explicit test that ops jobs never invoke arbitrary code or cloud APIs (covered by design and code review).
