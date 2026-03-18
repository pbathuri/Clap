"""
M29I–M29L: Activity timeline and intervention inbox models.
Unified event and review-worthy item types for operator review studio.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Timeline event kinds (meaningful system activity)
EVENT_PROJECT_CREATED = "project_created"
EVENT_PROJECT_CHANGED = "project_changed"
EVENT_PLAN_COMPILED = "plan_compiled"
EVENT_PLAN_REPLANNED = "plan_replanned"
EVENT_ACTION_QUEUED = "action_queued"
EVENT_ACTION_APPROVED = "action_approved"
EVENT_ACTION_REJECTED = "action_rejected"
EVENT_ACTION_DEFERRED = "action_deferred"
EVENT_EXECUTOR_STARTED = "executor_started"
EVENT_EXECUTOR_BLOCKED = "executor_blocked"
EVENT_EXECUTOR_COMPLETED = "executor_completed"
EVENT_LANE_CREATED = "lane_created"
EVENT_LANE_RETURNED = "lane_returned"
EVENT_LANE_FAILED = "lane_failed"
EVENT_SKILL_DRAFTED = "skill_drafted"
EVENT_SKILL_ACCEPTED = "skill_accepted"
EVENT_SKILL_REJECTED = "skill_rejected"
EVENT_PACK_INSTALLED = "pack_installed"
EVENT_PACK_UPDATED = "pack_updated"
EVENT_PACK_BLOCKED = "pack_blocked"
EVENT_POLICY_OVERRIDE_APPLIED = "policy_override_applied"
EVENT_POLICY_OVERRIDE_REVOKED = "policy_override_revoked"
EVENT_ARTIFACT_PRODUCED = "artifact_produced"
EVENT_ARTIFACT_REVIEWED = "artifact_reviewed"

EVENT_KINDS = (
    EVENT_PROJECT_CREATED,
    EVENT_PROJECT_CHANGED,
    EVENT_PLAN_COMPILED,
    EVENT_PLAN_REPLANNED,
    EVENT_ACTION_QUEUED,
    EVENT_ACTION_APPROVED,
    EVENT_ACTION_REJECTED,
    EVENT_ACTION_DEFERRED,
    EVENT_EXECUTOR_STARTED,
    EVENT_EXECUTOR_BLOCKED,
    EVENT_EXECUTOR_COMPLETED,
    EVENT_LANE_CREATED,
    EVENT_LANE_RETURNED,
    EVENT_LANE_FAILED,
    EVENT_SKILL_DRAFTED,
    EVENT_SKILL_ACCEPTED,
    EVENT_SKILL_REJECTED,
    EVENT_PACK_INSTALLED,
    EVENT_PACK_UPDATED,
    EVENT_PACK_BLOCKED,
    EVENT_POLICY_OVERRIDE_APPLIED,
    EVENT_POLICY_OVERRIDE_REVOKED,
    EVENT_ARTIFACT_PRODUCED,
    EVENT_ARTIFACT_REVIEWED,
)

# Intervention item kinds (review-worthy)
ITEM_APPROVAL_QUEUE = "approval_queue"
ITEM_BLOCKED_RUN = "blocked_run"
ITEM_LANE_RESULT = "lane_result"
ITEM_REPLAN_RECOMMENDATION = "replan_recommendation"
ITEM_SKILL_CANDIDATE = "skill_candidate"
ITEM_POLICY_EXCEPTION = "policy_exception"
ITEM_STALLED_INTERVENTION = "stalled_intervention"
ITEM_ARTIFACT_REVIEW = "artifact_review"
# M31H.1 Graph review inbox
ITEM_GRAPH_ROUTINE_CONFIRMATION = "graph_routine_confirmation"
ITEM_GRAPH_PATTERN_REVIEW = "graph_pattern_review"

INTERVENTION_ITEM_KINDS = (
    ITEM_APPROVAL_QUEUE,
    ITEM_BLOCKED_RUN,
    ITEM_LANE_RESULT,
    ITEM_REPLAN_RECOMMENDATION,
    ITEM_SKILL_CANDIDATE,
    ITEM_POLICY_EXCEPTION,
    ITEM_STALLED_INTERVENTION,
    ITEM_ARTIFACT_REVIEW,
    ITEM_GRAPH_ROUTINE_CONFIRMATION,
    ITEM_GRAPH_PATTERN_REVIEW,
)


@dataclass
class TimelineEvent:
    """One meaningful system activity event for unified timeline."""
    event_id: str = ""
    kind: str = ""
    timestamp_utc: str = ""
    summary: str = ""
    entity_refs: dict[str, str] = field(default_factory=dict)  # project_id, run_id, session_id, plan_ref, etc.
    project_id: str = ""
    pack_id: str = ""
    lane_id: str = ""
    run_id: str = ""
    session_id: str = ""
    plan_ref: str = ""
    artifact_ref: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "kind": self.kind,
            "timestamp_utc": self.timestamp_utc,
            "summary": self.summary,
            "entity_refs": dict(self.entity_refs),
            "project_id": self.project_id,
            "pack_id": self.pack_id,
            "lane_id": self.lane_id,
            "run_id": self.run_id,
            "session_id": self.session_id,
            "plan_ref": self.plan_ref,
            "artifact_ref": self.artifact_ref,
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TimelineEvent":
        return cls(
            event_id=d.get("event_id", ""),
            kind=d.get("kind", ""),
            timestamp_utc=d.get("timestamp_utc", ""),
            summary=d.get("summary", ""),
            entity_refs=dict(d.get("entity_refs", {})),
            project_id=d.get("project_id", ""),
            pack_id=d.get("pack_id", ""),
            lane_id=d.get("lane_id", ""),
            run_id=d.get("run_id", ""),
            session_id=d.get("session_id", ""),
            plan_ref=d.get("plan_ref", ""),
            artifact_ref=d.get("artifact_ref", ""),
            details=dict(d.get("details", {})),
        )


@dataclass
class InterventionItem:
    """One review-worthy item in the unified intervention inbox."""
    item_id: str = ""
    kind: str = ""
    status: str = "pending"  # pending | accepted | rejected | deferred
    summary: str = ""
    created_at: str = ""
    priority: str = "medium"  # low | medium | high | urgent
    entity_refs: dict[str, str] = field(default_factory=dict)
    source_ref: str = ""  # queue_id, run_id, skill_id, project_id, override_id, etc.
    operator_notes: str = ""
    decided_at: str = ""
    decision_note: str = ""
    revisit_after: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "kind": self.kind,
            "status": self.status,
            "summary": self.summary,
            "created_at": self.created_at,
            "priority": self.priority,
            "entity_refs": dict(self.entity_refs),
            "source_ref": self.source_ref,
            "operator_notes": self.operator_notes,
            "decided_at": self.decided_at,
            "decision_note": self.decision_note,
            "revisit_after": self.revisit_after,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "InterventionItem":
        return cls(
            item_id=d.get("item_id", ""),
            kind=d.get("kind", ""),
            status=d.get("status", "pending"),
            summary=d.get("summary", ""),
            created_at=d.get("created_at", ""),
            priority=d.get("priority", "medium"),
            entity_refs=dict(d.get("entity_refs", {})),
            source_ref=d.get("source_ref", ""),
            operator_notes=d.get("operator_notes", ""),
            decided_at=d.get("decided_at", ""),
            decision_note=d.get("decision_note", ""),
            revisit_after=d.get("revisit_after", ""),
        )
