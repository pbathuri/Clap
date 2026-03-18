"""
M28: Portfolio router models — portfolio, entry, priority, health, urgency/value scores,
blocker severity, attention recommendation, defer/revisit state. Local, inspectable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Project priority tier for display/sorting (higher = more attention)
PRIORITY_TIERS = ("critical", "high", "medium", "low", "deferred")
BLOCKER_SEVERITY_LEVELS = ("blocked", "partial", "unblocked", "unknown")
PORTFOLIO_HEALTH_LABELS = ("healthy", "stalled", "blocked", "needs_intervention", "unknown")


@dataclass
class UrgencyScore:
    """Urgency: deadlines, recency, time-sensitivity. Higher = more urgent."""
    score: float = 0.0  # 0.0–1.0
    deadline_iso: str = ""
    days_until_deadline: int | None = None
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "deadline_iso": self.deadline_iso,
            "days_until_deadline": self.days_until_deadline,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> UrgencyScore:
        return cls(
            score=float(d.get("score", 0)),
            deadline_iso=str(d.get("deadline_iso", "")),
            days_until_deadline=d.get("days_until_deadline"),
            reason=str(d.get("reason", "")),
        )


@dataclass
class ValueScore:
    """Value: operator goal, impact, progress potential. Higher = more valuable to advance now."""
    score: float = 0.0  # 0.0–1.0
    operator_hint: str = ""  # e.g. "high" | "medium" | "low" from portfolio store
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"score": self.score, "operator_hint": self.operator_hint, "reason": self.reason}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ValueScore:
        return cls(
            score=float(d.get("score", 0)),
            operator_hint=str(d.get("operator_hint", "")),
            reason=str(d.get("reason", "")),
        )


@dataclass
class BlockerSeverity:
    """How blocked the project is: blocked | partial | unblocked | unknown."""
    level: str = "unknown"  # one of BLOCKER_SEVERITY_LEVELS
    blocked_goals_count: int = 0
    blocked_reason_summary: str = ""
    can_advance: bool = False  # true if there is unblocked work

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "blocked_goals_count": self.blocked_goals_count,
            "blocked_reason_summary": self.blocked_reason_summary,
            "can_advance": self.can_advance,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> BlockerSeverity:
        return cls(
            level=str(d.get("level", "unknown")),
            blocked_goals_count=int(d.get("blocked_goals_count", 0)),
            blocked_reason_summary=str(d.get("blocked_reason_summary", "")),
            can_advance=bool(d.get("can_advance", False)),
        )


@dataclass
class ProjectPriority:
    """Composite priority for one project: tier + urgency + value + blocker."""
    project_id: str = ""
    tier: str = "medium"  # one of PRIORITY_TIERS
    urgency: UrgencyScore = field(default_factory=UrgencyScore)
    value: ValueScore = field(default_factory=ValueScore)
    blocker: BlockerSeverity = field(default_factory=BlockerSeverity)
    rank_index: int = 0  # 1-based position in ranked list
    composite_score: float = 0.0  # derived for ordering

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "tier": self.tier,
            "urgency": self.urgency.to_dict(),
            "value": self.value.to_dict(),
            "blocker": self.blocker.to_dict(),
            "rank_index": self.rank_index,
            "composite_score": self.composite_score,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ProjectPriority:
        return cls(
            project_id=str(d.get("project_id", "")),
            tier=str(d.get("tier", "medium")),
            urgency=UrgencyScore.from_dict(d.get("urgency") or {}),
            value=ValueScore.from_dict(d.get("value") or {}),
            blocker=BlockerSeverity.from_dict(d.get("blocker") or {}),
            rank_index=int(d.get("rank_index", 0)),
            composite_score=float(d.get("composite_score", 0)),
        )


@dataclass
class AttentionRecommendation:
    """Recommendation for where to direct attention: project_id + reason."""
    project_id: str = ""
    reason: str = ""
    action_hint: str = ""  # e.g. "advance" | "intervene" | "unblock" | "revisit"
    priority_tier: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "reason": self.reason,
            "action_hint": self.action_hint,
            "priority_tier": self.priority_tier,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AttentionRecommendation:
        return cls(
            project_id=str(d.get("project_id", "")),
            reason=str(d.get("reason", "")),
            action_hint=str(d.get("action_hint", "")),
            priority_tier=str(d.get("priority_tier", "")),
        )


@dataclass
class DeferRevisitState:
    """Portfolio-level defer/revisit: project deferred until date or condition."""
    project_id: str = ""
    deferred_at_iso: str = ""
    revisit_after_iso: str = ""
    reason: str = ""
    active: bool = True  # if False, no longer deferred

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "deferred_at_iso": self.deferred_at_iso,
            "revisit_after_iso": self.revisit_after_iso,
            "reason": self.reason,
            "active": self.active,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DeferRevisitState:
        return cls(
            project_id=str(d.get("project_id", "")),
            deferred_at_iso=str(d.get("deferred_at_iso", "")),
            revisit_after_iso=str(d.get("revisit_after_iso", "")),
            reason=str(d.get("reason", "")),
            active=bool(d.get("active", True)),
        )


# ----- M28D.1 Attention budgets + work windows -----

ATTENTION_RESET_INTERVALS = ("day", "week")
WORK_WINDOW_DAYS = (1, 2, 3, 4, 5, 6, 7)  # 1=Monday
FOCUS_MODE_SWITCH_RULES = ("on_window_end", "on_budget_exhausted", "when_higher_priority_ready", "manual_only")
SWITCH_RULE_TRIGGERS = ("work_window_ended", "attention_budget_cap", "higher_priority_ready", "manual_only")


@dataclass
class AttentionBudget:
    """Per-project attention budget: max time per day/week. Operator-defined; explicit."""
    project_id: str = ""
    minutes_per_day: int | None = None  # None = no cap
    minutes_per_week: int | None = None
    reset_interval: str = "day"  # day | week
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "minutes_per_day": self.minutes_per_day,
            "minutes_per_week": self.minutes_per_week,
            "reset_interval": self.reset_interval,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AttentionBudget":
        return cls(
            project_id=str(d.get("project_id", "")),
            minutes_per_day=int(d["minutes_per_day"]) if d.get("minutes_per_day") is not None else None,
            minutes_per_week=int(d["minutes_per_week"]) if d.get("minutes_per_week") is not None else None,
            reset_interval=str(d.get("reset_interval", "day")),
            note=str(d.get("note", "")),
        )


@dataclass
class WorkWindow:
    """Work window / time slice: suggested duration and optional schedule. Operator-defined."""
    window_id: str = ""
    name: str = ""
    duration_minutes: int = 25  # e.g. Pomodoro
    start_time_local: str = ""  # HH:MM optional
    days_of_week: list[int] = field(default_factory=list)  # 1=Mon .. 7=Sun; empty = every day
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_id": self.window_id,
            "name": self.name,
            "duration_minutes": self.duration_minutes,
            "start_time_local": self.start_time_local,
            "days_of_week": list(self.days_of_week),
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "WorkWindow":
        return cls(
            window_id=str(d.get("window_id", "")),
            name=str(d.get("name", "")),
            duration_minutes=int(d.get("duration_minutes", 25)),
            start_time_local=str(d.get("start_time_local", "")),
            days_of_week=list(d.get("days_of_week") or []),
            note=str(d.get("note", "")),
        )


@dataclass
class FocusMode:
    """Operator-defined focus mode: which projects and when to recommend switching."""
    mode_id: str = ""
    name: str = ""
    description: str = ""
    default_project_id: str = ""  # optional; suggested when entering mode
    project_ids: list[str] = field(default_factory=list)  # allowed in this mode; empty = all
    switch_rules: list[str] = field(default_factory=list)  # on_window_end, on_budget_exhausted, when_higher_priority_ready, manual_only
    active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode_id": self.mode_id,
            "name": self.name,
            "description": self.description,
            "default_project_id": self.default_project_id,
            "project_ids": list(self.project_ids),
            "switch_rules": list(self.switch_rules),
            "active": self.active,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "FocusMode":
        return cls(
            mode_id=str(d.get("mode_id", "")),
            name=str(d.get("name", "")),
            description=str(d.get("description", "")),
            default_project_id=str(d.get("default_project_id", "")),
            project_ids=list(d.get("project_ids") or []),
            switch_rules=list(d.get("switch_rules") or []),
            active=bool(d.get("active", True)),
        )


@dataclass
class SwitchRecommendation:
    """Recommendation to switch project: rule that triggered, reason, suggested next. Explicit, operator-readable."""
    recommend_switch: bool = False
    reason: str = ""
    suggested_project_id: str = ""
    rule_triggered: str = ""  # one of SWITCH_RULE_TRIGGERS
    current_project_id: str = ""
    work_window_remaining_minutes: int | None = None  # None = not in a tracked window
    focus_mode_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommend_switch": self.recommend_switch,
            "reason": self.reason,
            "suggested_project_id": self.suggested_project_id,
            "rule_triggered": self.rule_triggered,
            "current_project_id": self.current_project_id,
            "work_window_remaining_minutes": self.work_window_remaining_minutes,
            "focus_mode_id": self.focus_mode_id,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SwitchRecommendation":
        return cls(
            recommend_switch=bool(d.get("recommend_switch", False)),
            reason=str(d.get("reason", "")),
            suggested_project_id=str(d.get("suggested_project_id", "")),
            rule_triggered=str(d.get("rule_triggered", "")),
            current_project_id=str(d.get("current_project_id", "")),
            work_window_remaining_minutes=d.get("work_window_remaining_minutes"),
            focus_mode_id=str(d.get("focus_mode_id", "")),
        )


@dataclass
class WorkWindowRecommendation:
    """Current work window suggestion: which project, duration left, next suggested. Operator-readable."""
    project_id: str = ""
    window_id: str = ""
    window_name: str = ""
    duration_minutes: int = 25
    remaining_minutes: int | None = None  # None = not tracking
    suggested_next_project_id: str = ""
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "window_id": self.window_id,
            "window_name": self.window_name,
            "duration_minutes": self.duration_minutes,
            "remaining_minutes": self.remaining_minutes,
            "suggested_next_project_id": self.suggested_next_project_id,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "WorkWindowRecommendation":
        return cls(
            project_id=str(d.get("project_id", "")),
            window_id=str(d.get("window_id", "")),
            window_name=str(d.get("window_name", "")),
            duration_minutes=int(d.get("duration_minutes", 25)),
            remaining_minutes=d.get("remaining_minutes"),
            suggested_next_project_id=str(d.get("suggested_next_project_id", "")),
            reason=str(d.get("reason", "")),
        )


@dataclass
class PortfolioHealth:
    """Portfolio-wide health summary."""
    total_active: int = 0
    stalled_count: int = 0
    blocked_count: int = 0
    advancing_count: int = 0
    needs_intervention_count: int = 0
    ready_for_execution_count: int = 0
    labels: list[str] = field(default_factory=list)  # e.g. ["2 stalled", "1 blocked"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_active": self.total_active,
            "stalled_count": self.stalled_count,
            "blocked_count": self.blocked_count,
            "advancing_count": self.advancing_count,
            "needs_intervention_count": self.needs_intervention_count,
            "ready_for_execution_count": self.ready_for_execution_count,
            "labels": list(self.labels),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> PortfolioHealth:
        return cls(
            total_active=int(d.get("total_active", 0)),
            stalled_count=int(d.get("stalled_count", 0)),
            blocked_count=int(d.get("blocked_count", 0)),
            advancing_count=int(d.get("advancing_count", 0)),
            needs_intervention_count=int(d.get("needs_intervention_count", 0)),
            ready_for_execution_count=int(d.get("ready_for_execution_count", 0)),
            labels=list(d.get("labels") or []),
        )


@dataclass
class PortfolioEntry:
    """One project in the portfolio view: id, title, state, priority, health label, ready."""
    project_id: str = ""
    title: str = ""
    state: str = "active"
    priority: ProjectPriority = field(default_factory=ProjectPriority)
    health_label: str = "unknown"  # one of PORTFOLIO_HEALTH_LABELS
    is_current: bool = False
    is_stalled: bool = False
    is_blocked: bool = False
    is_ready_for_execution: bool = False
    needs_intervention: bool = False
    deferred: DeferRevisitState | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "title": self.title,
            "state": self.state,
            "priority": self.priority.to_dict(),
            "health_label": self.health_label,
            "is_current": self.is_current,
            "is_stalled": self.is_stalled,
            "is_blocked": self.is_blocked,
            "is_ready_for_execution": self.is_ready_for_execution,
            "needs_intervention": self.needs_intervention,
            "deferred": self.deferred.to_dict() if self.deferred else None,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> PortfolioEntry:
        defr = d.get("deferred")
        return cls(
            project_id=str(d.get("project_id", "")),
            title=str(d.get("title", "")),
            state=str(d.get("state", "active")),
            priority=ProjectPriority.from_dict(d.get("priority") or {}),
            health_label=str(d.get("health_label", "unknown")),
            is_current=bool(d.get("is_current", False)),
            is_stalled=bool(d.get("is_stalled", False)),
            is_blocked=bool(d.get("is_blocked", False)),
            is_ready_for_execution=bool(d.get("is_ready_for_execution", False)),
            needs_intervention=bool(d.get("needs_intervention", False)),
            deferred=DeferRevisitState.from_dict(defr) if defr else None,
        )


@dataclass
class Portfolio:
    """Full portfolio snapshot: entries (ranked), health, next recommendation, etc."""
    entries: list[PortfolioEntry] = field(default_factory=list)
    health: PortfolioHealth = field(default_factory=PortfolioHealth)
    next_recommended_project: AttentionRecommendation | None = None
    top_intervention: AttentionRecommendation | None = None
    most_blocked_project_id: str = ""
    most_valuable_ready_project_id: str = ""
    updated_at_iso: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "entries": [e.to_dict() for e in self.entries],
            "health": self.health.to_dict(),
            "next_recommended_project": self.next_recommended_project.to_dict() if self.next_recommended_project else None,
            "top_intervention": self.top_intervention.to_dict() if self.top_intervention else None,
            "most_blocked_project_id": self.most_blocked_project_id,
            "most_valuable_ready_project_id": self.most_valuable_ready_project_id,
            "updated_at_iso": self.updated_at_iso,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Portfolio:
        entries = [PortfolioEntry.from_dict(x) for x in d.get("entries", [])]
        health = PortfolioHealth.from_dict(d.get("health") or {})
        nr = d.get("next_recommended_project")
        ti = d.get("top_intervention")
        return cls(
            entries=entries,
            health=health,
            next_recommended_project=AttentionRecommendation.from_dict(nr) if nr else None,
            top_intervention=AttentionRecommendation.from_dict(ti) if ti else None,
            most_blocked_project_id=str(d.get("most_blocked_project_id", "")),
            most_valuable_ready_project_id=str(d.get("most_valuable_ready_project_id", "")),
            updated_at_iso=str(d.get("updated_at_iso", "")),
        )
