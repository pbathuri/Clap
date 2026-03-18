# M28 Before-Coding: Portfolio Router + Project Scheduler

## 1. What project and loop state already exists

- **project_case**: `Project`, `Goal`, `ProjectState`, `NextProjectAction`; store: `list_projects(state_filter)`, `get_current_project_id`, `get_project_summary(project_id)` with blockers and `recommended_next_action`; goal_stack: `get_blocked_goals`, `recommended_next_goal`; graph: `build_project_state`, `get_project_summary`.
- **supervised_loop**: `AgentCycle` (project_slug, status, blocked_reason), `ApprovalQueueItem`, `QueuedAction`; store: `load_cycle`, `load_queue`, `load_handoffs`; queue: `list_pending`, approve/reject/defer; `propose_next_actions(project_slug)` → (actions, blocked_reason). Single current cycle; no multi-project routing.
- **progress**: `ReplanSignal`, `ProgressSignal`; store: `list_projects()` from prior_plans dir, `load_replan_signals`, `load_prior_plan`; board: `build_progress_board` → active_projects, project_health, stalled_projects, advancing_projects, replan_needed_projects, next_intervention_candidate; recommendation: `recommend_replan(project_id)`.
- **mission_control**: state includes `project_case`, `progress_replan`, `supervised_loop`; report formats them; `recommend_next_action(state)` recommends build/benchmark/hold etc. but does **not** recommend which project to work on next.
- **trust**: `build_trust_cockpit` (benchmark, approval, release gates); **daily**: inbox/digest; **outcomes**: session outcomes, outcome history, repeated_block_patterns, repeated_success_patterns used by progress board for stalled/advancing.

## 2. What is missing for real portfolio-level routing

- No **portfolio** abstraction: no explicit container for "active projects" with per-project urgency/value/blocker/readiness.
- No **ranking** of projects by urgency, value, blockers, trust/readiness; no "next recommended project" for the agent loop.
- No **explanation** of why a project is prioritized (urgency score, value score, blocker severity, trust/readiness).
- No **defer/revisit** at portfolio level (only at approval-queue level).
- Mission control does not show portfolio priority stack, top intervention candidate, next recommended project, most blocked, or most valuable ready.
- Progress board uses `progress.store.list_projects()` (prior_plans) and outcomes-based stalled; it is not aligned with **project_case** active projects and has no unified ranking across project_case + progress + loop.

## 3. Exact file plan

| Action | Path |
|--------|------|
| New | `src/workflow_dataset/portfolio/__init__.py` |
| New | `src/workflow_dataset/portfolio/models.py` — Phase A models |
| New | `src/workflow_dataset/portfolio/store.py` — optional portfolio metadata (priority hints, defer/revisit) |
| New | `src/workflow_dataset/portfolio/scheduler.py` — Phase B: rank, next, explain |
| New | `src/workflow_dataset/portfolio/reports.py` — Phase C: reports (active, stalled, blocked, next, intervention, ready) |
| New | `src/workflow_dataset/portfolio/cli.py` — Phase D: CLI helpers |
| Edit | `src/workflow_dataset/cli.py` — add `portfolio` group and commands |
| Edit | `src/workflow_dataset/mission_control/state.py` — add `portfolio_router` block |
| Edit | `src/workflow_dataset/mission_control/report.py` — add [Portfolio] section |
| New | `tests/test_portfolio_m28.py` — Phase E tests |
| New | `docs/M28_PORTFOLIO_ROUTER.md` — Phase E docs |

## 4. Safety/risk note

- Portfolio layer is **read-only** for project_case, supervised_loop, progress: it only aggregates and ranks. No auto-run across projects; no hidden reprioritization.
- Priority logic is **explicit and inspectable** via `portfolio explain --project <id>`.
- Optional portfolio store (e.g. defer/revisit, operator priority hints) is local and operator-editable.
- **Risk**: Two project sources (project_case vs progress prior_plans). Mitigation: use **project_case.list_projects(state_filter="active")** as source of truth for portfolio entries; use progress/board and outcomes as **signals** for ranking (replan_needed, stalled, etc.).

## 5. What this block will NOT do

- Auto-run work across projects.
- Rebuild project/loop/progress systems.
- Hide priority logic (all explainable).
- Add cloud portfolio sync or multi-user collaboration.
- Replace progress board or project report — additive only.
