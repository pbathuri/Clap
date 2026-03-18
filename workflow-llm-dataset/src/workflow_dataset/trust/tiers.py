"""
M35A–M35D: Authority tier model — explicit tiers for agent actions with allowed/forbidden,
approval requirements, reversibility, audit, valid scopes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AuthorityTierId(str, Enum):
    """Authority tier identifiers."""
    OBSERVE_ONLY = "observe_only"
    SUGGEST_ONLY = "suggest_only"
    DRAFT_ONLY = "draft_only"
    SANDBOX_WRITE = "sandbox_write"
    QUEUED_EXECUTE = "queued_execute"
    BOUNDED_TRUSTED_REAL = "bounded_trusted_real"
    COMMIT_OR_SEND_CANDIDATE = "commit_or_send_candidate"


@dataclass
class AuthorityTier:
    """One authority tier: allowed/forbidden action classes, approval, reversibility, audit, valid scopes."""
    tier_id: str = ""
    name: str = ""
    description: str = ""
    allowed_action_classes: list[str] = field(default_factory=list)
    forbidden_action_classes: list[str] = field(default_factory=list)
    approval_required: bool = True
    approval_scope_note: str = ""
    reversibility_expected: str = ""   # none | optional | required
    audit_required: bool = False
    audit_scope_note: str = ""
    valid_scopes: list[str] = field(default_factory=list)   # global, project, pack, workflow, recurring_routine, worker_lane
    order: int = 0   # lower = lower authority

    def to_dict(self) -> dict[str, Any]:
        return {
            "tier_id": self.tier_id,
            "name": self.name,
            "description": self.description,
            "allowed_action_classes": list(self.allowed_action_classes),
            "forbidden_action_classes": list(self.forbidden_action_classes),
            "approval_required": self.approval_required,
            "approval_scope_note": self.approval_scope_note,
            "reversibility_expected": self.reversibility_expected,
            "audit_required": self.audit_required,
            "audit_scope_note": self.audit_scope_note,
            "valid_scopes": list(self.valid_scopes),
            "order": self.order,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AuthorityTier":
        return cls(
            tier_id=d.get("tier_id", ""),
            name=d.get("name", ""),
            description=d.get("description", ""),
            allowed_action_classes=list(d.get("allowed_action_classes") or []),
            forbidden_action_classes=list(d.get("forbidden_action_classes") or []),
            approval_required=bool(d.get("approval_required", True)),
            approval_scope_note=d.get("approval_scope_note", ""),
            reversibility_expected=d.get("reversibility_expected", ""),
            audit_required=bool(d.get("audit_required", False)),
            audit_scope_note=d.get("audit_scope_note", ""),
            valid_scopes=list(d.get("valid_scopes") or []),
            order=int(d.get("order", 0)),
        )


# Action class names used across planner/human_policy/executor
ACTION_OBSERVE = "observe"
ACTION_SUGGEST = "suggest"
ACTION_DRAFT = "draft"
ACTION_EXECUTE_SIMULATE = "execute_simulate"
ACTION_SANDBOX_WRITE = "sandbox_write"
ACTION_QUEUED_EXECUTE = "queued_execute"
ACTION_EXECUTE_TRUSTED_REAL = "execute_trusted_real"
ACTION_COMMIT_OR_SEND = "commit_or_send"


BUILTIN_TIERS: list[AuthorityTier] = [
    AuthorityTier(
        tier_id=AuthorityTierId.OBSERVE_ONLY.value,
        name="Observe only",
        description="Read-only observation; no writes or execution.",
        allowed_action_classes=[ACTION_OBSERVE],
        forbidden_action_classes=[ACTION_EXECUTE_SIMULATE, ACTION_EXECUTE_TRUSTED_REAL, ACTION_COMMIT_OR_SEND, ACTION_QUEUED_EXECUTE],
        approval_required=False,
        reversibility_expected="none",
        audit_required=False,
        valid_scopes=["global", "project", "pack", "workflow", "recurring_routine"],
        order=0,
    ),
    AuthorityTier(
        tier_id=AuthorityTierId.SUGGEST_ONLY.value,
        name="Suggest only",
        description="Suggestions and recommendations; no execution.",
        allowed_action_classes=[ACTION_OBSERVE, ACTION_SUGGEST],
        forbidden_action_classes=[ACTION_EXECUTE_TRUSTED_REAL, ACTION_COMMIT_OR_SEND, ACTION_QUEUED_EXECUTE],
        approval_required=False,
        reversibility_expected="none",
        audit_required=False,
        valid_scopes=["global", "project", "pack", "workflow", "recurring_routine"],
        order=1,
    ),
    AuthorityTier(
        tier_id=AuthorityTierId.DRAFT_ONLY.value,
        name="Draft only",
        description="Create drafts; no real execution or commit.",
        allowed_action_classes=[ACTION_OBSERVE, ACTION_SUGGEST, ACTION_DRAFT],
        forbidden_action_classes=[ACTION_EXECUTE_TRUSTED_REAL, ACTION_COMMIT_OR_SEND],
        approval_required=False,
        reversibility_expected="optional",
        audit_required=False,
        valid_scopes=["global", "project", "pack", "workflow", "recurring_routine"],
        order=2,
    ),
    AuthorityTier(
        tier_id=AuthorityTierId.SANDBOX_WRITE.value,
        name="Sandbox write",
        description="Writes in sandbox only; simulate execution allowed.",
        allowed_action_classes=[ACTION_OBSERVE, ACTION_SUGGEST, ACTION_DRAFT, ACTION_SANDBOX_WRITE, ACTION_EXECUTE_SIMULATE],
        forbidden_action_classes=[ACTION_EXECUTE_TRUSTED_REAL, ACTION_COMMIT_OR_SEND],
        approval_required=False,
        reversibility_expected="optional",
        audit_required=False,
        valid_scopes=["global", "project", "pack", "workflow", "recurring_routine"],
        order=3,
    ),
    AuthorityTier(
        tier_id=AuthorityTierId.QUEUED_EXECUTE.value,
        name="Queued execute",
        description="Execution only after approval queue; no direct real run.",
        allowed_action_classes=[ACTION_OBSERVE, ACTION_SUGGEST, ACTION_DRAFT, ACTION_SANDBOX_WRITE, ACTION_EXECUTE_SIMULATE, ACTION_QUEUED_EXECUTE],
        forbidden_action_classes=[ACTION_EXECUTE_TRUSTED_REAL, ACTION_COMMIT_OR_SEND],
        approval_required=True,
        approval_scope_note="Execution goes through approval queue.",
        reversibility_expected="optional",
        audit_required=True,
        audit_scope_note="Queue decisions logged.",
        valid_scopes=["global", "project", "pack", "workflow", "recurring_routine", "worker_lane"],
        order=4,
    ),
    AuthorityTier(
        tier_id=AuthorityTierId.BOUNDED_TRUSTED_REAL.value,
        name="Bounded trusted real",
        description="Real execution within approved scope and checkpoints.",
        allowed_action_classes=[ACTION_OBSERVE, ACTION_SUGGEST, ACTION_DRAFT, ACTION_SANDBOX_WRITE, ACTION_EXECUTE_SIMULATE, ACTION_QUEUED_EXECUTE, ACTION_EXECUTE_TRUSTED_REAL],
        forbidden_action_classes=[ACTION_COMMIT_OR_SEND],
        approval_required=True,
        approval_scope_note="Approval registry and checkpoints required.",
        reversibility_expected="required",
        audit_required=True,
        audit_scope_note="All real steps logged.",
        valid_scopes=["project", "pack", "workflow", "recurring_routine", "worker_lane"],
        order=5,
    ),
    AuthorityTier(
        tier_id=AuthorityTierId.COMMIT_OR_SEND_CANDIDATE.value,
        name="Commit or send candidate",
        description="Highest tier: commit or send actions allowed with explicit approval.",
        allowed_action_classes=[ACTION_OBSERVE, ACTION_SUGGEST, ACTION_DRAFT, ACTION_SANDBOX_WRITE, ACTION_EXECUTE_SIMULATE, ACTION_QUEUED_EXECUTE, ACTION_EXECUTE_TRUSTED_REAL, ACTION_COMMIT_OR_SEND],
        forbidden_action_classes=[],
        approval_required=True,
        approval_scope_note="Explicit approval required for commit/send.",
        reversibility_expected="required",
        audit_required=True,
        audit_scope_note="All commit/send actions logged.",
        valid_scopes=["project", "pack", "workflow", "recurring_routine", "worker_lane"],
        order=6,
    ),
]


def get_tier(tier_id: str) -> AuthorityTier | None:
    """Return built-in authority tier by id."""
    for t in BUILTIN_TIERS:
        if t.tier_id == tier_id:
            return t
    return None


def list_tiers() -> list[AuthorityTier]:
    """Return all built-in tiers in order."""
    return list(BUILTIN_TIERS)


def tier_allows_action(tier: AuthorityTier, action_class: str) -> bool:
    """True if tier allows this action class (in allowed and not in forbidden)."""
    if action_class in tier.forbidden_action_classes:
        return False
    if not tier.allowed_action_classes:
        return True
    return action_class in tier.allowed_action_classes
