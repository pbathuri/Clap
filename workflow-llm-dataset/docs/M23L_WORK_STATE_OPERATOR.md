# M23L — Work state engine operator guide

What the work-state engine is, what inputs it uses, how recommendations become context-aware, what stays manual, and how privacy/local-first is preserved.

---

## 1. What the work-state engine is

The **work-state engine** is a local, on-demand snapshot of your current working context. It:

- **Aggregates** existing local data: job packs (recent success, trusted, blocked), intake labels, dashboard (workspaces, review/package counts), approval registry, copilot (reminders, routines, plan runs), task demos count.
- **Persists** snapshots under `data/local/context/snapshots/` and a `latest.json` copy for comparison.
- **Does not run in the background.** Refresh is explicit: `workflow-dataset context refresh`.
- **Feeds** context-aware recommendations: when you run `copilot recommend --context latest`, recommendations are enriched with “why now?” evidence from trigger evaluation.

---

## 2. What inputs it uses

All read-only, local:

- **Job packs:** `job_packs_report` (recent_successful, trusted_for_real_jobs, approval_blocked_jobs, simulate_only_jobs, jobs_with_failure_notes).
- **Intake:** `list_intakes` (labels, file_count, created_at).
- **Dashboard:** `get_dashboard_data` (recent_workspaces, review_package unreviewed/package_pending).
- **Approvals:** `load_approval_registry` (approved_paths, approved_action_scopes); `list_adapters`.
- **Copilot:** `list_reminders`, `reminders_due`, `list_routines`, `list_plan_runs`.
- **Task demos:** `list_tasks` count.

No cloud, no file watchers, no daemons.

---

## 3. How recommendations become context-aware

- **Without context:** `copilot recommend` uses only job_packs_report buckets (recent_successful_run, trusted_for_real, approval_blocked, simulate_only_available).
- **With context:** `copilot recommend --context latest` loads the latest work-state snapshot and runs **trigger policies** per job (and optionally routine). Triggers include: previous_job_succeeded, approval_present, approval_blocked, simulate_only, reminder_due, intake_available, routine_defined. Each recommendation gets:
  - **why_now_evidence:** short reasons (e.g. “Reminder due for this job”, “Intake sets available”).
  - **context_trigger:** trigger type names that fired.
- **Explain:** `copilot explain-recommendation --id <rec_id>` or `--job <job_id>` prints why that job is recommended now (trigger results, blockers, approvals).

---

## 4. What is still manual

- **Context refresh:** You run `context refresh` when you want an up-to-date snapshot. Nothing refreshes automatically by default.
- **Running jobs/routines:** Context and triggers only affect **recommendation and explanation**. Execution is still `copilot run` or `jobs run` only; no auto-run from triggers.
- **Reminders:** Stored and listed; “due” is a list. No automatic execution when a reminder is due.

---

## 5. How this differs from autonomous background agents

- **No continuous monitoring:** Work state is built when you run `context refresh`, not by a daemon.
- **No auto-execution:** Trigger policies only tag recommendations; they do not start runs.
- **Inspectable:** Snapshots are JSON + markdown; you can inspect `data/local/context/work_state_summary.md` and compare with `context compare`.

---

## 6. How privacy/local-first is preserved

- All context data lives under `data/local/context` (snapshots, latest, previous).
- No network calls; all sources are local (job_packs, intake, dashboard, approvals, copilot, task_demos).
- No telemetry or cloud sync. Optional future scheduled refresh would be a local, opt-in, stoppable script (e.g. cron you control).
