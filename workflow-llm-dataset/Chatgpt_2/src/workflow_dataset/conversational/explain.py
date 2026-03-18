"""
M29E–M29H: Explainability — conversational answers grounded in explicit system state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _get_state(repo_root: Path | str | None) -> dict[str, Any]:
    try:
        from workflow_dataset.mission_control.state import get_mission_control_state
        return get_mission_control_state(repo_root)
    except Exception:
        return {}


def answer_what_next(state: dict[str, Any] | None = None, repo_root: Path | str | None = None) -> str:
    """What should I do next? Grounded in mission_control next action and project/loop state."""
    state = state or _get_state(repo_root)
    try:
        from workflow_dataset.mission_control.next_action import recommend_next_action
        rec = recommend_next_action(state)
        action = rec.get("action", "hold")
        rationale = rec.get("rationale", "")
        detail = rec.get("detail", "")
        out = f"Recommended next action: **{action}**. {rationale}"
        if detail:
            out += f" {detail}"
    except Exception as e:
        out = f"Could not compute next action: {e}. Run 'workflow-dataset mission-control' for full state."
    pc = state.get("project_case", {})
    if pc and not pc.get("error"):
        nxt = pc.get("recommended_next_project_action")
        if nxt:
            out += f" For your current project, suggested: {nxt.get('action_type', '')} — {nxt.get('label', '')}."
    return out


def answer_why_blocked(
    project_id: str | None,
    state: dict[str, Any] | None = None,
    repo_root: Path | str | None = None,
) -> str:
    """Why is this project / goal blocked? Grounded in project_case and progress."""
    state = state or _get_state(repo_root)
    if not project_id:
        pr = state.get("progress_replan", {})
        blocked = pr.get("replan_needed_projects", []) or []
        stalled = pr.get("stalled_projects", [])
        if blocked or stalled:
            return f"Blocked or need-replan projects: {', '.join(blocked[:5] + stalled[:5])}. Run 'workflow-dataset portfolio blocked' and 'workflow-dataset portfolio explain --project <id>' for details."
        return "No specific project given. Say 'Why is founder_case_alpha blocked?' or run 'workflow-dataset portfolio blocked'."
    pc = state.get("project_case", {})
    blockers = (pc.get("project_blockers") or []) if pc.get("active_project_id") == project_id else []
    for b in blockers:
        if b.get("goal_id"):
            return f"Project **{project_id}** has blocked goal **{b.get('goal_id')}**: {b.get('blocked_reason', 'blocked')}. Unblock or replan: 'workflow-dataset progress recovery --project {project_id}'."
    gp = state.get("goal_plan", {})
    if gp and gp.get("blocked_step_count", 0) > 0:
        return f"Current plan has **{gp.get('blocked_step_count')}** blocked step(s). Check planner/executor. Run 'workflow-dataset planner preview --latest'."
    return f"No blocker found for **{project_id}** in current state. Run 'workflow-dataset portfolio explain --project {project_id}' for full context."


def answer_why_this_project(
    project_id: str | None,
    state: dict[str, Any] | None = None,
    repo_root: Path | str | None = None,
) -> str:
    """Why did we choose this project / why this priority? Grounded in portfolio."""
    state = state or _get_state(repo_root)
    if not project_id:
        return "No project specified. Use 'workflow-dataset portfolio explain --project <id>' for priority explanation."
    try:
        from workflow_dataset.portfolio.cli import cmd_explain
        root = Path(repo_root).resolve() if repo_root else None
        return cmd_explain(project_id, repo_root=root) or f"Priority/rank explanation for **{project_id}** (see portfolio explain)."
    except Exception as e:
        return f"Could not explain project: {e}. Run 'workflow-dataset portfolio explain --project {project_id}'."


def answer_what_changed(
    state: dict[str, Any] | None = None,
    repo_root: Path | str | None = None,
) -> str:
    """What changed since yesterday / recently? Grounded in progress and replan signals."""
    state = state or _get_state(repo_root)
    pr = state.get("progress_replan", {})
    signals_count = pr.get("recent_replan_signals_count", 0)
    replan_needed = pr.get("replan_needed_projects", [])[:5]
    stalled = pr.get("stalled_projects", [])[:5]
    advancing = pr.get("advancing_projects", [])[:5]
    out = "Recent changes (progress/replan): "
    if signals_count:
        out += f"**{signals_count}** replan signal(s). "
    if replan_needed:
        out += f"Replan needed: {', '.join(replan_needed)}. "
    if stalled:
        out += f"Stalled: {', '.join(stalled)}. "
    if advancing:
        out += f"Advancing: {', '.join(advancing)}."
    if not (signals_count or replan_needed or stalled or advancing):
        out += "No recent replan/stall signals in state. Run 'workflow-dataset progress board' for full board."
    return out.strip()


def answer_approval_queue(
    state: dict[str, Any] | None = None,
    repo_root: Path | str | None = None,
) -> str:
    """Why is this in the approval queue? What's pending? Grounded in supervised_loop."""
    state = state or _get_state(repo_root)
    sl = state.get("supervised_loop", {})
    if sl.get("error"):
        return f"Supervised loop state error: {sl['error']}."
    pending = sl.get("pending_queue_count", 0)
    next_label = sl.get("next_proposed_action_label", "")
    next_id = sl.get("next_proposed_action_id", "")
    blocked = sl.get("blocked_reason", "")
    if blocked:
        return f"Agent loop is **blocked**: {blocked}. Resolve before approving."
    if pending == 0:
        return "No actions pending in the approval queue. Propose a new cycle or run executor/planner to get proposed actions."
    out = f"There are **{pending}** item(s) pending approval. Next proposed: **{next_label or 'unknown'}**. "
    out += "To approve: 'workflow-dataset agent-loop approve --id " + (next_id or "<queue_id>") + "'."
    return out


def answer_pack_doing(
    pack_ref: str | None,
    state: dict[str, Any] | None = None,
    repo_root: Path | str | None = None,
) -> str:
    """What is this pack doing? High-level from state/packs."""
    state = state or _get_state(repo_root)
    # Packs surface in state indirectly; point to CLI
    return f"Pack **{pack_ref or 'current'}**: Use 'workflow-dataset packs list' and pack-specific commands for purpose and jobs. No pack summary in mission-control state yet."


def answer_status(state: dict[str, Any] | None = None, repo_root: Path | str | None = None) -> str:
    """High-level status overview from mission control."""
    state = state or _get_state(repo_root)
    try:
        from workflow_dataset.mission_control.report import format_mission_control_report
        return format_mission_control_report(state=state)
    except Exception as e:
        return f"Could not build status report: {e}. Run 'workflow-dataset mission-control'."


def answer_artifact_lookup(state: dict[str, Any] | None = None, repo_root: Path | str | None = None) -> str:
    """Summarize active workspace / artifacts from project_case and mission control."""
    state = state or _get_state(repo_root)
    pc = state.get("project_case", {})
    if pc.get("error"):
        return f"Project state error: {pc['error']}."
    proj_id = pc.get("active_project_id")
    gs = pc.get("goal_stack_summary", {})
    linked = pc.get("latest_linked", {}) or {}
    out = f"Active project: **{proj_id or 'none'}**. "
    if gs:
        out += f"Goals: {gs.get('goals_count', 0)} total, {gs.get('active', 0)} active, {gs.get('blocked', 0)} blocked. "
    if linked:
        out += f"Linked: plans={linked.get('plans', 0)}, runs={linked.get('runs', 0)}, artifacts={linked.get('artifacts', 0)}."
    return out or "Run 'workflow-dataset mission-control' for full workspace state."
