"""
M27B: Project graph / summary — active goals, blockers, linked counts, recommended next action.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.project_case.store import (
    load_project,
    get_linked_sessions,
    get_linked_plans,
    get_linked_runs,
    get_linked_artifacts,
    get_linked_skills,
)
from workflow_dataset.project_case.models import ProjectState
from workflow_dataset.project_case.goal_stack import (
    list_goals,
    get_blocked_goals,
    recommended_next_goal,
)


def build_project_state(project_id: str, repo_root: Path | str | None = None) -> ProjectState | None:
    """Build ProjectState summary for a project. Returns None if project not found."""
    proj = load_project(project_id, repo_root)
    if not proj:
        return None
    goals = list_goals(project_id, repo_root)
    active = sum(1 for g in goals if g.status == "active")
    blocked = sum(1 for g in goals if g.status == "blocked")
    deferred = sum(1 for g in goals if g.status == "deferred")
    complete = sum(1 for g in goals if g.status == "complete")
    return ProjectState(
        project_id=project_id,
        state=proj.state,
        active_goals_count=active,
        blocked_goals_count=blocked,
        deferred_goals_count=deferred,
        complete_goals_count=complete,
        linked_sessions_count=len(get_linked_sessions(project_id, repo_root)),
        linked_plans_count=len(get_linked_plans(project_id, repo_root)),
        linked_runs_count=len(get_linked_runs(project_id, repo_root)),
        linked_artifacts_count=len(get_linked_artifacts(project_id, repo_root)),
    )


def get_project_summary(project_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Full summary for mission control or report: state, goals, blockers, links, next action."""
    proj = load_project(project_id, repo_root)
    if not proj:
        return {"error": f"Project not found: {project_id}"}
    state = build_project_state(project_id, repo_root)
    goals = list_goals(project_id, repo_root)
    blocked = get_blocked_goals(project_id, repo_root)
    next_action = recommended_next_goal(project_id, repo_root)
    sessions = get_linked_sessions(project_id, repo_root)
    plans = get_linked_plans(project_id, repo_root)
    runs = get_linked_runs(project_id, repo_root)
    artifacts = get_linked_artifacts(project_id, repo_root)
    return {
        "project_id": project_id,
        "title": proj.title,
        "state": proj.state,
        "project_state": {
            "active_goals_count": state.active_goals_count if state else 0,
            "blocked_goals_count": state.blocked_goals_count if state else 0,
            "deferred_goals_count": state.deferred_goals_count if state else 0,
            "complete_goals_count": state.complete_goals_count if state else 0,
            "linked_sessions_count": state.linked_sessions_count if state else 0,
            "linked_plans_count": state.linked_plans_count if state else 0,
            "linked_runs_count": state.linked_runs_count if state else 0,
            "linked_artifacts_count": state.linked_artifacts_count if state else 0,
        } if state else {},
        "goals_count": len(goals),
        "blocked_goals": [{"goal_id": g.goal_id, "title": g.title, "reason": r} for g, r in blocked],
        "recommended_next_action": {
            "action_type": next_action.action_type,
            "ref": next_action.ref,
            "label": next_action.label,
            "reason": next_action.reason,
        } if next_action else None,
        "latest_linked": {
            "session_id": sessions[-1].session_id if sessions else None,
            "plan_id": plans[-1].plan_id if plans else None,
            "run_id": runs[-1].run_id if runs else None,
            "artifact": artifacts[-1].path_or_label if artifacts else None,
        },
    }
