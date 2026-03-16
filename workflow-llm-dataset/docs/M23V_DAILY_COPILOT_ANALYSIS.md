# M23V — Daily Copilot Surface + Macro Execution + Trust/Release Cockpit (pre-coding)

## 1. What already exists for daily surface, routines, and trust

### Daily / inbox surface
- **Mission control** (`mission_control/state.py`, `report.py`): Aggregates product_state, evaluation_state, development_state, incubator_state, coordination_graph_summary, desktop_bridge, job_packs, **copilot**, work_context, corrections. Report has [Product], [Evaluation], [Development], [Incubator], [Coordination graph], [Desktop bridge], [Job packs], [Copilot], [Context], [Corrections], plus recommended next action. No dedicated "daily inbox" or "start here" digest.
- **Copilot state in mission_control**: `recommended_jobs_count`, `blocked_jobs_count`, `routines_count`, `recent_plan_runs_count`, `reminders_count`, `upcoming_reminders`, `next_copilot_action`. Raw counts and IDs; not formatted as a daily "what should I do now?" digest.
- **Work context (M23L)**: `latest_snapshot_id`, `context_recommendations_count`, `context_blocked_count`, `newly_recommendable_jobs`, `reminders_due_count`, `recent_state_changes`, `next_recommended_action`. Used by mission_control; no standalone daily view.
- **Reminders**: `copilot/reminders.py` — `list_reminders`, `reminders_due`; storage in `data/local/copilot/reminders.yaml`. No "approvals needing refresh" or "trust regressions" in one place.
- **Dashboard** (`release/dashboard_data.py`): Readiness, workspaces, review_package, staging, cohort, alerts, next_actions, action_macros. Oriented to review/package/cohort, not daily operator inbox.
- **Console home** (`ui/home_view.py`): Setup sessions, projects, domains, style profiles, suggestions, drafts, workspaces, rollback, generations, LLM adapter. No jobs/routines/reminders/approvals/trust.

### Routines / multi-step
- **Routines (M23K)**: `copilot/routines.py` — `Routine` dataclass (routine_id, title, job_pack_ids, ordering, stop_on_first_blocked, required_approvals, simulate_only, expected_outputs). Stored under `data/local/copilot/routines/*.yaml`. `list_routines`, `get_routine`, `get_ordered_job_ids`.
- **Plan preview**: `copilot/plan.py` — `build_plan_for_job`, `build_plan_for_routine` → `PlanPreview` (plan_id, job_pack_ids, mode, approvals_required, trusted_actions_involved, blocked, blocked_reasons, step_previews). No execution.
- **Plan run**: `copilot/run.py` — `run_plan(plan, repo_root, stop_on_first_blocked, continue_on_blocked)`. Runs jobs in order; records executed/blocked; persists to `data/local/copilot/runs/<run_id>/plan_run.json`. **No checkpoint/pause/resume**; no "macro" as a first-class named entity beyond routine.
- **No macro schema** distinct from Routine: routines are the only multi-step bundle; no separate "macro" with preview/simulate/checkpoint semantics.

### Trust / evidence
- **Desktop benchmark (M23I)**: `desktop_bench/board.py` — `board_report()`: latest_run_id, latest_outcome, latest_trust_status, simulate_only_coverage, trusted_real_coverage, missing_approval_blockers, regressions, recommended_next_action. `desktop_bench/scoring.py` — `compute_trust_status`: trusted | usable_with_simulation_only | approval_missing | experimental | regression_detected. `desktop_bench/trusted_actions.py` — `get_trusted_real_actions()`.
- **Job policy**: `job_packs/policy.py` — `check_job_policy(job, mode, params, repo_root)`; trust_level, real_mode_eligibility.
- **Corrections (M23M)**: `corrections/report.py` — `corrections_report()`: recent_corrections_count, proposed_updates_count, applied/reverted, most_corrected_ids. Mission_control already has corrections block.
- **No unified "trust cockpit"**: Benchmark board, job trust, corrections, and release gates are separate; no single view of benchmark trust, trusted-real coverage, simulate-only coverage, approval readiness, job/macro trust state, unresolved corrections, release-gate status.

