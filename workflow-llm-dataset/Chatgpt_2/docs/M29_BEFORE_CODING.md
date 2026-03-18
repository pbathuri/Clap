# M29 Before-Coding: Unified Workspace Shell + Navigation State

## 1. What user-facing / workspace-adjacent surfaces already exist

- **mission_control**: `get_mission_control_state(repo_root)` aggregates product_state, evaluation_state, development_state, incubator_state, project_case, supervised_loop, progress_replan, portfolio_router, worker_lanes, human_policy, executor, goal_plan, etc. `format_mission_control_report(state)` produces a long text report. `recommend_next_action(state)` returns build/benchmark/hold/rollback etc. CLI: `workflow-dataset mission-control`.
- **daily**: `build_daily_digest(repo_root)` returns DailyDigest (inbox_items, blocked_items, reminders_due, top_next_recommended, recommended_next_action). Used by mission_control state (daily_inbox). No standalone CLI "inbox" in the list checked.
- **dashboard (ui)**: `dashboard_group` with `dashboard` (default), `dashboard workspace`, `dashboard package`, etc.; `print_dashboard_cli` / `print_drilldown_cli` use release/dashboard_data (cohort, workspaces, review/package, staging). Focus is release/package/readiness, not portfolio/session/lanes.
- **ui/home_view**: `render_home` shows "Local Operator Console" with get_home_counts (setup sessions, projects, domains, suggestions, drafts, workspaces, rollback, generations, LLM). Menu: Setup, Projects, Suggestions, Drafts, Materialize, Apply, Rollback, Chat, Generation, LLM, Trials, Release, Friendly trial, Pilot, Runtime, Quit. No portfolio, session, lanes, policy, or "current project/session" in the menu.
- **session**: `get_current_session`, `build_session_board` (queued, blocked, ready), `list_artifacts`; CLI under `session` group. mission_control has `active_session` block.
- **portfolio**: `build_portfolio`, `get_next_recommended_project`; CLI `portfolio list|status|rank|next|...`. mission_control has `portfolio_router`.
- **projects**: `list_projects`, `get_current_project_id`, `get_project_summary`; CLI `projects list|show|goals|report|set-current|...`. mission_control has `project_case`.
- **agent_loop**: Cycle summary, queue, next; CLI `agent-loop status|next|queue|approve|...`. mission_control has `supervised_loop`.
- **lanes**: `list_lanes`, handoff/results; CLI `lanes list|create|status|results|handoff|close`. mission_control has `worker_lanes`.
- **human_policy**: Board, overrides, evaluate; CLI `policy show|evaluate|override|board|...`. mission_control has `human_policy`.
- **outcomes**: `list_session_outcomes`, `load_outcome_history`; used by mission_control and progress. No dedicated "workspace" entry that answers "where am I / what is active / what next" in one place.

## 2. What is missing for a real unified shell

- **Single workspace home**: One command/view that shows top-priority project, active session, approval queue summary, blocked items, recent artifacts, and next action recommendation together (without running full mission-control or digging into each subsystem).
- **Explicit navigation state**: No current "view" (Home / Portfolio / Project / Session / Approvals / Lanes / Packs / Artifacts / Rollout / Settings), no stored "current project context" or "current session context" for the shell (project_case has current_project_id; session has current_session_id — but no unified breadcrumb or "open" view).
- **View switching / deep links**: No explicit "open portfolio", "open project X", "open session Y" that set context and suggest next commands; no CLI-equivalent deep links (e.g. workspace open --project X → output "projects show --id X; agent-loop next --project X").
- **Unified context command**: No single "workspace context" that prints current project, session, view, and suggested next steps in one block.
- **Workspace CLI group**: No `workflow-dataset workspace home|open|context|next` that ties together the above.

## 3. Exact file plan

| Action | Path |
|--------|------|
| New | `src/workflow_dataset/workspace/__init__.py` |
| New | `src/workflow_dataset/workspace/models.py` — Phase A (areas, WorkspaceModel with active project, goal, session, approvals, blocked, artifacts, next_action) + Phase B (WorkspaceView, NavigationState, breadcrumbs, quick_actions) |
| New | `src/workflow_dataset/workspace/state.py` — build_workspace_state() aggregating from mission_control, portfolio, project_case, session, supervised_loop, lanes, human_policy, outcomes, daily |
| New | `src/workflow_dataset/workspace/home.py` — build_unified_home(), format_workspace_home() (Phase C) |
| New | `src/workflow_dataset/workspace/navigation.py` — resolve_view_target(), deep_link_commands (Phase D) |
| New | `src/workflow_dataset/workspace/cli.py` — cmd_home, cmd_open, cmd_context, cmd_next (Phase E) |
| Edit | `src/workflow_dataset/cli.py` — add workspace_group and commands (workspace home|open|context|next) |
| New | `tests/test_workspace_m29.py` — Phase F |
| New | `docs/M29_WORKSPACE_SHELL.md` — Phase F |

## 4. Safety/risk note

- Workspace layer is **read-only** and **additive**: it only aggregates existing state and formats it. It does not change project_case, session, portfolio, or policy state. Navigation "current view" can be in-memory or a small local file (e.g. data/local/workspace/current_view.json) for CLI consistency; no cloud, no hidden automation.
- **Trust/approval boundaries** unchanged: no auto-approve or auto-execute from the workspace shell. Deep links suggest commands; operator runs them.
- **Risk**: Duplication of "next action" logic (mission_control next_action vs workspace next). Mitigation: workspace "next" can call or mirror mission_control recommend_next_action and optionally portfolio get_next_recommended_project so one source of truth is used.

## 5. What this block will NOT do

- Replace or redesign mission_control, dashboard, or ui/home_view; integrate additively.
- Add a web UI or cloud dashboard.
- Add collaborative or multi-user workspace features.
- Auto-execute or auto-approve; all commands remain explicit and operator-driven.
- Full visual redesign; focus is structure, navigation model, and unified home/context CLI.
