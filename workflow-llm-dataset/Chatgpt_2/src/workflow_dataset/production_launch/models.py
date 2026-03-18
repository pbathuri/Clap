"""
M40I–M40L: Production launch discipline — runbook, gates, blockers, launch decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LaunchDecision(str, Enum):
    """Recommended launch decision from evidence-based evaluation."""
    LAUNCH = "launch"
    LAUNCH_NARROWLY = "launch_narrowly"
    PAUSE = "pause"
    REPAIR_AND_REVIEW = "repair_and_review"


@dataclass
class OperatingChecklistItem:
    """Single item in an operating checklist (pre-launch or daily)."""
    id: str
    label: str
    command_or_ref: str = ""
    required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "command_or_ref": self.command_or_ref,
            "required": self.required,
        }


@dataclass
class DailyOperatingReviewStep:
    """Step in a daily operating review routine."""
    id: str
    label: str
    command_or_ref: str = ""
    frequency: str = "daily"  # daily | weekly | per_session

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "command_or_ref": self.command_or_ref,
            "frequency": self.frequency,
        }


@dataclass
class RecoveryEscalationPath:
    """Recovery or escalation path reference."""
    path_id: str
    label: str
    first_step_command: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_id": self.path_id,
            "label": self.label,
            "first_step_command": self.first_step_command,
            "description": self.description,
        }


@dataclass
class SupportPath:
    """Support path reference (triage, handoff, recovery guide)."""
    path_id: str
    label: str
    command_or_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"path_id": self.path_id, "label": self.label, "command_or_ref": self.command_or_ref}


@dataclass
class TrustedRoutineReviewStep:
    """Trusted routine review step (pre-launch or ongoing)."""
    step_id: str
    label: str
    command_or_ref: str = ""
    when: str = "pre_launch"  # pre_launch | daily | on_incident

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "label": self.label,
            "command_or_ref": self.command_or_ref,
            "when": self.when,
        }


@dataclass
class ProductionRunbook:
    """Production runbook for a chosen vertical: operating checklist, daily review, recovery/support paths, trusted routine steps."""
    vertical_id: str
    label: str
    operating_checklist: list[OperatingChecklistItem] = field(default_factory=list)
    daily_operating_review: list[DailyOperatingReviewStep] = field(default_factory=list)
    recovery_paths: list[RecoveryEscalationPath] = field(default_factory=list)
    support_paths: list[SupportPath] = field(default_factory=list)
    trusted_routine_review_steps: list[TrustedRoutineReviewStep] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "vertical_id": self.vertical_id,
            "label": self.label,
            "description": self.description,
            "operating_checklist": [c.to_dict() for c in self.operating_checklist],
            "daily_operating_review": [d.to_dict() for d in self.daily_operating_review],
            "recovery_paths": [r.to_dict() for r in self.recovery_paths],
            "support_paths": [s.to_dict() for s in self.support_paths],
            "trusted_routine_review_steps": [t.to_dict() for t in self.trusted_routine_review_steps],
        }


@dataclass
class LaunchGateResult:
    """Result of evaluating a single production launch gate."""
    gate_id: str
    label: str
    passed: bool
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"gate_id": self.gate_id, "label": self.label, "passed": self.passed, "detail": self.detail}


@dataclass
class LaunchBlocker:
    """Launch blocker: must resolve before launch (or narrow launch)."""
    id: str
    summary: str
    source: str = ""
    remediation_hint: str = ""
    severity: str = "blocker"  # blocker | critical

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "summary": self.summary,
            "source": self.source,
            "remediation_hint": self.remediation_hint,
            "severity": self.severity,
        }


@dataclass
class LaunchWarning:
    """Launch warning: does not block but operator should be aware; may reduce to launch_narrowly."""
    id: str
    summary: str
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "summary": self.summary, "source": self.source}


# ----- M40L.1 Production review cycles + sustained-use checkpoints + post-deployment guidance -----


class PostDeploymentGuidance(str, Enum):
    """Recommended ongoing action after deployment: continue, narrow scope, rollback, or repair."""
    CONTINUE = "continue"
    NARROW = "narrow"
    ROLLBACK = "rollback"
    REPAIR = "repair"


@dataclass
class ProductionReviewCycle:
    """A single production review cycle: snapshot at a point in time with findings and guidance."""
    cycle_id: str
    at_iso: str
    summary: str = ""
    findings: list[str] = field(default_factory=list)
    guidance_snapshot: str = ""  # PostDeploymentGuidance value
    recommended_actions: list[str] = field(default_factory=list)
    next_due_iso: str = ""
    vertical_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "at_iso": self.at_iso,
            "summary": self.summary,
            "findings": list(self.findings),
            "guidance_snapshot": self.guidance_snapshot,
            "recommended_actions": list(self.recommended_actions),
            "next_due_iso": self.next_due_iso,
            "vertical_id": self.vertical_id,
        }


@dataclass
class SustainedUseCheckpoint:
    """Sustained-use checkpoint: assessment at a usage milestone (e.g. after N sessions or days)."""
    checkpoint_id: str
    kind: str  # day_7 | session_5 | session_10 | auto
    at_iso: str
    criteria_met: bool
    report_summary: str = ""
    sessions_or_days_context: dict[str, Any] = field(default_factory=dict)
    guidance: str = ""  # continue | narrow | rollback | repair
    recommended_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "kind": self.kind,
            "at_iso": self.at_iso,
            "criteria_met": self.criteria_met,
            "report_summary": self.report_summary,
            "sessions_or_days_context": dict(self.sessions_or_days_context),
            "guidance": self.guidance,
            "recommended_actions": list(self.recommended_actions),
        }
