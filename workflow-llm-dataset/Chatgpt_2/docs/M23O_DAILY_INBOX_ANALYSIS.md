# M23O — Daily Work Inbox + Context Digest (pre-coding)

## 1. What already exists (work state, context, routines, reminders)

- **WorkState** (`context/work_state.py`): build_work_state() aggregates job_packs report, intake, dashboard (workspaces, unreviewed, package_pending), approvals, copilot (reminders, routines, plan runs), task_demos. work_state_summary_md() for human-readable summary.
- **Context snapshot** (`context/snapshot.py`): save_snapshot(), load_snapshot("latest"|"previous"|id), list_snapshots(). Writes to data/local/context/snapshots/, latest.json, previous.json, work_state_summary.md.
- **Context drift** (`context/drift.py`): compare_snapshots(older, newer) → ContextDrift (newly_recommendable_jobs, newly_blocked_jobs, approvals_changed, intake added/removed, count deltas, summary lines). load_latest_and_previous().
- **Recommendations** (`copilot/recommendations.py`): recommend_jobs(limit, context_snapshot) returns list of dicts with job_pack_id, reason, trust_level, required_approvals, mode_allowed, blocking_issues, recommended_timing_context; optional why_now_evidence, context_trigger from triggers.
- **Routines** (`copilot/routines.py`): list_routines(), get_routine(), save_routine(); Routine has job_pack_ids, title, description, simulate_only.
- **Reminders** (`copilot/reminders.py`): list_reminders(), reminders_due(limit), add_reminder(); reminders_due currently returns all reminders (no real scheduling).
- **Corrections** (`corrections/store.py`, propose.py, eval_bridge): list_corrections(), propose_updates(), advisory_review_for_corrections().
- **Mission control** (`mission_control/state.py`, next_action.py): get_mission_control_state() aggregates product, evaluation, development, incubator, desktop_bridge, job_packs, copilot, work_context, corrections; recommend_next_action(state) for build/benchmark/cohort_test/promote/hold/rollback/replay_task.
- **Dashboard** (`release/dashboard_data.py`): get_dashboard_data() → readiness, recent_workspaces, review_package, cohort, next_actions, action_macros.
- **Job packs** (`job_packs/report.py`): job_packs_report() → total_jobs, simulate_only_jobs, trusted_for_real_jobs, approval_blocked_jobs, jobs_with_failure_notes, recent_successful; job_diagnostics(job_pack_id).
- **Daily inbox (M23V)** (`daily/inbox.py`, inbox_report.py): DailyDigest with relevant_job_ids, relevant_routine_ids, blocked_items, reminders_due, approvals_needing_refresh, trust_regressions, recent_successful_runs, recommended_next_action/detail, corrections_review_recommended, unresolved_corrections_count. build_daily_digest(). format_inbox_report(). CLI: `workflow-dataset inbox`.

## 2. What is missing for a daily-use inbox

- **What changed since last snapshot**: Digest does not integrate context drift; no "what changed" section in the inbox view.
- **Per-item explanation**: Inbox does not show reason, trust level, mode available, blockers, and expected outcome for each recommended item; recommend_jobs has this data but it is not surfaced in the report.
- **Explicit prioritization**: Ranking is implicit (order of recommend_jobs); no single "top next recommended action" with explanation.
- **Digest history**: No persistence of digest snapshots or compare (latest vs previous, newly appeared, dropped, escalated).
- **Stale items**: Not explicitly called out (e.g. jobs with failure notes or old unreviewed workspaces).
- **Explain-why-now**: No dedicated command or section that explains why each item is shown now.

## 3. Exact file plan

| Action | Path |
|--------|------|
| Modify | `src/workflow_dataset/daily/inbox.py` — Extend DailyDigest: created_at, work_state_snapshot_id, what_changed (list[str] or drift summary), inbox_items (list of {id, kind, reason, trust_level, mode_available, blockers, expected_outcome}), top_next_recommended_action (dict with label, reason, command). Build inbox_items from recommend_jobs + get_job_pack title/description for expected_outcome. Optionally refresh work-state snapshot and compute drift. |
| Modify | `src/workflow_dataset/daily/inbox_report.py` — Add "What changed" section when what_changed present; add "Inbox items (why now)" with reason, trust, mode, blockers, expected outcome per item; add format_explain_why_now(digest). |
| Create | `src/workflow_dataset/daily/digest_history.py` — save_digest_snapshot(digest, repo_root), load_digest_snapshot(snapshot_id), list_digest_snapshots(limit), compare_digests(older, newer) → DigestCompare (newly_appeared, dropped, escalated). Persist under data/local/context/digests/ or data/local/daily/. |
| Modify | `src/workflow_dataset/cli.py` — inbox: add --explain; add `inbox compare` (latest vs previous); add `inbox snapshot` to persist current digest. |
| Create | `tests/test_daily_inbox_m23o.py` — digest with inbox_items, blocked-state reporting, explain output, digest compare, no-data/partial-data. |
| Create | `docs/M23O_DAILY_INBOX.md` — CLI usage, sample digest, sample explain, sample compare, tests. |

## 4. Safety/risk note

- **No autonomous execution**: Inbox and digest are read-only aggregation and presentation. No runs or writes except optional snapshot persistence under data/local.
- **Local-only**: All sources are existing local modules (job_packs, copilot, context, corrections, desktop_bench); digest history stored under data/local.
- **Explicit ranking**: Prioritization uses existing recommend_jobs order and explicit reason/trust/mode/blockers; no hidden scoring.
- **Preserve gates**: No change to approval or execution gates; inbox only surfaces what is blocked and why.
