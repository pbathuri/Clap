"""
M26I–M26L: Explicit skill model for teaching studio.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SKILL_STATUSES = ("draft", "accepted", "rejected")
TRUST_READINESS_LEVELS = ("unset", "simulate_only", "trusted_real_candidate", "blocked", "unclear")
SKILL_SOURCE_TYPES = ("task_demo", "correction", "session_pattern", "manual")


@dataclass
class Skill:
    """Reusable skill definition from demo/correction/session/manual. Reviewable; no auto-promotion."""
    skill_id: str
    source_type: str  # task_demo | correction | session_pattern | manual
    source_reference_id: str = ""  # task_id, correction_id, session_id, or ""
    goal_family: str = ""
    task_family: str = ""
    required_capabilities: list[str] = field(default_factory=list)
    required_approvals: list[str] = field(default_factory=list)
    pack_associations: list[str] = field(default_factory=list)
    job_associations: list[str] = field(default_factory=list)
    expected_inputs: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    trust_readiness_status: str = "unset"  # unset | simulate_only | trusted_real_candidate | blocked | unclear
    operator_notes: str = ""
    certification_notes: str = ""
    status: str = "draft"  # draft | accepted | rejected
    simulate_only_or_trusted_real: str = "simulate_only"  # simulate_only | trusted_real_candidate
    normalized_steps: list[dict[str, Any]] = field(default_factory=list)  # normalized step sequence for review
    created_at: str = ""
    updated_at: str = ""
    accepted_at: str = ""
    rejected_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "source_type": self.source_type,
            "source_reference_id": self.source_reference_id,
            "goal_family": self.goal_family,
            "task_family": self.task_family,
            "required_capabilities": list(self.required_capabilities),
            "required_approvals": list(self.required_approvals),
            "pack_associations": list(self.pack_associations),
            "job_associations": list(self.job_associations),
            "expected_inputs": list(self.expected_inputs),
            "expected_outputs": list(self.expected_outputs),
            "trust_readiness_status": self.trust_readiness_status,
            "operator_notes": self.operator_notes,
            "certification_notes": self.certification_notes,
            "status": self.status,
            "simulate_only_or_trusted_real": self.simulate_only_or_trusted_real,
            "normalized_steps": list(self.normalized_steps),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "accepted_at": self.accepted_at,
            "rejected_at": self.rejected_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Skill:
        return cls(
            skill_id=str(d.get("skill_id", "")),
            source_type=str(d.get("source_type", "manual")),
            source_reference_id=str(d.get("source_reference_id", "")),
            goal_family=str(d.get("goal_family", "")),
            task_family=str(d.get("task_family", "")),
            required_capabilities=list(d.get("required_capabilities") or []),
            required_approvals=list(d.get("required_approvals") or []),
            pack_associations=list(d.get("pack_associations") or []),
            job_associations=list(d.get("job_associations") or []),
            expected_inputs=list(d.get("expected_inputs") or []),
            expected_outputs=list(d.get("expected_outputs") or []),
            trust_readiness_status=str(d.get("trust_readiness_status", "unset")),
            operator_notes=str(d.get("operator_notes", "")),
            certification_notes=str(d.get("certification_notes", "")),
            status=str(d.get("status", "draft")),
            simulate_only_or_trusted_real=str(d.get("simulate_only_or_trusted_real", "simulate_only")),
            normalized_steps=list(d.get("normalized_steps") or []),
            created_at=str(d.get("created_at", "")),
            updated_at=str(d.get("updated_at", "")),
            accepted_at=str(d.get("accepted_at", "")),
            rejected_at=str(d.get("rejected_at", "")),
        )
