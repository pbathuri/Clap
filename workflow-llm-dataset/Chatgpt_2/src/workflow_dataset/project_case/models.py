"""
M27A: Project/case and goal stack models. Persistent unit of work; local-first, inspectable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PROJECT_STATES = ("active", "archived", "closed")
GOAL_STATUSES = ("active", "deferred", "complete", "blocked")


@dataclass
class Project:
    """Persistent project or case. Long-lived container for goals, sessions, plans, runs, artifacts."""
    project_id: str
    title: str = ""
    description: str = ""
    state: str = "active"  # active | archived | closed
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "title": self.title,
            "description": self.description,
            "state": self.state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Project:
        return cls(
            project_id=d.get("project_id", ""),
            title=d.get("title", ""),
            description=d.get("description", ""),
            state=d.get("state", "active"),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
        )


@dataclass
class Goal:
    """Long-lived goal in the project goal stack."""
    goal_id: str
    title: str = ""
    description: str = ""
    status: str = "active"  # active | deferred | complete | blocked
    order: int = 0  # lower = higher priority
    blocked_reason: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "order": self.order,
            "blocked_reason": self.blocked_reason,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Goal:
        return cls(
            goal_id=d.get("goal_id", ""),
            title=d.get("title", ""),
            description=d.get("description", ""),
            status=d.get("status", "active"),
            order=int(d.get("order", 0)),
            blocked_reason=d.get("blocked_reason", ""),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
        )


@dataclass
class Subgoal:
    """Subgoal under a parent goal."""
    subgoal_id: str
    parent_goal_id: str = ""
    title: str = ""
    status: str = "active"
    order: int = 0
    blocked_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "subgoal_id": self.subgoal_id,
            "parent_goal_id": self.parent_goal_id,
            "title": self.title,
            "status": self.status,
            "order": self.order,
            "blocked_reason": self.blocked_reason,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Subgoal:
        return cls(
            subgoal_id=d.get("subgoal_id", ""),
            parent_goal_id=d.get("parent_goal_id", ""),
            title=d.get("title", ""),
            status=d.get("status", "active"),
            order=int(d.get("order", 0)),
            blocked_reason=d.get("blocked_reason", ""),
        )


@dataclass
class ProjectMilestone:
    """Named milestone on the project (optional marker)."""
    milestone_id: str
    title: str = ""
    reached_at: str = ""
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "milestone_id": self.milestone_id,
            "title": self.title,
            "reached_at": self.reached_at,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ProjectMilestone:
        return cls(
            milestone_id=d.get("milestone_id", ""),
            title=d.get("title", ""),
            reached_at=d.get("reached_at", ""),
            note=d.get("note", ""),
        )


@dataclass
class ProjectState:
    """Snapshot of project state for display (derived)."""
    project_id: str = ""
    state: str = ""
    active_goals_count: int = 0
    blocked_goals_count: int = 0
    deferred_goals_count: int = 0
    complete_goals_count: int = 0
    linked_sessions_count: int = 0
    linked_plans_count: int = 0
    linked_runs_count: int = 0
    linked_artifacts_count: int = 0


@dataclass
class LinkedSession:
    """Reference to a session attached to the project."""
    session_id: str
    attached_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"session_id": self.session_id, "attached_at": self.attached_at}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LinkedSession:
        return cls(session_id=d.get("session_id", ""), attached_at=d.get("attached_at", ""))


@dataclass
class LinkedPlan:
    """Reference to a plan (e.g. plan_id or path) attached to the project."""
    plan_id: str = ""
    plan_path: str = ""
    attached_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"plan_id": self.plan_id, "plan_path": self.plan_path, "attached_at": self.attached_at}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LinkedPlan:
        return cls(
            plan_id=d.get("plan_id", ""),
            plan_path=d.get("plan_path", ""),
            attached_at=d.get("attached_at", ""),
        )


@dataclass
class LinkedRun:
    """Reference to an execution run attached to the project."""
    run_id: str
    attached_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"run_id": self.run_id, "attached_at": self.attached_at}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LinkedRun:
        return cls(run_id=d.get("run_id", ""), attached_at=d.get("attached_at", ""))


@dataclass
class LinkedArtifact:
    """Reference to an artifact (path or label) attached to the project."""
    path_or_label: str
    attached_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"path_or_label": self.path_or_label, "attached_at": self.attached_at}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LinkedArtifact:
        return cls(path_or_label=d.get("path_or_label", ""), attached_at=d.get("attached_at", ""))


@dataclass
class LinkedSkill:
    """Reference to a skill attached to the project."""
    skill_id: str
    attached_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"skill_id": self.skill_id, "attached_at": self.attached_at}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LinkedSkill:
        return cls(skill_id=d.get("skill_id", ""), attached_at=d.get("attached_at", ""))


@dataclass
class BlockedDependency:
    """A goal or subgoal blocked by a dependency (e.g. another goal or external reason)."""
    goal_id: str = ""
    subgoal_id: str = ""
    reason: str = ""
    depends_on_goal_id: str = ""  # optional: blocked by another goal

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "subgoal_id": self.subgoal_id,
            "reason": self.reason,
            "depends_on_goal_id": self.depends_on_goal_id,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> BlockedDependency:
        return cls(
            goal_id=d.get("goal_id", ""),
            subgoal_id=d.get("subgoal_id", ""),
            reason=d.get("reason", ""),
            depends_on_goal_id=d.get("depends_on_goal_id", ""),
        )


@dataclass
class NextProjectAction:
    """Recommended next action for the project (derived from goal stack and blockers)."""
    action_type: str = ""  # e.g. work_goal, unblock, attach_session, review_plan
    ref: str = ""  # goal_id, run_id, session_id, etc.
    label: str = ""
    reason: str = ""


# ----- M27D.1 Project templates + goal archetypes -----


@dataclass
class GoalArchetype:
    """One goal in a template's default goal stack."""
    goal_id: str
    title: str = ""
    description: str = ""
    order: int = 0
    default_blocked_reason: str = ""  # optional; e.g. "Waiting on approval"

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "title": self.title,
            "description": self.description,
            "order": self.order,
            "default_blocked_reason": self.default_blocked_reason,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> GoalArchetype:
        return cls(
            goal_id=d.get("goal_id", ""),
            title=d.get("title", ""),
            description=d.get("description", ""),
            order=int(d.get("order", 0)),
            default_blocked_reason=d.get("default_blocked_reason", ""),
        )


