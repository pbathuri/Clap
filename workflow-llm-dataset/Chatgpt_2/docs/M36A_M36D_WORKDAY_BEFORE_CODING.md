# M36A–M36D Daily Operating Surface — Before Coding

## 1. What top-level shell/state surfaces already exist

- **Workspace**: `workspace home` builds `WorkspaceHomeSnapshot` with `ActiveWorkContext` (active project, goal, session, approval queue, blocked, recent artifacts, next action), `NavigationState`, and areas. Sections: where you are, top priority, approvals, blocked, recent, trust health, areas, quick actions. CLI: `workspace home`, `workspace open`, `workspace context`, `workspace next`.
- **Mission control**: `get_mission_control_state()` aggregates product_state, evaluation_state, development_state, incubator_state, coordination_graph, desktop_bridge, observation_state, live_context_state, job_packs, copilot, work_context, action_cards_summary, automations_state, background_runner_state, automation_inbox, workflow_episodes, live_workflow_state, trust_cockpit, authority_contracts_state, daily_inbox, and many more. `format_mission_control_report()` produces a long text dashboard. `recommend_next_action()` returns build|benchmark|cohort_test|promote|hold|rollback|replay_task|observe_setup.
- **Daily**: `build_daily_digest()` produces `DailyDigest` (what changed, relevant jobs/routines, inbox items, blocked, reminders, approvals, trust regressions, top next). `format_inbox_report()` formats it. Inbox CLI: default callback, explain, compare, snapshot, list, review, accept, reject, defer.
- **Operator mode**: `operator-mode status`, `bundles`, `pause`, `revoke` — pause state, revocation, responsibilities/bundles. No explicit “workday mode.”
- **Session**: Current session, board, artifacts, start/resume/close — session-scoped, not day-scoped.
- **Portfolio, projects, progress, outcomes, planner, executor, automations, background, review studio, automation inbox, timeline**: All exist; no single “workday state” or explicit “current operating mode” (start / focus / review / operator / wrap / shutdown / resume).

## 2. What is missing for a real daily operating layer

- **Explicit workday state** with persistence: e.g. not_started, startup, focus_work, review_and_approvals, operator_mode, wrap_up, shutdown, resume_pending.
- **State transitions** that are explicit, explainable, and stateful: start day, shift to focus, shift to review, shift to operator mode, wrap up, shutdown, resume.
- **State entry/exit conditions** and **blocked state** (e.g. cannot enter operator_mode if trust config invalid or paused).
- **Day summary snapshot**: What was done this “day” (states visited, approvals count, top actions).
- **Single top-level daily operating surface**: One view showing current workday state, active project, active focus/workflow, top queue item, pending approvals, automation/background summary, trust posture, next recommended transition.
- **Resume prior state** next session: Persist last state so “day resume” restores it.
- **CLI**: `workflow-dataset day status`, `day start`, `day mode --set focus_work`, `day wrap-up`, `day shutdown`, `day resume`.
- **Mission control additive**: Current workday mode, pending state transition recommendation, blocked mode transition, day progress snapshot, next best operating action.

## 3. Exact file plan

| Action | Path | Purpose |
|--------|------|---------|
| Create | `src/workflow_dataset/workday/__init__.py` | Exports |
| Create | `src/workflow_dataset/workday/models.py` | WorkdayState enum, WorkdayStateRecord, StateTransition, ActiveDailyContext, DaySummarySnapshot |
| Create | `src/workflow_dataset/workday/state_machine.py` | Valid transition graph, can_transition, entry/exit conditions, blocked_reasons, apply_transition |
| Create | `src/workflow_dataset/workday/store.py` | load/save workday state (data/local/workday/state.json), day summaries |
| Create | `src/workflow_dataset/workday/surface.py` | build_daily_operating_surface() |
| Create | `src/workflow_dataset/workday/cli.py` | cmd_day_status, cmd_day_start, cmd_day_mode, cmd_wrap_up, cmd_shutdown, cmd_resume |
| Modify | `src/workflow_dataset/cli.py` | Add day_group with status, start, mode, wrap-up, shutdown, resume |
| Modify | `src/workflow_dataset/mission_control/state.py` | workday_state: current_workday_mode, pending_transition, blocked_transition, day_progress_snapshot, next_best_operating_action |
| Modify | `src/workflow_dataset/mission_control/report.py` | [Workday] section |
| Create | `tests/test_workday.py` | State model, transitions, surface, blocked, resume/shutdown, empty state |
| Create | `docs/M36A_M36D_WORKDAY_STATE_AND_SURFACE.md` | Files, CLI, samples, tests, gaps |

## 4. Safety/risk note

- Workday state is **local-only and advisory**. It does not auto-execute transitions or change system behavior by itself; it only records and recommends.
- Operator mode pause/revoke and trust/approval gates remain the authority. No cloud; no hidden state changes. Transitions are explicit (user/CLI driven).

## 5. What this block will NOT do

- Will not rebuild workspace, mission_control, daily inbox, or operator mode.
- Will not add cloud sync or collaborative workday.
- Will not auto-transition states (e.g. time-based).
- Will not override trust/approval/operator-mode policies.
