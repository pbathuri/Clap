"""
M29: Build unified workspace state from mission_control, portfolio, project_case, session, lanes, policy, outcomes.
Read-only aggregation; local-first.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any

# Full mission_control aggregate can take minutes on large trees; cap for home/shell UX.
_MISSION_CONTROL_HOME_TIMEOUT = float(os.environ.get("WORKFLOW_DATASET_MC_HOME_TIMEOUT", "12"))


def _mission_control_state_with_timeout(repo_root: Path) -> dict[str, Any] | None:
    """Run get_mission_control_state in a daemon thread with timeout.

    ThreadPoolExecutor workers are non-daemon; if MC times out the worker keeps
    running and blocks process exit (shell appears hung on the next command).
    """
    from workflow_dataset.mission_control.state import get_mission_control_state

    if _MISSION_CONTROL_HOME_TIMEOUT <= 0:
        return get_mission_control_state(repo_root)
    out: list[dict[str, Any] | None] = [None]
    err: list[BaseException | None] = [None]

    def _run() -> None:
        try:
            out[0] = get_mission_control_state(repo_root)
        except BaseException as e:
            err[0] = e

    t = threading.Thread(target=_run, daemon=True, name="mc_home_timeout")
    t.start()
    t.join(timeout=_MISSION_CONTROL_HOME_TIMEOUT)
    if t.is_alive():
        return None
    if err[0] is not None:
        return None
    return out[0]


try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.workspace.models import (
    ActiveWorkContext,
    NavigationState,
    WorkspaceArea,
    WorkspaceHomeSnapshot,
    WORKSPACE_AREAS,
)

_MC_NOT_FETCHED = object()


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_active_work_context(
    repo_root: Path | str | None = None,
    *,
    mission_control_prefetch: Any = _MC_NOT_FETCHED,
) -> ActiveWorkContext:
    """Aggregate active project, goal, session, approval queue, blocked, recent artifacts, next action."""
    root = _root(repo_root)
    ctx = ActiveWorkContext()

    # Current project
    try:
        from workflow_dataset.project_case.store import get_current_project_id
        from workflow_dataset.project_case.graph import get_project_summary
        pid = get_current_project_id(root)
        if pid:
            ctx.active_project_id = pid
            summary = get_project_summary(pid, root)
            if not summary.get("error"):
                ctx.active_project_title = summary.get("title", pid)
                rec = summary.get("recommended_next_action")
                if rec:
                    ctx.next_recommended_action = rec.get("action_type", "")
                    ctx.next_recommended_detail = rec.get("label", "") or rec.get("reason", "")
    except Exception:
        pass

    # Active goal (from planner or project)
    try:
        from workflow_dataset.planner.store import load_current_goal
        goal = load_current_goal(root)
        if goal:
            ctx.active_goal_text = goal[:200] if isinstance(goal, str) else str(goal)[:200]
    except Exception:
        pass

    # Active session
    try:
        from workflow_dataset.session import get_current_session
        session = get_current_session(root)
        if session:
            ctx.active_session_id = session.session_id
            ctx.active_session_pack_id = getattr(session, "value_pack_id", "") or ""
    except Exception:
        pass

    # Approval queue
    try:
        from workflow_dataset.supervised_loop.queue import list_pending
        pending = list_pending(root)
        ctx.queued_approvals_count = len(pending)
        ctx.queued_approval_ids = [q.queue_id for q in pending[:10]]
    except Exception:
        pass

    # Blocked (session board + progress)
    try:
        from workflow_dataset.session import get_current_session, build_session_board
        session = get_current_session(root)
        if session:
            board = build_session_board(session, root)
            for b in (board.blocked or [])[:5]:
                ctx.blocked_summary.append(str(b.get("label", b))[:60])
            ctx.blocked_items_count += len(board.blocked or [])
        from workflow_dataset.progress.board import build_progress_board
        board = build_progress_board(repo_root=root)
        stalled = board.get("stalled_projects", [])
        for p in stalled[:3]:
            ctx.blocked_summary.append(f"stalled:{p}")
        ctx.blocked_items_count += len(stalled)
    except Exception:
        pass

    # Recent artifacts (current session)
    try:
        from workflow_dataset.session import get_current_session
        from workflow_dataset.session.artifacts import list_artifacts
        session = get_current_session(root)
        if session:
            arts = list_artifacts(session.session_id, root, limit=10)
            ctx.recent_artifacts_count = len(arts)
            ctx.recent_artifact_refs = [getattr(a, "path_or_label", str(a))[:80] for a in arts[:5]]
    except Exception:
        pass

    # Next: portfolio next + mission_control next
    try:
        from workflow_dataset.portfolio import get_next_recommended_project
        rec = get_next_recommended_project(root)
        if rec:
            ctx.next_recommended_project_id = rec.project_id
            ctx.portfolio_next_reason = (rec.reason or "")[:150]
        if not ctx.next_recommended_action:
            from workflow_dataset.mission_control.next_action import recommend_next_action

            if mission_control_prefetch is not _MC_NOT_FETCHED:
                state = mission_control_prefetch
            else:
                state = _mission_control_state_with_timeout(root)
            if state is not None:
                next_rec = recommend_next_action(state)
                ctx.next_recommended_action = next_rec.get("action", "hold")
                ctx.next_recommended_detail = next_rec.get("rationale", "") or next_rec.get("detail", "")
            else:
                ctx.next_recommended_action = ctx.next_recommended_action or "hold"
                ctx.next_recommended_detail = (
                    ctx.next_recommended_detail or "Mission-control aggregate skipped (timeout); run mission-control for full state."
                )
    except Exception:
        pass

    return ctx


def build_workspace_areas(repo_root: Path | str | None = None) -> list[WorkspaceArea]:
    """Build list of workspace areas with labels and command hints."""
    root = _root(repo_root)
    areas = [
        WorkspaceArea("home", "Home", "Unified overview", "workflow-dataset workspace home", 0),
        WorkspaceArea("portfolio", "Portfolio", "Project priority and routing", "workflow-dataset portfolio status", 0),
        WorkspaceArea("projects", "Projects", "Projects and goals", "workflow-dataset projects list", 0),
        WorkspaceArea("active_session", "Active Session", "Current session and task board", "workflow-dataset session board", 0),
        WorkspaceArea("approvals_policy", "Approvals / Policy", "Queue and policy overrides", "workflow-dataset agent-loop queue ; workflow-dataset policy board", 0),
        WorkspaceArea("worker_lanes", "Worker Lanes", "Delegated subplans", "workflow-dataset lanes list", 0),
        WorkspaceArea("packs_runtime", "Packs / Runtime", "Packs and runtime mesh", "workflow-dataset packs list ; workflow-dataset runtime summary", 0),
        WorkspaceArea("artifacts_outcomes", "Artifacts / Outcomes", "Session artifacts and outcomes", "workflow-dataset outcomes report", 0),
        WorkspaceArea("rollout_support", "Rollout / Support", "Rollout state and support", "workflow-dataset rollout status", 0),
        WorkspaceArea("settings_health", "Settings / Health", "Environment and health", "workflow-dataset mission-control", 0),
        # M29 integration: conversational (Pane 3), timeline + inbox (Pane 2)
        WorkspaceArea("conversational_ask", "Ask", "Natural language query and explainability", "workflow-dataset ask \"What should I do next?\"", 0),
        WorkspaceArea("timeline", "Timeline", "Activity timeline (project, plan, approval, executor)", "workflow-dataset timeline latest", 0),
        WorkspaceArea("intervention_inbox", "Intervention Inbox", "Approval queue, blocked, replan, policy", "workflow-dataset inbox list", 0),
    ]
    try:
        from workflow_dataset.project_case.store import list_projects
        projects = list_projects(root, state_filter="active", limit=100)
        for a in areas:
            if a.area_id == "projects":
                a.count = len(projects)
                break
    except Exception:
        pass
    try:
        from workflow_dataset.portfolio import build_portfolio
        port = build_portfolio(root)
        for a in areas:
            if a.area_id == "portfolio":
                a.count = port.health.total_active
                break
    except Exception:
        pass
    try:
        from workflow_dataset.review_studio.inbox import build_inbox
        from workflow_dataset.review_studio.timeline import build_timeline
        inbox_items = build_inbox(root, status="pending", limit=500)
        timeline_events = build_timeline(root, limit=100)
        for a in areas:
            if a.area_id == "intervention_inbox":
                a.count = len(inbox_items)
                break
        for a in areas:
            if a.area_id == "timeline":
                a.count = len(timeline_events)
                break
    except Exception:
        pass
    return areas


def build_navigation_state(
    current_view: str = "home",
    current_project_id: str = "",
    current_session_id: str = "",
    repo_root: Path | str | None = None,
) -> NavigationState:
    """Build navigation state; optionally seed from current project/session."""
    root = _root(repo_root)
    if not current_project_id:
        try:
            from workflow_dataset.project_case.store import get_current_project_id
            current_project_id = get_current_project_id(root) or ""
        except Exception:
            pass
    if not current_session_id:
        try:
            from workflow_dataset.session import get_current_session
            session = get_current_session(root)
            current_session_id = session.session_id if session else ""
        except Exception:
            pass
    breadcrumbs = ["Home"]
    if current_view == "portfolio":
        breadcrumbs = ["Home", "Portfolio"]
    elif current_view == "project" and current_project_id:
        breadcrumbs = ["Home", "Portfolio", current_project_id]
    elif current_view == "session" and current_session_id:
        breadcrumbs = ["Home", "Session", current_session_id]
    elif current_view != "home":
        breadcrumbs = ["Home", current_view]
    quick_actions = []
    if current_project_id:
        quick_actions.append({"label": "Project report", "command": f"workflow-dataset projects report --id {current_project_id}"})
        quick_actions.append({"label": "Agent next", "command": f"workflow-dataset agent-loop next --project {current_project_id}"})
    quick_actions.append({"label": "Mission control", "command": "workflow-dataset mission-control"})
    return NavigationState(
        current_view=current_view,
        current_project_id=current_project_id,
        current_session_id=current_session_id,
        breadcrumbs=breadcrumbs,
        quick_actions=quick_actions[:5],
    )


def build_workspace_home_snapshot(repo_root: Path | str | None = None) -> WorkspaceHomeSnapshot:
    """Build full workspace home snapshot: context, navigation, areas, summaries."""
    root = _root(repo_root)
    mc_once = _mission_control_state_with_timeout(root)
    context = build_active_work_context(root, mission_control_prefetch=mc_once)
    areas = build_workspace_areas(root)
    navigation = build_navigation_state("home", context.active_project_id, context.active_session_id, root)

    top_priority_project_id = ""
    try:
        from workflow_dataset.portfolio import get_next_recommended_project
        rec = get_next_recommended_project(root)
        if rec:
            top_priority_project_id = rec.project_id
    except Exception:
        pass

    approval_queue_summary = ""
    if context.queued_approvals_count > 0:
        approval_queue_summary = f"{context.queued_approvals_count} pending approval(s). Run: workflow-dataset agent-loop queue"
    else:
        approval_queue_summary = "No pending approvals."

    blocked_summary = ""
    if context.blocked_items_count > 0:
        blocked_summary = "; ".join(context.blocked_summary[:3]) or f"{context.blocked_items_count} blocked item(s)"
    else:
        blocked_summary = "No blocked items."

    recent_activity_summary = ""
    try:
        from workflow_dataset.supervised_loop.summary import build_cycle_summary
        summary = build_cycle_summary(root)
        if summary.last_run_id or summary.last_handoff_status:
            recent_activity_summary = f"Last: {summary.last_handoff_status or '—'} run={summary.last_run_id or '—'}"
    except Exception:
        pass
    if not recent_activity_summary and context.recent_artifacts_count > 0:
        recent_activity_summary = f"{context.recent_artifacts_count} recent artifact(s) in session."

    trust_health_summary = ""
    try:
        state = mc_once
        if state is None:
            trust_health_summary = "— (mission-control summary skipped: timeout)"
        else:
            tc = state.get("trust_cockpit", {})
            if not tc.get("error"):
                trust_health_summary = f"Trust: {tc.get('benchmark_trust', {}).get('latest_trust_status', '—')}"
            eh = state.get("environment_health", {})
            if not eh.get("error") and eh.get("required_ok"):
                trust_health_summary = (trust_health_summary + " ; Env: OK").strip(" ;")
    except Exception:
        pass

    return WorkspaceHomeSnapshot(
        context=context,
        navigation=navigation,
        areas=areas,
        top_priority_project_id=top_priority_project_id or context.next_recommended_project_id,
        approval_queue_summary=approval_queue_summary,
        blocked_summary=blocked_summary,
        recent_activity_summary=recent_activity_summary or "—",
        trust_health_summary=trust_health_summary or "—",
        updated_at_iso=utc_now_iso(),
    )
