# M23L — Work State Engine + Context-Aware Trigger Policies — Read First

## 1. What already exists for job recommendations, routines, reminders, and approvals

- **Copilot (M23K):**
  - **Recommendations:** `recommend_jobs(repo_root, limit)` → list of dicts with `recommendation_id`, `job_pack_id`, `reason` (recent_successful_run, trusted_for_real, approval_blocked, simulate_only_available), `trust_level`, `mode_allowed`, `blocking_issues`, `recommended_timing_context`. Reasons are explicit; no context/timing beyond job_packs_report.
  - **Routines:** `Routine` dataclass; `list_routines`, `get_routine`, `save_routine`, `get_ordered_job_ids`. Stored under `data/local/copilot/routines/*.yaml`.
  - **Reminders:** `list_reminders`, `add_reminder`, `reminders_due`; storage in `reminders.yaml`. No auto-run.
  - **Plan / run:** `build_plan_for_job`, `build_plan_for_routine` → `PlanPreview`; `run_plan(plan, repo_root)` records under `copilot/runs/<run_id>/plan_run.json`.
- **Job packs (M23J):** `job_packs_report` (recent_successful, trusted_for_real_jobs, approval_blocked_jobs, simulate_only_jobs); `job_diagnostics`; `check_job_policy`; specialization memory (last_successful_run, preferred_params).
- **Approvals:** `capability_discovery/approval_registry` — `load_approval_registry` (approved_paths, approved_apps, approved_action_scopes); mission_control state already pulls desktop_bridge (approvals_path, approved_paths_count, etc.).
- **Mission control:** state block 8 **copilot** (recommended_jobs_count, blocked_jobs_count, routines_count, recent_plan_runs_count, reminders_count, next_copilot_action); report has [Copilot] section. `recommend_next_action` does not yet use copilot context (it uses eval, devlab, incubator, cohort, review, task demos).

## 2. What local signals already exist that can inform context

- **Job / specialization:** `job_packs_report` (recent_successful with run_id/timestamp, trusted/blocked/simulate-only); `load_specialization` (last_successful_run, preferred_params, recurring_failure_notes); `job_diagnostics` (policy_simulate, policy_real).
- **Intake:** `list_intakes` (label, input_type, snapshot_dir, file_count, created_at); `intake_report(label)` (file_inventory, parse_summary, suggested_workflows). No “last modified” on intake snapshots unless we use filesystem mtime on snapshot dirs.
- **Workspace / package / review:** `get_dashboard_data` → `recent_workspaces` (workspace_path, workflow, timestamp, status, artifact_count, package_ready, etc.); `review_package` (unreviewed_count, package_pending_count); staging. Mission_control state already has product_state.recent_workspaces_count, review_package.
- **Approvals / capabilities:** `load_approval_registry`; desktop_adapters `list_adapters`; mission_control desktop_bridge (adapter_ids, approvals_file_exists, approved_paths_count, approved_action_scopes_count).
- **Task demos / coordination:** `list_tasks`, `get_task`; coordination_graph summary (tasks_count, total_nodes, total_edges). Mission_control already aggregates these.
- **Copilot-specific:** `list_plan_runs` (recent runs); `list_reminders`, `reminders_due`; `list_routines`. No “last context refresh” or “work state snapshot” yet.
- **Eval / devlab / incubator:** Board report, proposal queue, incubator candidates — already in mission_control state; can be folded into a “work state” snapshot as read-only aggregates.

None of these are currently combined into a single **work-state snapshot** or **context snapshot** that answers “what is the current working context?” or “why recommend this job now?”. Recommendations today are based only on job_packs_report categories, not on intake changes, reminder due, or workspace/review state.

## 3. Current gap between “copilot” and “context-aware copilot”

- **No work-state model:** There is no single snapshot that represents “current work context” (active job context, recent intake, recent workspace/review, available approvals, reminders due, recent runs, blocked conditions).
- **No context refresh:** No explicit “refresh context” or “context show” or “context compare”; no persisted context snapshots to compare over time.
- **No trigger policies:** Jobs/routines are recommended by static buckets (recent_successful, trusted_for_real, approval_blocked, simulate_only). There are no rules like “recommend when intake X changed”, “recommend when reminder due”, “block when capability missing”, “recommend when related workspace incomplete”.
- **No “why now?”:** Recommendation output has `reason` and `recommended_timing_context` but no evidence from current context (e.g. “intake notes_mar15 updated”, “reminder morning_reporting due”, “approval just satisfied”).
- **No context in mission control:** Mission control shows copilot counts and next_copilot_action but not work-state summary, context-derived recommendations, or “newly relevant because of X”.
- **No context history/drift:** No comparison of “what changed since last snapshot” (newly recommendable, newly blocked, approval/capability drift).

