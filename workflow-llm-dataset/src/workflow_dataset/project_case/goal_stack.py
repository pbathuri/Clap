"""
M27C: Goal stack — ordered goals, active/deferred/complete/blocked, dependencies, recommended next goal.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.project_case.models import Goal, Subgoal, BlockedDependency, NextProjectAction
from workflow_dataset.project_case.store import get_project_dir, load_project

GOALS_FILE = "goals.json"


def _load_goals_data(project_id: str, repo_root: Path | str | None) -> dict[str, Any]:
    path = get_project_dir(project_id, repo_root) / GOALS_FILE
    if not path.exists():
        return {"goals": [], "subgoals": [], "goal_dependencies": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"goals": [], "subgoals": [], "goal_dependencies": []}


def _save_goals_data(project_id: str, data: dict[str, Any], repo_root: Path | str | None) -> Path:
    root = get_project_dir(project_id, repo_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / GOALS_FILE
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def list_goals(project_id: str, repo_root: Path | str | None = None) -> list[Goal]:
    """Return goals for project, sorted by order then created_at."""
    data = _load_goals_data(project_id, repo_root)
    goals = [Goal.from_dict(g) for g in data.get("goals", [])]
    goals.sort(key=lambda g: (g.order, g.created_at or ""))
    return goals


def list_subgoals(project_id: str, parent_goal_id: str | None = None, repo_root: Path | str | None = None) -> list[Subgoal]:
    data = _load_goals_data(project_id, repo_root)
    subgoals = [Subgoal.from_dict(s) for s in data.get("subgoals", [])]
    if parent_goal_id:
        subgoals = [s for s in subgoals if s.parent_goal_id == parent_goal_id]
    subgoals.sort(key=lambda s: (s.order, s.subgoal_id))
    return subgoals


def add_goal(
    project_id: str,
    goal_id: str,
    title: str = "",
    description: str = "",
    order: int | None = None,
    repo_root: Path | str | None = None,
) -> Goal | None:
    """Add a goal to the stack. If order is None, append. Returns Goal or None if project missing."""
    if not load_project(project_id, repo_root):
        return None
    data = _load_goals_data(project_id, repo_root)
    goals = [Goal.from_dict(g) for g in data.get("goals", [])]
    if any(g.goal_id == goal_id for g in goals):
        return next(g for g in goals if g.goal_id == goal_id)
    max_order = max([g.order for g in goals], default=-1)
    now = utc_now_iso()
    goal = Goal(
        goal_id=goal_id,
        title=title or goal_id,
        description=description,
        status="active",
        order=order if order is not None else max_order + 1,
        created_at=now,
        updated_at=now,
    )
    goals.append(goal)
    data["goals"] = [g.to_dict() for g in goals]
    _save_goals_data(project_id, data, repo_root)
    return goal


def add_subgoal(
    project_id: str,
    subgoal_id: str,
    parent_goal_id: str,
    title: str = "",
    order: int | None = None,
    repo_root: Path | str | None = None,
) -> Subgoal | None:
    if not load_project(project_id, repo_root):
        return None
    data = _load_goals_data(project_id, repo_root)
    subgoals = [Subgoal.from_dict(s) for s in data.get("subgoals", [])]
    if any(s.subgoal_id == subgoal_id for s in subgoals):
        return next(s for s in subgoals if s.subgoal_id == subgoal_id)
    siblings = [s for s in subgoals if s.parent_goal_id == parent_goal_id]
    max_order = max([s.order for s in siblings], default=-1)
    sub = Subgoal(
        subgoal_id=subgoal_id,
        parent_goal_id=parent_goal_id,
        title=title or subgoal_id,
        status="active",
        order=order if order is not None else max_order + 1,
    )
    subgoals.append(sub)
    data["subgoals"] = [s.to_dict() for s in subgoals]
    _save_goals_data(project_id, data, repo_root)
    return sub


def set_goal_order(project_id: str, goal_id: str, order: int, repo_root: Path | str | None = None) -> bool:
    """Set order of a goal. Returns True if goal exists."""
    data = _load_goals_data(project_id, repo_root)
    goals = [Goal.from_dict(g) for g in data.get("goals", [])]
    for g in goals:
        if g.goal_id == goal_id:
            g.order = order
            g.updated_at = utc_now_iso()
            data["goals"] = [x.to_dict() for x in goals]
            _save_goals_data(project_id, data, repo_root)
            return True
    return False


def set_goal_status(
    project_id: str,
    goal_id: str,
    status: str,
    blocked_reason: str = "",
    repo_root: Path | str | None = None,
) -> bool:
    """Set status of a goal (active | deferred | complete | blocked). Returns True if goal exists."""
    data = _load_goals_data(project_id, repo_root)
    goals = [Goal.from_dict(g) for g in data.get("goals", [])]
    for g in goals:
        if g.goal_id == goal_id:
            g.status = status
            if blocked_reason:
                g.blocked_reason = blocked_reason
            g.updated_at = utc_now_iso()
            data["goals"] = [x.to_dict() for x in goals]
            _save_goals_data(project_id, data, repo_root)
            return True
    return False


def set_subgoal_status(
    project_id: str,
    subgoal_id: str,
    status: str,
    blocked_reason: str = "",
    repo_root: Path | str | None = None,
) -> bool:
    data = _load_goals_data(project_id, repo_root)
    subgoals = [Subgoal.from_dict(s) for s in data.get("subgoals", [])]
    for s in subgoals:
        if s.subgoal_id == subgoal_id:
            s.status = status
            if blocked_reason:
                s.blocked_reason = blocked_reason
            data["subgoals"] = [x.to_dict() for x in subgoals]
            _save_goals_data(project_id, data, repo_root)
            return True
    return False


def add_goal_dependency(
    project_id: str,
    goal_id: str,
    depends_on_goal_id: str,
    reason: str = "",
    repo_root: Path | str | None = None,
) -> bool:
    """Record that goal_id depends on depends_on_goal_id (for blocker reporting)."""
    if not load_project(project_id, repo_root):
        return False
    data = _load_goals_data(project_id, repo_root)
    deps = [BlockedDependency.from_dict(d) for d in data.get("goal_dependencies", [])]
    deps.append(BlockedDependency(goal_id=goal_id, depends_on_goal_id=depends_on_goal_id, reason=reason))
    data["goal_dependencies"] = [d.to_dict() for d in deps]
    _save_goals_data(project_id, data, repo_root)
    return True


def get_blocked_goals(project_id: str, repo_root: Path | str | None = None) -> list[tuple[Goal, str]]:
    """Return list of (goal, blocked_reason) for goals with status=blocked or blocked_reason set."""
    goals = list_goals(project_id, repo_root)
    out = []
    for g in goals:
        if g.status == "blocked" or g.blocked_reason:
            out.append((g, g.blocked_reason or "blocked"))
    return out


def recommended_next_goal(project_id: str, repo_root: Path | str | None = None) -> NextProjectAction | None:
    """Recommend next goal to work on: first active goal by order, or first blocked with reason."""
    goals = list_goals(project_id, repo_root)
    active = [g for g in goals if g.status == "active"]
    if active:
        active.sort(key=lambda g: g.order)
        return NextProjectAction(
            action_type="work_goal",
            ref=active[0].goal_id,
            label=active[0].title or active[0].goal_id,
            reason="First active goal in stack",
        )
    blocked = [g for g in goals if g.status == "blocked"]
    if blocked:
        blocked.sort(key=lambda g: g.order)
        return NextProjectAction(
            action_type="unblock",
            ref=blocked[0].goal_id,
            label=blocked[0].title or blocked[0].goal_id,
            reason=blocked[0].blocked_reason or "Goal is blocked",
        )
    return None
