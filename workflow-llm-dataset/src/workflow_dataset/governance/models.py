"""
M48A: Role and authority model — human role, authority scope, bindings, review/override, escalation, conflict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RoleType(str, Enum):
    """Human role types."""
    OPERATOR = "operator"
    REVIEWER = "reviewer"
    APPROVER = "approver"
    MAINTAINER = "maintainer"
    OBSERVER = "observer"
    SUPPORT_REVIEWER = "support_reviewer"


class ScopeLevelId(str, Enum):
    """Authority scope level."""
    PRODUCT_WIDE = "product_wide"
    VERTICAL = "vertical"
    PROJECT = "project"
    WORKFLOW_ROUTINE = "workflow_routine"
    REVIEW_DOMAIN = "review_domain"
    OPERATOR_MODE_ROUTINE = "operator_mode_routine"


@dataclass
class HumanRole:
    """Human role: id, type, label, allowed/forbidden surfaces and action classes, review/override semantics."""
    role_id: str = ""
    role_type: str = ""  # operator | reviewer | approver | maintainer | observer | support_reviewer
    label: str = ""
    description: str = ""
    allowed_surface_ids: list[str] = field(default_factory=list)  # empty = all not in forbidden
    forbidden_surface_ids: list[str] = field(default_factory=list)
    allowed_action_classes: list[str] = field(default_factory=list)
    forbidden_action_classes: list[str] = field(default_factory=list)
    may_review: bool = False
    may_approve: bool = False
    may_execute: bool = False
    may_request_only: bool = False  # request but not execute
    observe_only: bool = False
    default_authority_tier_id: str = ""  # cap from trust tiers
    order: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "role_id": self.role_id,
            "role_type": self.role_type,
            "label": self.label,
            "description": self.description,
            "allowed_surface_ids": list(self.allowed_surface_ids),
            "forbidden_surface_ids": list(self.forbidden_surface_ids),
            "allowed_action_classes": list(self.allowed_action_classes),
            "forbidden_action_classes": list(self.forbidden_action_classes),
            "may_review": self.may_review,
            "may_approve": self.may_approve,
            "may_execute": self.may_execute,
            "may_request_only": self.may_request_only,
            "observe_only": self.observe_only,
            "default_authority_tier_id": self.default_authority_tier_id,
            "order": self.order,
        }


@dataclass
class AuthorityScope:
    """Authority scope: level, scope_id, label, precedence rank."""
    level_id: str = ""
    scope_id: str = ""  # e.g. vertical_id, project_id, domain_id
    label: str = ""
    precedence_rank: int = 0  # higher = more specific
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "level_id": self.level_id,
            "scope_id": self.scope_id,
            "label": self.label,
            "precedence_rank": self.precedence_rank,
            "description": self.description,
        }


@dataclass
class RoleAuthorityBinding:
    """Binding of role to scope: effective surfaces and action classes, review/override requirements."""
    role_id: str = ""
    scope_level: str = ""
    scope_id: str = ""
    effective_surface_ids: list[str] = field(default_factory=list)
    effective_action_classes: list[str] = field(default_factory=list)
    review_required: bool = False
    override_required: bool = False
    authority_tier_id: str = ""
    trust_preset_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "role_id": self.role_id,
            "scope_level": self.scope_level,
            "scope_id": self.scope_id,
            "effective_surface_ids": list(self.effective_surface_ids),
            "effective_action_classes": list(self.effective_action_classes),
            "review_required": self.review_required,
            "override_required": self.override_required,
            "authority_tier_id": self.authority_tier_id,
            "trust_preset_id": self.trust_preset_id,
        }


@dataclass
class ReviewRequirement:
    """When review is required for an action."""
    action_class: str = ""
    scope_level: str = ""
    domain_id: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_class": self.action_class,
            "scope_level": self.scope_level,
            "domain_id": self.domain_id,
            "description": self.description,
        }


@dataclass
class OverrideRequirement:
    """When override (e.g. second party) is required."""
    action_class: str = ""
    scope_level: str = ""
    override_by_role_id: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_class": self.action_class,
            "scope_level": self.scope_level,
            "override_by_role_id": self.override_by_role_id,
            "description": self.description,
        }


@dataclass
class EscalationPath:
    """Escalation path when authority is blocked."""
    from_role_id: str = ""
    to_role_id: str = ""
    to_domain_id: str = ""
    trigger: str = ""  # blocked | sensitivity_threshold | manual
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_role_id": self.from_role_id,
            "to_role_id": self.to_role_id,
            "to_domain_id": self.to_domain_id,
            "trigger": self.trigger,
            "description": self.description,
        }


@dataclass
class ScopeConflict:
    """Conflict between scopes (e.g. broader vs narrower)."""
    scope_a: str = ""
    scope_b: str = ""
    resolution: str = ""  # more_specific_wins | deny | allow_both
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope_a": self.scope_a,
            "scope_b": self.scope_b,
            "resolution": self.resolution,
            "description": self.description,
        }


@dataclass
class CheckResult:
    """Result of can_role_perform_action check."""
    allowed: bool = False
    reason: str = ""
    required_review: bool = False
    required_approval: bool = False
    escalation_path: EscalationPath | None = None
    binding_scope: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "required_review": self.required_review,
            "required_approval": self.required_approval,
            "escalation_path": self.escalation_path.to_dict() if self.escalation_path else None,
            "binding_scope": self.binding_scope,
        }


@dataclass
class AuthorityExplanation:
    """Human-readable explanation of authority for a role/surface/action."""
    role_id: str = ""
    summary: str = ""
    allowed_surfaces: list[str] = field(default_factory=list)
    blocked_surfaces: list[str] = field(default_factory=list)
    allowed_actions: list[str] = field(default_factory=list)
    blocked_actions: list[str] = field(default_factory=list)
    required_review: str = ""
    override_required: str = ""
    escalation_path: str = ""
    scope_context: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "role_id": self.role_id,
            "summary": self.summary,
            "allowed_surfaces": list(self.allowed_surfaces),
            "blocked_surfaces": list(self.blocked_surfaces),
            "allowed_actions": list(self.allowed_actions),
            "blocked_actions": list(self.blocked_actions),
            "required_review": self.required_review,
            "override_required": self.override_required,
            "escalation_path": self.escalation_path,
            "scope_context": self.scope_context,
        }


# ----- M48D.1 Governance presets + scope templates -----


@dataclass
class GovernancePreset:
    """Governance preset: solo operator, supervised team, production maintainer."""
    preset_id: str = ""
    label: str = ""
    description: str = ""
    primary_role_id: str = ""  # default role for operator-facing context
    trust_preset_id: str = ""
    scope_template_id: str = ""  # optional linked scope template
    implications: list[str] = field(default_factory=list)  # operator-facing bullets
    allowed_role_ids: list[str] = field(default_factory=list)  # empty = all
    order: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "preset_id": self.preset_id,
            "label": self.label,
            "description": self.description,
            "primary_role_id": self.primary_role_id,
            "trust_preset_id": self.trust_preset_id,
            "scope_template_id": self.scope_template_id,
            "implications": list(self.implications),
            "allowed_role_ids": list(self.allowed_role_ids),
            "order": self.order,
        }


@dataclass
class ScopeTemplate:
    """Scope template for common deployment patterns."""
    template_id: str = ""
    label: str = ""
    description: str = ""
    scope_levels: list[str] = field(default_factory=list)  # e.g. ["vertical", "project"]
    default_scope_hint: str = ""
    deployment_pattern: str = ""  # solo_vertical | team_vertical_project | production_single_vertical
    order: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "label": self.label,
            "description": self.description,
            "scope_levels": list(self.scope_levels),
            "default_scope_hint": self.default_scope_hint,
            "deployment_pattern": self.deployment_pattern,
            "order": self.order,
        }
