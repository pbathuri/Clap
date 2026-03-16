# M23J — Personal Job Packs + Specialization Memory — Read First

## 1. What already exists for task replay, trust, and approvals

- **Task demos:** task_demos/store (list_tasks, get_task, save_task), task_demos/replay (replay_task_simulate only). Steps: adapter_id, action_id, params. No parameter schema or user preferences.
- **Desktop benchmark:** desktop_bench/schema (DesktopBenchmarkCase: benchmark_id, title, task_category, required_adapters, required_approvals, real_mode_eligibility, steps, task_id). desktop_bench/harness (run_benchmark, run_suite with mode simulate|real; approvals_checked, outcome, provenance). desktop_bench/trusted_actions (TRUSTED_ADAPTER_ACTIONS, get_trusted_real_actions). desktop_bench/scoring (trust_status: trusted | usable_with_simulation_only | approval_missing | experimental).
- **Approvals:** capability_discovery/approval_registry (load/save approvals.yaml; approved_paths, approved_action_scopes). approval_check (check_execution_allowed gates run_execute).
- **Mission control:** state includes desktop_bridge (adapters_count, approvals_path, tasks_count, etc.); report shows [Desktop bridge]; next_action can recommend replay_task.

## 2. What can be reused for persistent local memory

- **Storage pattern:** Same as task_demos and desktop_bench: data/local/<dir> with YAML/JSON per entity (e.g. data/local/job_packs/*.yaml for pack definitions, data/local/job_packs/<id>/specialization.yaml for memory).
- **Execution path:** Job run can resolve to (1) task_id → replay_task_simulate or (2) benchmark_case_id → run_benchmark with resolved params. Reuse run_simulate/run_execute and approval_check; add job-level policy (simulate_only, trusted_for_real, approval_required_every_run, etc.).
- **Provenance:** Reuse run manifest shape (run_id, mode, outcome, approvals_checked, timestamp); store job run ref in job pack’s last_run or in a job_runs dir.
- **Setup/personal patterns:** setup/job_store uses JSON per job in a dir; personal/graph_store uses SQLite. For job packs we keep simple: one YAML per job pack, one specialization file per job pack, optional job_runs index.

## 3. Exact gap between trusted benchmarked actions and reusable personal jobs

- **No first-class job pack:** No entity that has title, description, source (task_id or benchmark_id), parameter schema, trust policy, and version.
- **No specialization memory:** No per-job store for preferred params, preferred paths, last successful run, operator corrections, or confidence notes.
- **No parameterized job execution:** Benchmarks and tasks use fixed params in the case/task file; no “run job with param notes_dir=…” with validation and defaults from specialization.
- **No job-level trust/approval policy:** No declare simulate-only vs trusted-for-real vs approval-required-every-run; no check “does this run exceed approved scope?” at job level.
- **No operator surface:** No “jobs list/show/run”, “show specialization”, “show last run / trust level”, or “recommended personal jobs” in mission control.
- **No explicit learning rules:** No rule that “specialization updates only from operator-confirmed successful run or explicit save-as-preferred”.

## 4. File plan

| Module | Files | Purpose |
|--------|-------|--------|
| B — Schema | job_packs/schema.py, job_packs/config.py | JobPack model (job_pack_id, title, description, category, source: task_id | benchmark_id, required_adapters, required_approvals, simulate_support, real_mode_eligibility, parameter_schema, expected_outputs, trust_level, trust_notes, created_at, updated_at, version). Config: data/local/job_packs. |
| C — Specialization | job_packs/specialization.py | SpecializationMemory (preferred_params, preferred_paths, preferred_apps, last_successful_run, recurring_failure_notes, operator_notes, updated_at). load/save per job; update only via explicit functions (from_successful_run, from_operator_override, save_as_preferred). |
| D — Execution | job_packs/execute.py | resolve_params(job, specialization, cli_params) → validated params; run_job(job_id, mode, params, repo_root) → run via task replay or benchmark harness; policy check before run; preview. |
| E — Policy | job_packs/policy.py | Job trust policy: simulate_only, trusted_for_real, approval_required_every_run, approval_valid_for_scope, experimental. check_job_policy(job, mode, params, repo_root) → (allowed, message). |
| F — Store + report | job_packs/store.py, job_packs/report.py | list_jobs, get_job, save_job; report (most-used, most-trusted, simulate-only, approval-blocked, failures, ready for benchmark); diagnostics(job_id). |
| Mission control | mission_control/state.py, report.py | Add job_packs summary (count, recent_successful, needing_approval_refresh); optional next_action branch. |
| CLI | cli.py | jobs list, show, run (--id, --mode, --param), report, diagnostics, specialization show/save-as-preferred. |
| G — Docs + tests | docs/M23J_JOB_PACKS_OPERATOR.md, tests/test_job_packs.py | What is a job pack, how it differs from task demo, specialization rules, trust, tests. |

## 5. Safety/risk note

- **No hidden learning:** Specialization memory is updated only when (1) operator confirms successful run, (2) operator runs “save as preferred”, (3) explicit “promote from benchmark” flow. No updates from failed runs or background inference.
- **Job-level policy enforced:** Before run, check trust policy (simulate_only → refuse real; approval_required_every_run → require registry; scope check via existing approval_check).
- **Local-only:** All job packs and specialization under data/local/job_packs; no cloud sync.
- **Inspectable:** Job pack and specialization files are YAML/JSON; operator can review and edit.
- **No new automation surface:** Job execution reuses desktop_bench/task_demos and approval_check; we do not add new adapters or bypass approval.
