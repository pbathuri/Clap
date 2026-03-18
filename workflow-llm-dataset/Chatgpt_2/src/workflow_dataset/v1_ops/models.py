"""
M50E–M50H Phase A: v1 Operating model.
v1 support posture, maintenance rhythm, review cadence, incident class,
recovery path, escalation path, rollback readiness, support ownership note, stable-v1 maintenance pack.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IncidentClass(str, Enum):
    """Class of incident for v1 support."""
    DEGRADATION = "degradation"   # partial or degraded operation
    OUTAGE = "outage"             # unable to operate
    DRIFT = "drift"               # state/config drift, repair needed
    BLOCKED_APPROVAL = "blocked_approval"
    FAILED_UPGRADE = "failed_upgrade"
    MISSING_RUNTIME = "missing_runtime"
    OTHER = "other"


@dataclass
class V1SupportPosture:
    """How stable v1 is operated and supported: paths, level, ownership hint."""
    posture_id: str = ""
    support_level: str = ""   # e.g. sustained | maintenance | full
    support_paths: list[str] = field(default_factory=list)
    maintenance_rhythm_id: str = ""
    review_cadence_id: str = ""
    recovery_posture_summary: str = ""
    rollback_ready: bool = False
    as_of_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "posture_id": self.posture_id,
            "support_level": self.support_level,
            "support_paths": list(self.support_paths),
            "maintenance_rhythm_id": self.maintenance_rhythm_id,
            "review_cadence_id": self.review_cadence_id,
            "recovery_posture_summary": self.recovery_posture_summary,
            "rollback_ready": self.rollback_ready,
            "as_of_utc": self.as_of_utc,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "V1SupportPosture":
        return cls(
            posture_id=d.get("posture_id", ""),
            support_level=d.get("support_level", ""),
            support_paths=list(d.get("support_paths") or []),
            maintenance_rhythm_id=d.get("maintenance_rhythm_id", ""),
            review_cadence_id=d.get("review_cadence_id", ""),
            recovery_posture_summary=d.get("recovery_posture_summary", ""),
            rollback_ready=bool(d.get("rollback_ready", False)),
            as_of_utc=d.get("as_of_utc", ""),
        )


@dataclass
class MaintenanceRhythm:
    """Maintenance rhythm: daily/weekly tasks, label, interval."""
    rhythm_id: str = ""
    label: str = ""
    description: str = ""
    interval_days: int = 1
    daily_tasks: list[str] = field(default_factory=list)
    weekly_tasks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rhythm_id": self.rhythm_id,
            "label": self.label,
            "description": self.description,
            "interval_days": self.interval_days,
            "daily_tasks": list(self.daily_tasks),
            "weekly_tasks": list(self.weekly_tasks),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MaintenanceRhythm":
        return cls(
            rhythm_id=d.get("rhythm_id", ""),
            label=d.get("label", ""),
            description=d.get("description", ""),
            interval_days=int(d.get("interval_days", 1)),
            daily_tasks=list(d.get("daily_tasks") or []),
            weekly_tasks=list(d.get("weekly_tasks") or []),
        )


@dataclass
class ReviewCadenceRef:
    """Reference to a review cadence (e.g. from stability_reviews)."""
    cadence_id: str = ""
    label: str = ""
    kind: str = ""   # daily | weekly | rolling_stability
    next_due_iso: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "cadence_id": self.cadence_id,
            "label": self.label,
            "kind": self.kind,
            "next_due_iso": self.next_due_iso,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ReviewCadenceRef":
        return cls(
            cadence_id=d.get("cadence_id", ""),
            label=d.get("label", ""),
            kind=d.get("kind", ""),
            next_due_iso=d.get("next_due_iso", ""),
            description=d.get("description", ""),
        )


@dataclass
class RecoveryPath:
    """Recovery path: steps to restore v1 health from an incident class."""
    path_id: str = ""
    incident_class: str = ""
    label: str = ""
    steps: list[str] = field(default_factory=list)
    first_step_command: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_id": self.path_id,
            "incident_class": self.incident_class,
            "label": self.label,
            "steps": list(self.steps),
            "first_step_command": self.first_step_command,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RecoveryPath":
        return cls(
            path_id=d.get("path_id", ""),
            incident_class=d.get("incident_class", ""),
            label=d.get("label", ""),
            steps=list(d.get("steps") or []),
            first_step_command=d.get("first_step_command", ""),
        )


@dataclass
class EscalationPath:
    """Escalation path: when to escalate and to whom."""
    path_id: str = ""
    trigger_condition: str = ""
    escalate_to: str = ""
    handoff_artifact: str = ""   # e.g. support_bundle, issue_report

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_id": self.path_id,
            "trigger_condition": self.trigger_condition,
            "escalate_to": self.escalate_to,
            "handoff_artifact": self.handoff_artifact,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EscalationPath":
        return cls(
            path_id=d.get("path_id", ""),
            trigger_condition=d.get("trigger_condition", ""),
            escalate_to=d.get("escalate_to", ""),
            handoff_artifact=d.get("handoff_artifact", ""),
        )


@dataclass
class RollbackReadiness:
    """Rollback readiness posture for v1."""
    ready: bool = False
    prior_stable_ref: str = ""
    reason: str = ""
    recommended_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "prior_stable_ref": self.prior_stable_ref,
            "reason": self.reason,
            "recommended_action": self.recommended_action,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RollbackReadiness":
        return cls(
            ready=bool(d.get("ready", False)),
            prior_stable_ref=d.get("prior_stable_ref", ""),
            reason=d.get("reason", ""),
            recommended_action=d.get("recommended_action", ""),
        )


@dataclass
class SupportOwnershipNote:
    """Who owns v1 support / who does what."""
    role_or_owner: str = ""
    responsibility: str = ""
    scope_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "role_or_owner": self.role_or_owner,
            "responsibility": self.responsibility,
            "scope_note": self.scope_note,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SupportOwnershipNote":
        return cls(
            role_or_owner=d.get("role_or_owner", ""),
            responsibility=d.get("responsibility", ""),
            scope_note=d.get("scope_note", ""),
        )


@dataclass
class StableV1MaintenancePack:
    """Single pack: support posture, rhythm, review cadence, recovery path, escalation, rollback readiness, ownership."""
    pack_id: str = ""
    label: str = ""
    support_posture: V1SupportPosture | None = None
    maintenance_rhythm: MaintenanceRhythm | None = None
    review_cadence_ref: ReviewCadenceRef | None = None
    recovery_paths: list[RecoveryPath] = field(default_factory=list)
    escalation_paths: list[EscalationPath] = field(default_factory=list)
    rollback_readiness: RollbackReadiness | None = None
    ownership_notes: list[SupportOwnershipNote] = field(default_factory=list)
    generated_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "label": self.label,
            "support_posture": self.support_posture.to_dict() if self.support_posture else None,
            "maintenance_rhythm": self.maintenance_rhythm.to_dict() if self.maintenance_rhythm else None,
            "review_cadence_ref": self.review_cadence_ref.to_dict() if self.review_cadence_ref else None,
            "recovery_paths": [r.to_dict() for r in self.recovery_paths],
            "escalation_paths": [e.to_dict() for e in self.escalation_paths],
            "rollback_readiness": self.rollback_readiness.to_dict() if self.rollback_readiness else None,
            "ownership_notes": [o.to_dict() for o in self.ownership_notes],
            "generated_at_utc": self.generated_at_utc,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "StableV1MaintenancePack":
        sp = d.get("support_posture")
        mr = d.get("maintenance_rhythm")
        rc = d.get("review_cadence_ref")
        rr = d.get("rollback_readiness")
        return cls(
            pack_id=d.get("pack_id", ""),
            label=d.get("label", ""),
            support_posture=V1SupportPosture.from_dict(sp) if sp else None,
            maintenance_rhythm=MaintenanceRhythm.from_dict(mr) if mr else None,
            review_cadence_ref=ReviewCadenceRef.from_dict(rc) if rc else None,
            recovery_paths=[RecoveryPath.from_dict(x) for x in (d.get("recovery_paths") or [])],
            escalation_paths=[EscalationPath.from_dict(x) for x in (d.get("escalation_paths") or [])],
            rollback_readiness=RollbackReadiness.from_dict(rr) if rr else None,
            ownership_notes=[SupportOwnershipNote.from_dict(x) for x in (d.get("ownership_notes") or [])],
            generated_at_utc=d.get("generated_at_utc", ""),
        )


# ----- M50H.1 Support review summary + maintenance obligations -----


@dataclass
class MaintenanceObligation:
    """Single obligation: what must be done to preserve stable-v1 posture."""
    category: str = ""   # daily | weekly | review_cadence | rollback | support_path
    label: str = ""
    frequency: str = ""   # daily | weekly | on_cadence | on_demand
    command_or_description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "label": self.label,
            "frequency": self.frequency,
            "command_or_description": self.command_or_description,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MaintenanceObligation":
        return cls(
            category=d.get("category", ""),
            label=d.get("label", ""),
            frequency=d.get("frequency", ""),
            command_or_description=d.get("command_or_description", ""),
        )


@dataclass
class MaintenanceObligationsSummary:
    """Clear summary of what must be maintained to preserve stable-v1 posture."""
    summary_id: str = ""
    obligations: list[MaintenanceObligation] = field(default_factory=list)
    generated_at_utc: str = ""
    summary_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary_id": self.summary_id,
            "obligations": [o.to_dict() for o in self.obligations],
            "generated_at_utc": self.generated_at_utc,
            "summary_text": self.summary_text,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MaintenanceObligationsSummary":
        return cls(
            summary_id=d.get("summary_id", ""),
            obligations=[MaintenanceObligation.from_dict(x) for x in (d.get("obligations") or [])],
            generated_at_utc=d.get("generated_at_utc", ""),
            summary_text=d.get("summary_text", ""),
        )


@dataclass
class SupportReviewSummary:
    """Operator/owner support review summary: what was reviewed, overdue, next actions, ownership."""
    review_id: str = ""
    period_label: str = ""
    reviewed_at_iso: str = ""
    items_reviewed: list[str] = field(default_factory=list)
    overdue_items: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    ownership_roles: list[str] = field(default_factory=list)
    summary_text: str = ""
    generated_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "period_label": self.period_label,
            "reviewed_at_iso": self.reviewed_at_iso,
            "items_reviewed": list(self.items_reviewed),
            "overdue_items": list(self.overdue_items),
            "next_actions": list(self.next_actions),
            "ownership_roles": list(self.ownership_roles),
            "summary_text": self.summary_text,
            "generated_at_utc": self.generated_at_utc,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SupportReviewSummary":
        return cls(
            review_id=d.get("review_id", ""),
            period_label=d.get("period_label", ""),
            reviewed_at_iso=d.get("reviewed_at_iso", ""),
            items_reviewed=list(d.get("items_reviewed") or []),
            overdue_items=list(d.get("overdue_items") or []),
            next_actions=list(d.get("next_actions") or []),
            ownership_roles=list(d.get("ownership_roles") or []),
            summary_text=d.get("summary_text", ""),
            generated_at_utc=d.get("generated_at_utc", ""),
        )
