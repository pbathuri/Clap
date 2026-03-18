"""
M30I–M30L: Release readiness and supportability models — explicit status, blockers, warnings, scope, limitations, handoff.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Release readiness status
READINESS_READY = "ready"
READINESS_BLOCKED = "blocked"
READINESS_DEGRADED = "degraded"

# Support guidance
GUIDANCE_SAFE_TO_CONTINUE = "safe_to_continue"
GUIDANCE_NEEDS_OPERATOR = "needs_operator"
GUIDANCE_NEEDS_ROLLBACK = "needs_rollback"


@dataclass
class ReleaseBlocker:
    """A single release blocker (must resolve before first-user release)."""
    id: str
    summary: str
    source: str = ""  # e.g. rollout, package_readiness, environment
    remediation_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "summary": self.summary,
            "source": self.source,
            "remediation_hint": self.remediation_hint,
        }


@dataclass
class ReleaseWarning:
    """A release warning (does not block but operator should be aware)."""
    id: str
    summary: str
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "summary": self.summary, "source": self.source}


@dataclass
class SupportedWorkflowScope:
    """Declared supported workflow scope for first-user release."""
    workflow_ids: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"workflow_ids": list(self.workflow_ids), "description": self.description}


@dataclass
class KnownLimitation:
    """A known limitation to document for first users."""
    id: str
    summary: str
    category: str = ""  # e.g. performance, scope, manual_step

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "summary": self.summary, "category": self.category}


@dataclass
class OperatorHandoffStatus:
    """Status of operator handoff pack (freshness, path)."""
    generated_at: str = ""
    output_path: str = ""
    artifact_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "output_path": self.output_path,
            "artifact_count": self.artifact_count,
        }


@dataclass
class SupportabilityStatus:
    """Supportability confidence and guidance."""
    confidence: str = ""  # high | medium | low
    guidance: str = ""  # safe_to_continue | needs_operator | needs_rollback
    recommended_next_support_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "confidence": self.confidence,
            "guidance": self.guidance,
            "recommended_next_support_action": self.recommended_next_support_action,
        }


@dataclass
class ReleaseReadinessStatus:
    """Aggregate release readiness: status, blockers, warnings, scope, limitations, handoff, supportability."""
    status: str  # ready | blocked | degraded
    blockers: list[ReleaseBlocker] = field(default_factory=list)
    warnings: list[ReleaseWarning] = field(default_factory=list)
    supported_scope: SupportedWorkflowScope = field(default_factory=SupportedWorkflowScope)
    known_limitations: list[KnownLimitation] = field(default_factory=list)
    handoff_status: OperatorHandoffStatus = field(default_factory=OperatorHandoffStatus)
    supportability: SupportabilityStatus = field(default_factory=SupportabilityStatus)
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "blockers": [b.to_dict() for b in self.blockers],
            "warnings": [w.to_dict() for w in self.warnings],
            "supported_scope": self.supported_scope.to_dict(),
            "known_limitations": [k.to_dict() for k in self.known_limitations],
            "handoff_status": self.handoff_status.to_dict(),
            "supportability": self.supportability.to_dict(),
            "reasons": list(self.reasons),
        }


# M30L.1 Launch profiles and rollout gates
@dataclass
class RolloutGate:
    """A single rollout gate: condition that must pass for a launch profile to be allowed."""
    gate_id: str
    label: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"gate_id": self.gate_id, "label": self.label, "description": self.description}


@dataclass
class LaunchProfile:
    """Launch profile: demo, internal pilot, careful first user, broader controlled pilot."""
    profile_id: str
    label: str = ""
    description: str = ""
    required_gate_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "label": self.label,
            "description": self.description,
            "required_gate_ids": list(self.required_gate_ids),
        }