@dataclass
class ProjectTemplate:
    """Reusable project template: default goal stack, common artifacts, likely blockers, pack associations."""
    template_id: str
    title: str = ""
    description: str = ""
    default_goal_stack: list[GoalArchetype] = field(default_factory=list)
    common_artifacts: list[str] = field(default_factory=list)  # path or label hints
    likely_blockers: list[str] = field(default_factory=list)
    recommended_pack_ids: list[str] = field(default_factory=list)
    recommended_value_pack_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "title": self.title,
            "description": self.description,
            "default_goal_stack": [g.to_dict() for g in self.default_goal_stack],
            "common_artifacts": list(self.common_artifacts),
            "likely_blockers": list(self.likely_blockers),
            "recommended_pack_ids": list(self.recommended_pack_ids),
            "recommended_value_pack_ids": list(self.recommended_value_pack_ids),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ProjectTemplate:
        goals = [GoalArchetype.from_dict(g) for g in d.get("default_goal_stack", [])]
        return cls(
            template_id=d.get("template_id", ""),
            title=d.get("title", ""),
            description=d.get("description", ""),
            default_goal_stack=goals,
            common_artifacts=list(d.get("common_artifacts", [])),
            likely_blockers=list(d.get("likely_blockers", [])),
            recommended_pack_ids=list(d.get("recommended_pack_ids", [])),
            recommended_value_pack_ids=list(d.get("recommended_value_pack_ids", [])),
        )