Filling this gap requires: (1) a local work-state model and snapshot persistence, (2) context refresh/show/compare, (3) trigger policy evaluation, (4) recommendation explanation that uses context, (5) mission control context panels, (6) context history/drift.

## 4. Exact file plan

| Module | Files | Purpose |
|--------|-------|--------|
| A — Analysis | docs/M23L_READ_FIRST.md | This document. |
| B — Work-state model | context/work_state.py | WorkState dataclass/schema; build_work_state(repo_root) from job_packs_report, list_intakes, get_dashboard_data (recent_workspaces, review_package), approval_registry, copilot (reminders_due, list_plan_runs, list_routines), task_demos count. Snapshot = serializable dict; write work_state.json + work_state_summary.md. |
| B — Config | context/config.py | get_context_root(repo_root) → data/local/context; get_snapshots_dir(), get_latest_snapshot_path(), get_previous_snapshot_path(). |
| C — Snapshot persistence | context/snapshot.py | save_snapshot(work_state, repo_root); load_snapshot(snapshot_id or "latest", repo_root); list_snapshots(limit, repo_root). Naming: snapshot_<iso_ts>.json or latest.json copy. |
| C — Context CLI | cli.py (add context group) | context refresh, context show [--snapshot latest], context compare --latest --previous. |
| D — Trigger policies | context/triggers.py | TriggerPolicy: trigger_type (intake_changed, reminder_due, approval_present, capability_missing, trust_too_low, previous_job_succeeded, workspace_incomplete); evaluate_trigger_for_job(job_id, work_state, repo_root), evaluate_trigger_for_routine(routine_id, work_state, repo_root); evaluate_all_triggers(work_state, repo_root) → list of {job_or_routine_id, type, triggered, reason, blocker}. Explicit reasoning; no auto-run. |
| E — Why-now recommendation | copilot/recommendations.py (extend) + context/recommendation_explain.py | recommend_jobs(..., context_snapshot=None) merges trigger evaluation: add why_now_evidence, context_trigger. New: explain_recommendation(rec_id, repo_root) or explain_recommendation_by_job(job_id, repo_root) using latest work state + trigger eval. CLI: copilot recommend --context latest; copilot explain-recommendation --id <rec_id>. |
| F — Mission control | mission_control/state.py, report.py | state["work_context"] or state["context"]: work_state_summary (or ref to latest snapshot), context_recommendations_count, context_blocked_count, newly_relevant_jobs, approvals_expiring_or_missing, recent_state_changes (from compare), next_recommended_action. Report: [Context] or [Work context] section (additive). |
| G — Context history/drift | context/drift.py | compare_snapshots(snap_a, snap_b) → {newly_recommendable, newly_blocked, approvals_changed, capabilities_changed, intake_changed, ...}. Persist last snapshot id in state or snapshot_meta so “previous” is well-defined. |
| H — Docs | docs/M23L_WORK_STATE_OPERATOR.md | What work-state engine is, inputs, how context-aware recommendations work, what stays manual, privacy/local-first. |
| H — Tests | tests/test_context.py | Work-state build, snapshot save/load, trigger evaluation, recommendation with context, explain_recommendation, context compare/drift, mission_control context block. |
| Final | docs/M23L_FINAL_OUTPUT.md | Files modified/created, CLI, sample outputs, tests, what remains manual, next phase. |

## 5. Safety/risk note

- **No background monitoring:** Context refresh is explicit (operator runs `context refresh`). No daemon or file watcher by default; any future “scheduled refresh” must be opt-in and stoppable.
- **No auto-run:** Trigger policies only affect **recommendation** and **explanation**. They do not trigger execution; execution remains `copilot run` / `jobs run` only.
- **Local-only:** All context data under `data/local/context` (snapshots, no cloud). Work state is derived from existing local sources (job_packs, intake, dashboard_data, approval_registry, copilot).
- **Inspectable:** Work-state snapshot and trigger results are JSON/MD; operator can inspect why a job is “recommended now” or blocked.
- **No new approval bypass:** Trigger evaluation uses existing check_job_policy and approval registry; no new path to run real mode without approval.
