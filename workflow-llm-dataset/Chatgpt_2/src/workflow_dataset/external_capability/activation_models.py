"""
M24D: Activation request model — structured request for install/enable/disable/remove/verify.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

REQUESTED_ACTIONS = ("install", "enable", "disable", "remove", "verify")
ACTIVATION_STATUSES = ("pending", "approved", "blocked", "executed", "failed", "rolled_back")


@dataclass
class ActivationRequest:
    """Single activation request for an external capability source."""

    activation_id: str
    source_id: str
    source_category: str = ""
    requested_action: str = "enable"  # install | enable | disable | remove | verify
    prerequisites: list[str] = field(default_factory=list)
    approvals_required: list[str] = field(default_factory=list)
    expected_resource_cost: str = ""  # low | medium | high
    reversible: bool = True
    status: str = "pending"  # pending | approved | blocked | executed | failed | rolled_back
    notes: str = ""
    risks: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "activation_id": self.activation_id,
            "source_id": self.source_id,
            "source_category": self.source_category,
            "requested_action": self.requested_action,
            "prerequisites": self.prerequisites,
            "approvals_required": self.approvals_required,
            "expected_resource_cost": self.expected_resource_cost,
            "reversible": self.reversible,
            "status": self.status,
            "notes": self.notes,
            "risks": self.risks,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ActivationRequest:
        return cls(
            activation_id=str(d.get("activation_id", "")),
            source_id=str(d.get("source_id", "")),
            source_category=str(d.get("source_category", "")),
            requested_action=str(d.get("requested_action", "enable")),
            prerequisites=list(d.get("prerequisites", [])),
            approvals_required=list(d.get("approvals_required", [])),
            expected_resource_cost=str(d.get("expected_resource_cost", "")),
            reversible=bool(d.get("reversible", True)),
            status=str(d.get("status", "pending")),
            notes=str(d.get("notes", "")),
            risks=str(d.get("risks", "")),
            created_at=str(d.get("created_at", "")),
            updated_at=str(d.get("updated_at", "")),
        )
