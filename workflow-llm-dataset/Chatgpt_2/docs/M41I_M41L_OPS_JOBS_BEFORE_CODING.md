# M41I–M41L — Sustained Deployment Ops + Jobized Maintenance Loops: Before Coding

## 1. What operational/background structures already exist

- **automations/**: TriggerKind (time_based, event_based, project_state, …), TriggerDefinition, RecurringWorkflowDefinition (workflow_id, trigger_ids, planner_goal, execution_mode, stop_conditions), TriggerMatchResult. Templates, store, evaluate.
- **background_run/**: QueuedRecurringJob (automation_id, plan_ref, trigger_type, allowed_modes), BackgroundRun, BackgroundArtifact, FailureRetryState, RunSourceTrigger, ExecutionMode, ApprovalState. Runner: pick_eligible_job, run_one_background (simulate-first, optional real). Store: load_queue, save_run, load_history. Gating: evaluate_background_policy. Retry policies, recovery, degraded_fallback.
- **reliability/**: GoldenPathScenario, ReliabilityRunResult, RecoveryCase; list_path_ids, get_path, run_golden_path, classify_run_result; save_run, load_latest_run, list_runs; recovery_playbooks (suggest_recovery, get_recovery_guide); degraded_profiles, fallback_matrix.
- **support/release_readiness**: build_release_readiness, build_supportability_report, build_handoff_pack, SupportedWorkflowScope, ReleaseBlocker.
- **triage/**: list_issues, list_evidence, build_cohort_health_summary, build_all_clusters, get_playbook_for_cluster, get_operator_do_now_for_cluster.
- **cohort/**: bindings, profiles, gates, transitions, explain.
- **release/**: dashboard_data, reporting_workspaces, handoff_profiles, staging_board.
- **deploy_bundle/**: get_deployment_bundle, validate_bundle, build_deployment_health_summary, build_maintenance_mode_report.
- **production_launch/**: build_production_review_cycle, build_sustained_use_checkpoint, build_post_deployment_guidance, build_ongoing_production_summary, build_launch_decision_pack, review_cycles, sustained_use.
- **mission_control/**: get_mission_control_state, format_mission_control_report (product, evaluation, development, incubator, coordination, desktop_bridge, live_context, triage, vertical_packs, deploy_bundle, production_launch, in_flow, …).

No dedicated “learning lab” or “council” package found in workflow_dataset; Pane 1/Pane 2 may add them elsewhere.

---

## 2. What useful job/research-loop patterns were found (Karpathy)

**karpathy/jobs (BLS data pipeline):**
- Clear **staged pipeline**: scrape → parse → tabulate → score → build; each stage is a script with defined inputs/outputs.
- **Outputs in known paths**: html/, pages/, occupations.csv, scores.json, site/data.json.
- **Repeatable steps**: Same commands produce same-shaped outputs; pipeline is re-runnable.
- **Single “job” abstraction**: Here “job” = occupation record; the useful part is the **pipeline stage** as a unit of work with a command and output contract.

**karpathy/autoresearch:**
- **Fixed time budget** per run (5 min); makes runs comparable and predictable.
- **Result logging**: results.tsv; each run produces a comparable metric (val_bpb).
- **Keep/discard by metric**: improved → keep; not improved → revert.
- **Repeatable loop**: read program → modify → run → check → log → repeat (human/agent controlled).
- **Single file / bounded scope**: One train.py to modify; keeps scope manageable.

---

## 3. Which ideas fit the product safely

- **Staged, repeatable maintenance steps**: Map each “ops job” to one or more existing calls (reliability run, triage health, deploy_bundle validate, supportability, review cycle). No new execution engine; ops job = structured wrapper + cadence + history.
- **Clear output contract**: Job output = dict with outcome, duration_seconds, output_refs (e.g. triage report path, reliability run id), linked_surfaces (triage, council, support).
- **Cadence and “due”**: Interval (e.g. daily, weekly) + last_run_utc → next_due; “due” and “overdue” for reporting.
- **Fixed or max duration hint**: Optional max_duration_seconds per job type for “time budget” (advisory only; we don’t kill runs).
- **Result logging**: Append-only run history per job_id (run_id, started_utc, outcome, summary, output_refs).
- **Blocked/retryable**: Job can have prerequisites (e.g. deploy_bundle validation passed); blocked_reason and escalation_target (e.g. deploy-bundle recovery-report).
- **No code modification by agent**: Ops jobs only invoke existing CLI/APIs; no autonomous edits to code or config.

---

## 4. Which ideas should be rejected

- **Autonomous code modification** (autoresearch’s agent editing train.py): Out of scope; we do not allow ops jobs to modify source or config.
- **Infinite unsupervised loop**: Ops jobs are triggered by operator or by explicit schedule/cron; we do not run “forever” without operator visibility.
- **Cloud job orchestration**: No K8s, Step Functions, or cloud queues; local-first only.
- **Replacing background_run/automations**: We add an ops-job layer that *calls* existing systems; we do not replace QueuedRecurringJob or RecurringWorkflowDefinition.
- **Generic DevOps**: No generic “run any script” job; each ops job type is a defined maintenance/review/research loop that maps to existing product surfaces.

---

## 5. Exact file plan

| Action | Path |
|--------|------|
| Create | `src/workflow_dataset/ops_jobs/models.py` — OpsJob, MaintenanceJob (subtype or flags), JobCadence, JobPrerequisite, JobOutput, JobHealth, JobBlockedReason, JobEscalationTarget. |
| Create | `src/workflow_dataset/ops_jobs/registry.py` — BUILTIN_OPS_JOBS (reliability_refresh, queue_calmness_review, issue_cluster_review, adaptation_audit, production_cut_regression, vertical_value_review, supportability_refresh, operator_audit_review), get_ops_job, list_ops_job_ids. |
| Create | `src/workflow_dataset/ops_jobs/cadence.py` — next_due_utc(job_id, repo_root), list_due(repo_root), list_overdue(repo_root). |
| Create | `src/workflow_dataset/ops_jobs/runner.py` — run_ops_job(job_id, repo_root) → invokes existing APIs, returns JobOutput, appends to history. |
| Create | `src/workflow_dataset/ops_jobs/store.py` — append_run(job_id, run_result), get_last_run(job_id), list_run_history(job_id, limit), get_ops_jobs_dir. |
| Create | `src/workflow_dataset/ops_jobs/report.py` — build_ops_maintenance_report(repo_root): next_due, blocked, overdue, recent_outcome, recommended_action. |
| Create | `src/workflow_dataset/ops_jobs/__init__.py` — Re-exports. |
| Modify | `src/workflow_dataset/cli.py` — Add ops-jobs: list, due, run --id, history --id, explain --id. |
| Modify | `src/workflow_dataset/mission_control/state.py` — Add ops_jobs_state: next_due_job_id, blocked_job_id, overdue_job_ids, recent_outcome, recommended_action. |
| Modify | `src/workflow_dataset/mission_control/report.py` — Add [Ops jobs] section. |
| Create | `tests/test_ops_jobs.py` — Model, cadence, run (mock or integration), history, blocked, report. |
| Create | `docs/samples/M41_ops_job_sample.json`, `M41_ops_due_history_sample.json`, `M41_ops_maintenance_report_sample.json`. |
| Create | `docs/M41I_M41L_OPS_JOBS_DELIVERABLE.md` — Files, mapping table (Karpathy → adopted/rejected), samples, tests, gaps. |

---

## 6. Safety/risk note

- Ops jobs only call existing workflow_dataset APIs (reliability, triage, deploy_bundle, release_readiness, production_launch). No new sandbox, no arbitrary script execution, no network beyond what those modules use.
- Run history is append-only and stored under data/local/ops_jobs. No PII; only job_id, timestamps, outcome, summary, output_refs.
- Cadence is advisory (“due” / “overdue”); no automatic execution without operator or explicit cron/scheduler. If a future step adds cron, it should invoke the same run_ops_job entry point with operator visibility.

---

## 7. What this block will NOT do

- Will not replace or duplicate background_run/automations; will not add cloud orchestration.
- Will not implement unsupervised self-improvement or agent-driven code/config changes.
- Will not add generic “run any command” jobs; only defined job types with fixed surface linkage.
- Will not enforce hard time limits (e.g. killing runs after N seconds); max_duration_seconds is advisory for reporting only.