### Packaging / install readiness
- **Edge**: `edge/report.py` — `generate_edge_readiness_report`, `generate_missing_dependency_report`, `generate_package_report`, tier matrix, smoke check report. Outputs under `data/local/edge/`.
- **Release**: `release/report.py` — `write_release_readiness_report()` → scope, evidence, safety, demo readiness; writes `data/local/release/release_readiness_report.md`.
- **No single "package/install readiness summary"** for "current machine readiness", "current product readiness", "missing runtime/integration prerequisites", "ready for first real-user install", "what is experimental".

---

## 2. What is missing for a credible daily-use shell

- **Daily inbox / digest**: One "start here" view with: new relevant jobs/routines, blocked items and why, reminders due, approvals needing refresh, trust regressions, recent successful runs, recommended next action, optional domain-pack-aware suggestions. Today the operator must open mission-control and mentally combine [Copilot], [Context], [Corrections], [Desktop bridge], [Job packs].
- **Macro as first-class**: Routine exists but no "macro" naming with explicit preview → simulate run → checkpointed real-run (where trusted/approved), pause/resume, blocked-step reporting. Need macro schema (can alias routine initially), preview CLI, simulate run, checkpointed real run, pause/resume state, blocked-step report.
- **Trust / evidence cockpit**: Single view: benchmark trust, trusted-real coverage, simulate-only coverage, approval readiness, job/macro trust state, unresolved corrections, release-gate status. Today: desktop-bench board, job_packs report, corrections report, release report are separate.
- **Packaging / install readiness summary**: One report: current machine readiness, product readiness, missing runtime/integration prerequisites, ready for first real-user install (yes/no), what remains experimental. Today: edge readiness + release readiness are separate; no single "package readiness" summary.
- **Dashboard / mission control integration**: Additive sections for inbox, macros, trust cockpit, release gates, package/install readiness in the existing mission_control report and/or dashboard_data so the daily surface is reachable from command center.
- **CLI entry points**: `workflow-dataset inbox`, `workflow-dataset macro list|preview|run`, `workflow-dataset trust cockpit|release-gates`, `workflow-dataset package readiness-report` (or under existing edge/release groups where appropriate).
- **Console/UI**: Home or a dedicated "Daily" screen could show inbox summary and link to trust/readiness; additive only, no rewrite of UI shell.

---

## 3. What can be reused from command center / mission control

- **Mission control state**: Already aggregates copilot, job_packs, work_context, corrections, desktop_bridge. **Reuse** `get_mission_control_state()` and existing blocks to build inbox digest (filter/format for "daily" view) and trust cockpit (aggregate desktop_bench board, job trust, corrections, release).
- **Mission control report**: Add new sections **[Inbox]** (or **[Daily digest]**), **[Macros]**, **[Trust cockpit]**, **[Release gates]**, **[Package readiness]**; or keep report as-is and add separate commands that call the same state + new formatters.
- **Dashboard data**: `get_dashboard_data()` has readiness, staging, cohort, next_actions, action_macros. **Reuse** for release-gate and readiness summary; add keys for inbox_summary, trust_summary, package_readiness_summary if we want dashboard one-shot.
- **Copilot**: `recommend_jobs`, `list_routines`, `reminders_due`, `list_plan_runs`; **reuse** for inbox. `build_plan_for_routine`, `run_plan` for macro preview/run (macro = routine for this phase).
- **Desktop bench**: `board_report`, `list_runs`, `get_trusted_real_actions`, `compute_trust_status`; **reuse** for trust cockpit.
- **Edge + release**: `run_readiness_checks`, `checks_summary`, `build_edge_profile`, `write_release_readiness_report`; **reuse** for package/install readiness summary.
- **Corrections**: `corrections_report`, `advisory_review_for_corrections`; **reuse** for trust cockpit and inbox "unresolved corrections".

---

## 4. Exact file plan

