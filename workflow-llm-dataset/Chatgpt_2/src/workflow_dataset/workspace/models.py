"""
M29: Unified workspace shell — information architecture, navigation state, view model.
Local-first; read-only aggregation; no hidden autonomy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Top-level workspace areas (Phase A). M29 integration: conversational_ask, timeline, intervention_inbox.
WORKSPACE_AREAS = (
    "home",
    "portfolio",
    "projects",
    "active_session",
    "approvals_policy",
    "worker_lanes",
    "packs_runtime",
    "artifacts_outcomes",
    "rollout_support",
    "settings_health",
    "conversational_ask",
    "timeline",
    "intervention_inbox",
)

# View identifiers for navigation (Phase B). M29 integration: ask (Pane 3), timeline, inbox (Pane 2).
WORKSPACE_VIEWS = (
    "home",
    "portfolio",
    "project",
    "session",
    "approvals",
    "policy",
    "lanes",
    "packs",
    "artifacts",
    "outcomes",
    "rollout",
    "settings",
    "ask",      # M29E–M29H conversational command center
    "timeline", # M29I–M29L activity timeline
    "inbox",    # M29I–M29L intervention inbox
)


@dataclass
class WorkspaceArea:
    """One top-level area in the workspace IA."""
    area_id: str = ""  # one of WORKSPACE_AREAS
    label: str = ""
    summary: str = ""
    command_hint: str = ""  # e.g. "workflow-dataset portfolio status"
    count: int = 0  # optional count (e.g. active projects)


@dataclass
class ActiveWorkContext:
    """Current active work context: project, goal, session, approvals, blocked, artifacts, next."""
    active_project_id: str = ""
    active_project_title: str = ""
    active_goal_id: str = ""
    active_goal_text: str = ""
    active_session_id: str = ""
    active_session_pack_id: str = ""
    queued_approvals_count: int = 0
    queued_approval_ids: list[str] = field(default_factory=list)
    blocked_items_count: int = 0
    blocked_summary: list[str] = field(default_factory=list)
    recent_artifacts_count: int = 0
    recent_artifact_refs: list[str] = field(default_factory=list)
    next_recommended_action: str = ""
    next_recommended_detail: str = ""
    next_recommended_project_id: str = ""
    portfolio_next_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_project_id": self.active_project_id,
            "active_project_title": self.active_project_title,
            "active_goal_id": self.active_goal_id,
            "active_goal_text": self.active_goal_text[:200] if self.active_goal_text else "",
            "active_session_id": self.active_session_id,
            "active_session_pack_id": self.active_session_pack_id,
            "queued_approvals_count": self.queued_approvals_count,
            "queued_approval_ids": list(self.queued_approval_ids),
            "blocked_items_count": self.blocked_items_count,
            "blocked_summary": list(self.blocked_summary),
            "recent_artifacts_count": self.recent_artifacts_count,
            "recent_artifact_refs": list(self.recent_artifact_refs),
            "next_recommended_action": self.next_recommended_action,
            "next_recommended_detail": self.next_recommended_detail,
            "next_recommended_project_id": self.next_recommended_project_id,
            "portfolio_next_reason": self.portfolio_next_reason,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ActiveWorkContext":
        return cls(
            active_project_id=str(d.get("active_project_id", "")),
            active_project_title=str(d.get("active_project_title", "")),
            active_goal_id=str(d.get("active_goal_id", "")),
            active_goal_text=str(d.get("active_goal_text", "")),
            active_session_id=str(d.get("active_session_id", "")),
            active_session_pack_id=str(d.get("active_session_pack_id", "")),
            queued_approvals_count=int(d.get("queued_approvals_count", 0)),
            queued_approval_ids=list(d.get("queued_approval_ids", [])),
            blocked_items_count=int(d.get("blocked_items_count", 0)),
            blocked_summary=list(d.get("blocked_summary", [])),
            recent_artifacts_count=int(d.get("recent_artifacts_count", 0)),
            recent_artifact_refs=list(d.get("recent_artifact_refs", [])),
            next_recommended_action=str(d.get("next_recommended_action", "")),
            next_recommended_detail=str(d.get("next_recommended_detail", "")),
            next_recommended_project_id=str(d.get("next_recommended_project_id", "")),
            portfolio_next_reason=str(d.get("portfolio_next_reason", "")),
        )


@dataclass
class NavigationState:
    """Current workspace view and context for navigation (Phase B)."""
    current_view: str = "home"  # one of WORKSPACE_VIEWS
    current_project_id: str = ""
    current_session_id: str = ""
    current_selection: str = ""  # e.g. lane_id, artifact ref
    breadcrumbs: list[str] = field(default_factory=list)  # e.g. ["Home", "Portfolio", "founder_case_alpha"]
    quick_actions: list[dict[str, str]] = field(default_factory=list)  # [{label, command}]

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_view": self.current_view,
            "current_project_id": self.current_project_id,
            "current_session_id": self.current_session_id,
            "current_selection": self.current_selection,
            "breadcrumbs": list(self.breadcrumbs),
            "quick_actions": list(self.quick_actions),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "NavigationState":
        return cls(
            current_view=str(d.get("current_view", "home")),
            current_project_id=str(d.get("current_project_id", "")),
            current_session_id=str(d.get("current_session_id", "")),
            current_selection=str(d.get("current_selection", "")),
            breadcrumbs=list(d.get("breadcrumbs", [])),
            quick_actions=list(d.get("quick_actions", [])),
        )


# Section keys for home composition (M29D.1 presets)
HOME_SECTION_WHERE = "where_you_are"
HOME_SECTION_TOP_PRIORITY = "top_priority_next"
HOME_SECTION_APPROVALS = "approvals"
HOME_SECTION_BLOCKED = "blocked"
HOME_SECTION_RECENT = "recent"
HOME_SECTION_TRUST_HEALTH = "trust_health"
HOME_SECTION_AREAS = "areas"
HOME_SECTION_QUICK = "quick"
HOME_SECTIONS_DEFAULT = (
    HOME_SECTION_WHERE,
    HOME_SECTION_TOP_PRIORITY,
    HOME_SECTION_APPROVALS,
    HOME_SECTION_BLOCKED,
    HOME_SECTION_RECENT,
    HOME_SECTION_TRUST_HEALTH,
    HOME_SECTION_AREAS,
    HOME_SECTION_QUICK,
)


@dataclass
class WorkspacePreset:
    """M29D.1: Role-specific workspace layout — home composition, quick actions, first view."""
    preset_id: str = ""
    label: str = ""
    description: str = ""
    home_section_order: tuple[str, ...] = ()  # section ids; empty = use default order
    default_quick_actions: tuple[dict[str, str], ...] = ()  # [{label, command}]
    priority_widgets: tuple[str, ...] = ()  # section ids to emphasize or show first
    recommended_first_view: str = "home"  # view to suggest on open

    def to_dict(self) -> dict[str, Any]:
        return {
            "preset_id": self.preset_id,
            "label": self.label,
            "description": self.description,
            "home_section_order": list(self.home_section_order),
            "default_quick_actions": list(self.default_quick_actions),
            "priority_widgets": list(self.priority_widgets),
            "recommended_first_view": self.recommended_first_view,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "WorkspacePreset":
        qa = d.get("default_quick_actions", [])
        return cls(
            preset_id=str(d.get("preset_id", "")),
            label=str(d.get("label", "")),
            description=str(d.get("description", "")),
            home_section_order=tuple(d.get("home_section_order", [])),
            default_quick_actions=tuple(dict(x) for x in qa),
            priority_widgets=tuple(d.get("priority_widgets", [])),
            recommended_first_view=str(d.get("recommended_first_view", "home")),
        )


@dataclass
class WorkspaceHomeSnapshot:
    """Unified home snapshot: context + areas + summary (Phase C)."""
    context: ActiveWorkContext = field(default_factory=ActiveWorkContext)
    navigation: NavigationState = field(default_factory=NavigationState)
    areas: list[WorkspaceArea] = field(default_factory=list)
    top_priority_project_id: str = ""
    approval_queue_summary: str = ""
    blocked_summary: str = ""
    recent_activity_summary: str = ""
    trust_health_summary: str = ""
    updated_at_iso: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "context": self.context.to_dict(),
            "navigation": self.navigation.to_dict(),
            "areas": [{"area_id": a.area_id, "label": a.label, "summary": a.summary[:200], "command_hint": a.command_hint, "count": a.count} for a in self.areas],
            "top_priority_project_id": self.top_priority_project_id,
            "approval_queue_summary": self.approval_queue_summary,
            "blocked_summary": self.blocked_summary,
            "recent_activity_summary": self.recent_activity_summary,
            "trust_health_summary": self.trust_health_summary,
            "updated_at_iso": self.updated_at_iso,
        }
