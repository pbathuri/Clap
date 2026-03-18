"""
M40A: Production cut model — final vertical lock and production surface freeze.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class IncludedSurface:
    """Surface included in the production cut (default-visible, supported)."""
    surface_id: str = ""
    label: str = ""
    policy_level: str = "recommended"  # recommended | allowed
    is_default_visible: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface_id": self.surface_id,
            "label": self.label,
            "policy_level": self.policy_level,
            "is_default_visible": self.is_default_visible,
        }


@dataclass
class ExcludedSurface:
    """Surface explicitly excluded from the production cut (non-core, blocked, or out of scope)."""
    surface_id: str = ""
    label: str = ""
    reason: str = ""  # non_core | blocked | out_of_scope

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface_id": self.surface_id,
            "label": self.label,
            "reason": self.reason,
        }


@dataclass
class QuarantinedExperimentalSurface:
    """Experimental surface in quarantine (visible only under policy; not in supported default)."""
    surface_id: str = ""
    label: str = ""
    reveal_rule: str = "on_demand"  # on_demand | after_first_milestone | never

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface_id": self.surface_id,
            "label": self.label,
            "reveal_rule": self.reveal_rule,
        }


@dataclass
class SupportedWorkflowSet:
    """Primary supported workflow set for the production cut."""
    workflow_ids: list[str] = field(default_factory=list)
    path_id: str = ""
    label: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_ids": list(self.workflow_ids),
            "path_id": self.path_id,
            "label": self.label,
            "description": self.description,
        }


@dataclass
class RequiredTrustPosture:
    """Required trust posture for the deployment cut."""
    trust_preset_id: str = ""
    review_gates_default: list[str] = field(default_factory=list)
    audit_posture: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "trust_preset_id": self.trust_preset_id,
            "review_gates_default": list(self.review_gates_default),
            "audit_posture": self.audit_posture,
            "description": self.description,
        }


@dataclass
class DefaultOperatingProfile:
    """Default operating profile for the production cut (queue/day/workspace)."""
    workday_preset_id: str = ""
    default_experience_profile_id: str = ""
    queue_section_order: list[str] = field(default_factory=list)
    operator_mode_usage: str = ""  # preferred | optional | rare | none
    role_operating_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "workday_preset_id": self.workday_preset_id,
            "default_experience_profile_id": self.default_experience_profile_id,
            "queue_section_order": list(self.queue_section_order),
            "operator_mode_usage": self.operator_mode_usage,
            "role_operating_hint": self.role_operating_hint,
        }


@dataclass
class ProductionReadinessNote:
    """Human-readable production readiness note for the cut."""
    summary: str = ""
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    last_updated_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "last_updated_utc": self.last_updated_utc,
        }


# M40D.1: Production defaults + experimental quarantine rules + production-safe labeling


@dataclass
class ProductionDefaultProfile:
    """M40D.1: Production-default workspace/day/queue profile for the cut (operator-facing)."""
    label: str = ""  # e.g. "Production default for Founder / Operator (core)"
    vertical_id: str = ""
    workspace_preset_id: str = ""
    workday_preset_id: str = ""
    queue_section_order: list[str] = field(default_factory=list)
    default_experience_profile_id: str = ""
    operator_mode_usage: str = ""
    role_operating_hint: str = ""
    operator_summary: str = ""  # One-line for mission control / CLI

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "vertical_id": self.vertical_id,
            "workspace_preset_id": self.workspace_preset_id,
            "workday_preset_id": self.workday_preset_id,
            "queue_section_order": list(self.queue_section_order),
            "default_experience_profile_id": self.default_experience_profile_id,
            "operator_mode_usage": self.operator_mode_usage,
            "role_operating_hint": self.role_operating_hint,
            "operator_summary": self.operator_summary,
        }


@dataclass
class ExperimentalQuarantineRule:
    """M40D.1: Rule for when an experimental (quarantined) surface is available."""
    surface_id: str = ""
    label: str = ""
    reveal_rule: str = ""  # on_demand | after_first_milestone | never
    condition_summary: str = ""  # e.g. "Only after first-value milestone"
    operator_explanation: str = ""  # Clear operator-facing text
    production_safe: bool = False  # Always false for quarantined

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface_id": self.surface_id,
            "label": self.label,
            "reveal_rule": self.reveal_rule,
            "condition_summary": self.condition_summary,
            "operator_explanation": self.operator_explanation,
            "production_safe": self.production_safe,
        }


@dataclass
class ProductionSafeLabel:
    """M40D.1: Stricter production-safe vs non-production-safe label per surface."""
    surface_id: str = ""
    label: str = ""
    production_safe: bool = True
    reason_if_not_safe: str = ""  # "" | "experimental" | "excluded" | "out_of_scope" | "advanced_only"

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface_id": self.surface_id,
            "label": self.label,
            "production_safe": self.production_safe,
            "reason_if_not_safe": self.reason_if_not_safe,
        }


@dataclass
class ChosenPrimaryVertical:
    """Chosen primary deployment vertical for the production cut."""
    vertical_id: str = ""
    label: str = ""
    description: str = ""
    selection_reason: str = ""
    primary_workflow_ids: list[str] = field(default_factory=list)
    allowed_roles: list[str] = field(default_factory=list)  # e.g. founder_operator, analyst
    allowed_modes: list[str] = field(default_factory=list)  # e.g. operator_mode, calm
    non_core_surface_ids: list[str] = field(default_factory=list)
    excluded_surface_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "vertical_id": self.vertical_id,
            "label": self.label,
            "description": self.description,
            "selection_reason": self.selection_reason,
            "primary_workflow_ids": list(self.primary_workflow_ids),
            "allowed_roles": list(self.allowed_roles),
            "allowed_modes": list(self.allowed_modes),
            "non_core_surface_ids": list(self.non_core_surface_ids),
            "excluded_surface_ids": list(self.excluded_surface_ids),
        }


@dataclass
class ProductionCut:
    """M40A: Production cut — final vertical lock and frozen surface set."""
    cut_id: str = ""  # e.g. founder_operator_primary
    vertical_id: str = ""
    label: str = ""
    frozen_at_utc: str = ""
    chosen_vertical: ChosenPrimaryVertical | None = None
    included_surface_ids: list[str] = field(default_factory=list)
    excluded_surface_ids: list[str] = field(default_factory=list)
    quarantined_surface_ids: list[str] = field(default_factory=list)
    supported_workflows: SupportedWorkflowSet | None = None
    required_trust: RequiredTrustPosture | None = None
    default_profile: DefaultOperatingProfile | None = None
    production_readiness_note: ProductionReadinessNote | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "cut_id": self.cut_id,
            "vertical_id": self.vertical_id,
            "label": self.label,
            "frozen_at_utc": self.frozen_at_utc,
            "chosen_vertical": self.chosen_vertical.to_dict() if self.chosen_vertical else None,
            "included_surface_ids": list(self.included_surface_ids),
            "excluded_surface_ids": list(self.excluded_surface_ids),
            "quarantined_surface_ids": list(self.quarantined_surface_ids),
            "supported_workflows": self.supported_workflows.to_dict() if self.supported_workflows else None,
            "required_trust": self.required_trust.to_dict() if self.required_trust else None,
            "default_profile": self.default_profile.to_dict() if self.default_profile else None,
            "production_readiness_note": self.production_readiness_note.to_dict() if self.production_readiness_note else None,
        }