| Action | Path |
|--------|------|
| Create | `src/workflow_dataset/daily/__init__.py` |
| Create | `src/workflow_dataset/daily/inbox.py` — Build daily digest: new/relevant jobs & routines, blocked + reasons, reminders due, approvals needing refresh, trust regressions (from desktop_bench), recent successful runs, recommended next action; optional domain-pack suggestions (interface only). Output: dataclass or dict for CLI/formatter. |
| Create | `src/workflow_dataset/daily/inbox_report.py` — Format inbox as text (sample output for doc). |
| Create | `src/workflow_dataset/macros/__init__.py` |
| Create | `src/workflow_dataset/macros/schema.py` — Macro schema (macro_id, title, routine_id or job_pack_ids, mode, stop_on_first_blocked, required_approvals, simulate_only). For M23V, macro can wrap a routine 1:1. |
| Create | `src/workflow_dataset/macros/runner.py` — preview(macro_id), simulate_run(macro_id), run(macro_id, mode) with checkpoint recording (reuse copilot run_plan; checkpoint = plan_run record), list_blocked_steps; no pause/resume state machine in first cut (optional: run_id + step index in plan_run.json). |
| Create | `src/workflow_dataset/macros/report.py` — format_macro_preview, format_blocked_steps. |
| Create | `src/workflow_dataset/trust/__init__.py` |
| Create | `src/workflow_dataset/trust/cockpit.py` — Aggregate: benchmark trust (desktop_bench board_report), trusted-real coverage, simulate-only coverage, approval readiness (desktop_bridge), job/macro trust state (job_packs_report + routine list), unresolved corrections (corrections_report), release-gate status (from dashboard_data/release). Output: dict; no new stores. |
| Create | `src/workflow_dataset/trust/report.py` — format_trust_cockpit, format_release_gates. |
| Create | `src/workflow_dataset/package_readiness/__init__.py` |
| Create | `src/workflow_dataset/package_readiness/summary.py` — Build summary: current machine readiness (edge checks_summary), product readiness (release readiness + staging), missing runtime/integration prerequisites (edge missing deps), ready for first real-user install (boolean + reasons), experimental list. Output: dict. |
| Create | `src/workflow_dataset/package_readiness/report.py` — format_readiness_report. |
| Modify | `src/workflow_dataset/cli.py` — Add `inbox` command; add `macro_group` with `list`, `preview`, `run`; add `trust_group` with `cockpit`, `release-gates`; add `package readiness-report` (under existing group or new `package` group). |
| Modify | `src/workflow_dataset/mission_control/state.py` — Optional: add `inbox_summary` and `trust_summary` keys when building state (or keep state as-is and have inbox/trust commands call their own builders that use same underlying sources). Prefer additive: add `daily_inbox` and `trust_cockpit` blocks that call daily.inbox and trust.cockpit. |
| Modify | `src/workflow_dataset/mission_control/report.py` — Add sections [Inbox] (or [Daily]), [Trust cockpit], [Package readiness] when present. |
| Modify | `src/workflow_dataset/release/dashboard_data.py` — Optional: add inbox_summary, trust_cockpit_summary, package_readiness_summary to get_dashboard_data() for dashboard view. |
| Create | `tests/test_daily_inbox.py` — inbox digest generation, structure. |
| Create | `tests/test_macros.py` — macro preview, run (simulate), checkpoint logic, blocked-step reporting. |
| Create | `tests/test_trust_cockpit.py` — trust cockpit output, release-gate reporting. |
| Create | `tests/test_package_readiness.py` — readiness report structure. |
| Create | `docs/M23V_DAILY_COPILOT.md` — Usage, sample inbox, macro definition + preview, trust cockpit, readiness report, CLI, safety. |

---

## 5. Safety/risk note

- **No new autopilot**: Inbox and macro runner are explicit: user runs `inbox` or `macro run`; no auto-run on reminders or background execution.
- **No bypass of approval/trust**: Macro run uses existing `run_plan` and `check_job_policy`; real mode still requires approval registry and trusted actions. Trust cockpit is read-only visibility.
- **No UI rewrite**: Additive sections in mission_control report and optional dashboard keys; console home can get a "Daily (I)" option or similar without replacing existing screens.
- **Local-only**: All new modules read from existing local_sources; macros persist runs under existing copilot/runs; no cloud or telemetry.
- **Pane contracts**: Consume runtime/backend and profile/domain-pack/specialization via abstract interfaces only; no hard dependency on concrete implementations from Pane 1/Pane 2.

---

## 6. What this phase will NOT do

- **No uncontrolled autopilot**: No auto-run of macros on reminders; no background scheduling.
- **No approval bypass**: Trust cockpit and package readiness are informational; they do not grant or skip approvals.
- **No full installer rewrite**: Package readiness is a summary/report only; no new installer or install flow.
- **No rewrite of dashboard/console**: Additive sections and commands only; existing workflow/templates/chain lab/dashboard/mission control unchanged in scope.
- **No hard dependency on cloud or optional integrations**: All features work with local data only; domain-pack-aware suggestions are optional and interface-based.
- **No pause/resume state machine** (optional for later): Checkpoint = persisted plan_run; "resume" can be "re-run from next step" in a follow-up if needed.
