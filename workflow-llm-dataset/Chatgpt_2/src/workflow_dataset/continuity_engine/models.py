"""
M36I–M36L: Continuity engine models.
Continuity snapshot, change since last session, morning brief, shutdown summary,
resume card, interrupted-work chain, carry-forward item, unresolved blocker continuation,
next-session recommendation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContinuitySnapshot:
    """Snapshot of continuity-relevant state at a point in time."""
    snapshot_id: str = ""
    as_of_utc: str = ""
    last_session_end_utc: str = ""
    workday_state: str = ""
    active_project_id: str = ""
    top_queue_item_ref: str = ""
    pending_approvals_count: int = 0
    automation_pending_count: int = 0
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "as_of_utc": self.as_of_utc,
            "last_session_end_utc": self.last_session_end_utc,
            "workday_state": self.workday_state,
            "active_project_id": self.active_project_id,
            "top_queue_item_ref": self.top_queue_item_ref,
            "pending_approvals_count": self.pending_approvals_count,
            "automation_pending_count": self.automation_pending_count,
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ContinuitySnapshot":
        return cls(
            snapshot_id=d.get("snapshot_id", ""),
            as_of_utc=d.get("as_of_utc", ""),
            last_session_end_utc=d.get("last_session_end_utc", ""),
            workday_state=d.get("workday_state", ""),
            active_project_id=d.get("active_project_id", ""),
            top_queue_item_ref=d.get("top_queue_item_ref", ""),
            pending_approvals_count=int(d.get("pending_approvals_count", 0)),
            automation_pending_count=int(d.get("automation_pending_count", 0)),
            details=dict(d.get("details", {})),
        )


@dataclass
class ChangeSinceLastSession:
    """What changed since the last active session."""
    last_session_end_utc: str = ""
    generated_at_utc: str = ""
    queue_items_added: int = 0
    queue_items_resolved: int = 0
    automation_outcomes: list[str] = field(default_factory=list)
    approvals_urgent: list[str] = field(default_factory=list)
    projects_stalled: list[str] = field(default_factory=list)
    summary_lines: list[str] = field(default_factory=list)
    has_changes: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_session_end_utc": self.last_session_end_utc,
            "generated_at_utc": self.generated_at_utc,
            "queue_items_added": self.queue_items_added,
            "queue_items_resolved": self.queue_items_resolved,
            "automation_outcomes": list(self.automation_outcomes),
            "approvals_urgent": list(self.approvals_urgent),
            "projects_stalled": list(self.projects_stalled),
            "summary_lines": list(self.summary_lines),
            "has_changes": self.has_changes,
        }


@dataclass
class MorningEntryBrief:
    """Morning entry flow output: change, top queue, automations, approvals, stalled, first mode/action."""
    brief_id: str = ""
    generated_at_utc: str = ""
    change_since_last: ChangeSinceLastSession | None = None
    top_queue_items: list[dict[str, Any]] = field(default_factory=list)
    automation_outcomes_summary: list[str] = field(default_factory=list)
    urgent_approvals: list[str] = field(default_factory=list)
    stalled_projects: list[str] = field(default_factory=list)
    recommended_first_mode: str = ""
    recommended_first_action: str = ""
    recommended_first_command: str = ""
    handoff_label: str = ""
    handoff_command: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "brief_id": self.brief_id,
            "generated_at_utc": self.generated_at_utc,
            "change_since_last": self.change_since_last.to_dict() if self.change_since_last else {},
            "top_queue_items": list(self.top_queue_items),
            "automation_outcomes_summary": list(self.automation_outcomes_summary),
            "urgent_approvals": list(self.urgent_approvals),
            "stalled_projects": list(self.stalled_projects),
            "recommended_first_mode": self.recommended_first_mode,
            "recommended_first_action": self.recommended_first_action,
            "recommended_first_command": self.recommended_first_command,
            "handoff_label": self.handoff_label,
            "handoff_command": self.handoff_command,
        }


@dataclass
class ShutdownSummary:
    """Shutdown / wrap-up flow output: completed, unresolved, carry-forward, tomorrow start, blocked."""
    summary_id: str = ""
    generated_at_utc: str = ""
    day_id: str = ""
    completed_work: list[str] = field(default_factory=list)
    unresolved_items: list[dict[str, Any]] = field(default_factory=list)
    carry_forward_items: list[dict[str, Any]] = field(default_factory=list)
    tomorrow_likely_start: str = ""
    tomorrow_first_action: str = ""
    blocked_or_high_risk: list[str] = field(default_factory=list)
    end_of_day_readiness: str = ""  # ready | has_unresolved | has_blocked

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary_id": self.summary_id,
            "generated_at_utc": self.generated_at_utc,
            "day_id": self.day_id,
            "completed_work": list(self.completed_work),
            "unresolved_items": list(self.unresolved_items),
            "carry_forward_items": list(self.carry_forward_items),
            "tomorrow_likely_start": self.tomorrow_likely_start,
            "tomorrow_first_action": self.tomorrow_first_action,
            "blocked_or_high_risk": list(self.blocked_or_high_risk),
            "end_of_day_readiness": self.end_of_day_readiness,
        }


@dataclass
class InterruptedWorkChain:
    """Chain of work that was interrupted: project/session/episode refs and next step."""
    chain_id: str = ""
    project_id: str = ""
    session_ref: str = ""
    episode_ref: str = ""
    last_activity_utc: str = ""
    inferred_what_doing: str = ""
    next_step_summary: str = ""
    artifact_refs: list[str] = field(default_factory=list)
    confidence: str = ""  # high | medium | low

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "project_id": self.project_id,
            "session_ref": self.session_ref,
            "episode_ref": self.episode_ref,
            "last_activity_utc": self.last_activity_utc,
            "inferred_what_doing": self.inferred_what_doing,
            "next_step_summary": self.next_step_summary,
            "artifact_refs": list(self.artifact_refs),
            "confidence": self.confidence,
        }


@dataclass
class ResumeCard:
    """Resume flow output: interrupted work, reconnect refs, artifacts, next steps, explanation."""
    card_id: str = ""
    generated_at_utc: str = ""
    interrupted_work: InterruptedWorkChain | None = None
    resume_target_label: str = ""
    resume_target_command: str = ""
    what_system_thinks_doing: str = ""
    what_remains: list[str] = field(default_factory=list)
    suggested_first_action: str = ""
    # M44: optional memory-backed context (prior_cases, rationale_summary)
    memory_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "card_id": self.card_id,
            "generated_at_utc": self.generated_at_utc,
            "interrupted_work": self.interrupted_work.to_dict() if self.interrupted_work else {},
            "resume_target_label": self.resume_target_label,
            "resume_target_command": self.resume_target_command,
            "what_system_thinks_doing": self.what_system_thinks_doing,
            "what_remains": list(self.what_remains),
            "suggested_first_action": self.suggested_first_action,
            "memory_context": dict(self.memory_context),
        }


# M36L.1: carry_forward_class = urgent | optional | automated_follow_up
CARRY_FORWARD_CLASS_URGENT = "urgent"
CARRY_FORWARD_CLASS_OPTIONAL = "optional"
CARRY_FORWARD_CLASS_AUTOMATED_FOLLOW_UP = "automated_follow_up"


@dataclass
class CarryForwardItem:
    """Item to carry into the next session."""
    item_id: str = ""
    kind: str = ""  # unresolved | blocker | follow_up | reminder
    carry_forward_class: str = ""  # M36L.1: urgent | optional | automated_follow_up
    label: str = ""
    detail: str = ""
    ref: str = ""
    command: str = ""
    created_at_utc: str = ""
    priority: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "kind": self.kind,
            "carry_forward_class": self.carry_forward_class,
            "label": self.label,
            "detail": self.detail,
            "ref": self.ref,
            "command": self.command,
            "created_at_utc": self.created_at_utc,
            "priority": self.priority,
        }


@dataclass
class UnresolvedBlockerContinuation:
    """Unresolved blocker carried into today."""
    blocker_id: str = ""
    label: str = ""
    reason: str = ""
    ref: str = ""
    carried_since_utc: str = ""
    suggested_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "blocker_id": self.blocker_id,
            "label": self.label,
            "reason": self.reason,
            "ref": self.ref,
            "carried_since_utc": self.carried_since_utc,
            "suggested_action": self.suggested_action,
        }


@dataclass
class NextSessionRecommendation:
    """Recommendation for next session start (from shutdown)."""
    generated_at_utc: str = ""
    day_id: str = ""
    likely_start_context: str = ""
    first_action_label: str = ""
    first_action_command: str = ""
    carry_forward_count: int = 0
    blocked_count: int = 0
    # M36L.1: clearer next-day operating recommendation
    urgent_carry_forward_count: int = 0
    optional_carry_forward_count: int = 0
    automated_follow_up_count: int = 0
    operating_mode: str = ""  # e.g. startup | review_first | deep_work_first
    rationale_lines: list[str] = field(default_factory=list)
    # M44: optional memory-backed context (prior_cases, rationale_summary)
    memory_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at_utc": self.generated_at_utc,
            "day_id": self.day_id,
            "likely_start_context": self.likely_start_context,
            "first_action_label": self.first_action_label,
            "first_action_command": self.first_action_command,
            "carry_forward_count": self.carry_forward_count,
            "blocked_count": self.blocked_count,
            "urgent_carry_forward_count": self.urgent_carry_forward_count,
            "optional_carry_forward_count": self.optional_carry_forward_count,
            "automated_follow_up_count": self.automated_follow_up_count,
            "operating_mode": self.operating_mode,
            "rationale_lines": list(self.rationale_lines),
            "memory_context": dict(self.memory_context),
        }


@dataclass
class RhythmPhase:
    """Single phase in a daily rhythm template (e.g. morning_check, deep_work, review, wrap_up)."""
    phase_id: str = ""
    label: str = ""
    suggested_duration_min: int = 0
    default_first_action_command: str = ""
    order: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase_id": self.phase_id,
            "label": self.label,
            "suggested_duration_min": self.suggested_duration_min,
            "default_first_action_command": self.default_first_action_command,
            "order": self.order,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RhythmPhase":
        return cls(
            phase_id=str(d.get("phase_id", "")),
            label=str(d.get("label", "")),
            suggested_duration_min=int(d.get("suggested_duration_min", 0)),
            default_first_action_command=str(d.get("default_first_action_command", "")),
            order=int(d.get("order", 0)),
        )


@dataclass
class DailyRhythmTemplate:
    """M36L.1: Daily rhythm template — named sequence of phases with suggested first actions."""
    template_id: str = ""
    name: str = ""
    description: str = ""
    phases: list[RhythmPhase] = field(default_factory=list)
    default_first_phase_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "phases": [p.to_dict() for p in self.phases],
            "default_first_phase_id": self.default_first_phase_id,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "DailyRhythmTemplate":
        phases = [RhythmPhase.from_dict(p) for p in (d.get("phases") or [])]
        return cls(
            template_id=str(d.get("template_id", "")),
            name=str(d.get("name", "")),
            description=str(d.get("description", "")),
            phases=phases,
            default_first_phase_id=str(d.get("default_first_phase_id", "")),
        )


@dataclass
class CarryForwardPolicyOutput:
    """M36L.1: Result of applying carry-forward policy — urgent, optional, automated_follow_up."""
    urgent_items: list[CarryForwardItem] = field(default_factory=list)
    optional_items: list[CarryForwardItem] = field(default_factory=list)
    automated_follow_up_items: list[CarryForwardItem] = field(default_factory=list)
    rationale_lines: list[str] = field(default_factory=list)
    generated_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "urgent_items": [i.to_dict() for i in self.urgent_items],
            "optional_items": [i.to_dict() for i in self.optional_items],
            "automated_follow_up_items": [i.to_dict() for i in self.automated_follow_up_items],
            "rationale_lines": list(self.rationale_lines),
            "generated_at_utc": self.generated_at_utc,
        }


@dataclass
class NextDayOperatingRecommendation:
    """M36L.1: Clearer next-day operating recommendation (from shutdown + policy)."""
    operating_mode: str = ""
    first_action_label: str = ""
    first_action_command: str = ""
    urgent_count: int = 0
    optional_count: int = 0
    automated_follow_up_count: int = 0
    rationale_lines: list[str] = field(default_factory=list)
    suggested_rhythm_phase_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "operating_mode": self.operating_mode,
            "first_action_label": self.first_action_label,
            "first_action_command": self.first_action_command,
            "urgent_count": self.urgent_count,
            "optional_count": self.optional_count,
            "automated_follow_up_count": self.automated_follow_up_count,
            "rationale_lines": list(self.rationale_lines),
            "suggested_rhythm_phase_id": self.suggested_rhythm_phase_id,
        }
