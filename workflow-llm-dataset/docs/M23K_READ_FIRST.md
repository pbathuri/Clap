# M23K — Operator-Approved Workday Copilot — Read First

## 1. What already exists for jobs, trust, approvals, and diagnostics

- **Job packs (M23J):** list_job_packs, get_job_pack, load_specialization, run_job, preview_job; check_job_policy (simulate_only, real_mode_eligibility, registry); job_packs_report (simulate_only_jobs, trusted_for_real_jobs, approval_blocked_jobs, recent_successful); job_diagnostics (policy_simulate, policy_real).
- **Trust/approvals:** capability_discovery/approval_registry (approved_paths, approved_action_scopes); approval_check gates run_execute; desktop_bench/trusted_actions (get_trusted_real_actions, ready_for_real).
- **Mission control:** state includes job_packs (total, simulate_only_count, trusted_for_real_count, approval_blocked_count, recent_successful_count); report has [Job packs] line; next_action recommends replay_task when tasks exist.

## 2. What can already be surfaced as a daily/operator queue

- **Recommended jobs:** recent_successful from job_packs_report; trusted_for_real_jobs; approval_blocked_jobs (as “needs approval”); simulate_only_jobs (as “simulate-only options”). No explicit “recommendation id” or “why” yet.
- **Blocked/eligible:** job_diagnostics per job gives policy_simulate and policy_real; we can derive “recommended” = recent success or trusted, “blocked” = approval_blocked or policy_real not allowed.
- **Queue-like list:** list_job_packs + job_packs_report already give enough to build a list of “recommended” (recent_successful + trusted) and “blocked” (approval_blocked). Missing: explicit recommendation records with reason, timing, and mode_allowed.

## 3. What is still missing for a usable copilot layer

- **Recommendation model:** No first-class recommendation object (id, job_pack_id, reason, trust_level, mode_allowed, blocking_issues). No “recommend” command that returns an ordered list with explicit reasons.
- **Routines/bundles:** No routine entity (routine_id, title, job_pack_ids, ordering, required_approvals, simulate/real eligibility). No “run routine” or “plan for routine.”
- **Plan preview:** No plan object (which jobs/routine, order, mode, approvals required, expected outputs, blocked items). No `copilot plan --job X` or `copilot plan --routine Y`.
- **Approved execution:** run_job exists but no “plan run” that executes a multi-job plan and records plan_id, approvals_checked, actions, blocked/skipped. No plan-run record store.
- **Reminders/schedule:** No reminder or schedule-proposal entity (routine_id or job_id, due/at, one-off vs recurring). No reminders list/due or add. No hidden scheduler; reminders are explicit records and “due” is a list, not auto-run.
- **Mission control copilot section:** No copilot block in state (recommended_jobs, recommended_routines, blocked, upcoming_reminders, recent_plan_runs, next_copilot_action). Report has no [Copilot] section.
- **Reporting:** No copilot report (accepted/skipped recommendations, routine usage, blocked causes, simulate vs real plan-run mix, stale reminders).
- **Trust boundaries:** Policy is enforced per job in check_job_policy; no aggregate “plan” check or “routine contains untrusted step” diagnostic. Refusals are per-job; we need to surface them in plan preview and run.

## 4. File plan

| Module | Files | Purpose |
|--------|-------|--------|
| B — Recommendation | copilot/recommendations.py | recommend_jobs(repo_root) → list of {recommendation_id, job_pack_id, reason, trust_level, required_approvals, mode_allowed, blocking_issues}; explicit reasons from job_packs_report + specialization + policy. |
| C — Routines | copilot/routines.py, copilot/routine_store.py | Routine schema (routine_id, title, description, job_pack_ids, ordering, required_approvals, simulate_only); list_routines, get_routine, save_routine; data/local/copilot/routines. |
| D — Plan preview | copilot/plan.py | PlanPreview (plan_id, jobs_or_routine, order, mode, approvals_required, trusted_actions_involved, expected_outputs, blocked, blocked_reason); build_plan_for_job(job_id), build_plan_for_routine(routine_id); no execution. |
| E — Execution | copilot/run.py | run_plan(plan_id, mode, repo_root) → execute jobs in order; stop on first blocked unless override; record plan_run (plan_id, jobs, mode, approvals_checked, executed, blocked, timestamps); persist under data/local/copilot/runs. |
| F — Reminders | copilot/reminders.py | Reminder (reminder_id, routine_id or job_pack_id, due_at, one_off, title); list_reminders, add_reminder, reminders_due; store data/local/copilot/reminders.yaml; no auto-run. |
| G — Mission control | mission_control/state.py, report.py | state["copilot"] = {recommended_jobs, recommended_routines, blocked_count, upcoming_reminders, recent_plan_runs_count, next_copilot_action}; report [Copilot] section. |
| H — Report/docs | copilot/report.py, docs/M23K_COPILOT_OPERATOR.md | copilot_report (recommendations, accepted/skipped, routine_usage, blocked_causes, plan_run_mix, stale_reminders); operator doc. |
| I — CLI | cli.py | copilot recommend, copilot plan --job/--routine, copilot run --plan --mode, copilot reminders list/add/due, copilot report. |
| J — Tests | tests/test_copilot.py | recommend, routine CRUD, plan preview, run plan simulate, reminders, report. |

## 5. Safety/risk note

- **No autonomous execution:** Plans run only when operator runs `copilot run --plan <id> --mode simulate|real`. Reminders are “due” lists only; no background process runs them.
- **Explicit recommendations:** Recommendation reasons are derived from local data (recent_successful, trust_level, approval_blocked); no opaque ML ranking.
- **Routine = ordered job list:** Routine execution runs each job in order via existing run_job; same policy and approval checks apply per job.
- **Plan run record:** Every plan run is recorded (plan_id, mode, approvals_checked, executed/blocked); no silent skip without record.
- **Local-only:** All copilot data under data/local/copilot (routines, runs, reminders); no cloud.
