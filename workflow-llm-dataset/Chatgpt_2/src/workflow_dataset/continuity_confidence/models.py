"""
M49I–M49L: Device-aware continuity models.
Target device profile, post-restore runtime profile, continuity confidence, downgraded/promoted capability, adjustments, recommended posture.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DeviceCapabilityClass(str, Enum):
    """Relative capability of target vs source (for comparison)."""
    STRONGER = "stronger"
    SAME = "same"
    WEAKER = "weaker"
    DIFFERENT = "different"
    UNKNOWN = "unknown"


class ContinuityConfidenceClass(str, Enum):
    """Post-restore continuity confidence classification."""
    HIGH_CONFIDENCE = "high_confidence"
    USABLE_DEGRADED = "usable_degraded"
    REVIEW_REQUIRED = "review_required"
    NARROWED_PRODUCTION_CUT = "narrowed_production_cut"
    OPERATOR_MODE_NOT_TRUSTED = "operator_mode_not_trusted"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


@dataclass
class TargetDeviceProfile:
    """Target device runtime profile: runtime, tier, capability class for comparison."""
    profile_id: str = ""
    device_id: str = ""  # optional identifier; e.g. current_machine
    runtime_id: str = ""
    edge_tier: str = ""  # dev_full | local_standard | constrained_edge | minimal_eval
    product_version: str = ""
    capability_class: str = DeviceCapabilityClass.UNKNOWN.value
    allowed_backends: list[str] = field(default_factory=list)
    has_llm_backend: bool = False
    notes: str = ""
    created_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "device_id": self.device_id,
            "runtime_id": self.runtime_id,
            "edge_tier": self.edge_tier,
            "product_version": self.product_version,
            "capability_class": self.capability_class,
            "allowed_backends": list(self.allowed_backends),
            "has_llm_backend": self.has_llm_backend,
            "notes": self.notes,
            "created_utc": self.created_utc,
        }


@dataclass
class PostRestoreRuntimeProfile:
    """Runtime profile after restore: device-safe mode, routing policy, production cut scope."""
    profile_id: str = ""
    target_device_profile_id: str = ""
    recommended_routing_policy_id: str = ""
    recommended_vertical_id: str = ""
    production_cut_narrowed: bool = False
    production_cut_scope_note: str = ""
    allow_degraded_fallback: bool = True
    operator_mode_ready: bool = False
    operator_mode_scope_note: str = ""
    created_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "target_device_profile_id": self.target_device_profile_id,
            "recommended_routing_policy_id": self.recommended_routing_policy_id,
            "recommended_vertical_id": self.recommended_vertical_id,
            "production_cut_narrowed": self.production_cut_narrowed,
            "production_cut_scope_note": self.production_cut_scope_note,
            "allow_degraded_fallback": self.allow_degraded_fallback,
            "operator_mode_ready": self.operator_mode_ready,
            "operator_mode_scope_note": self.operator_mode_scope_note,
            "created_utc": self.created_utc,
        }


@dataclass
class ContinuityConfidenceScore:
    """Continuity confidence score and classification after restore."""
    score: float = 0.0  # 0.0–1.0
    classification: str = ContinuityConfidenceClass.UNKNOWN.value
    label: str = ""  # human-readable: High-confidence continuity, Usable with degraded capabilities, etc.
    reasons: list[str] = field(default_factory=list)
    generated_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "classification": self.classification,
            "label": self.label,
            "reasons": list(self.reasons),
            "generated_at_utc": self.generated_at_utc,
        }


@dataclass
class DowngradedCapabilityNote:
    """A capability that is weaker or unavailable on the target after restore."""
    note_id: str = ""
    subsystem_or_feature: str = ""
    description: str = ""
    recommendation: str = ""
    created_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "note_id": self.note_id,
            "subsystem_or_feature": self.subsystem_or_feature,
            "description": self.description,
            "recommendation": self.recommendation,
            "created_utc": self.created_utc,
        }


@dataclass
class PromotedCapabilityNote:
    """A capability that is stronger or newly available on the target after restore."""
    note_id: str = ""
    subsystem_or_feature: str = ""
    description: str = ""
    created_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "note_id": self.note_id,
            "subsystem_or_feature": self.subsystem_or_feature,
            "description": self.description,
            "created_utc": self.created_utc,
        }


@dataclass
class ModelRouteAdjustment:
    """Recommendation to adjust model or runtime route for the restored device."""
    adjustment_id: str = ""
    task_family_or_vertical: str = ""
    current_route: str = ""
    recommended_route: str = ""
    reason: str = ""
    created_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "adjustment_id": self.adjustment_id,
            "task_family_or_vertical": self.task_family_or_vertical,
            "current_route": self.current_route,
            "recommended_route": self.recommended_route,
            "reason": self.reason,
            "created_utc": self.created_utc,
        }


@dataclass
class OperatorModeSafetyAdjustment:
    """Recommendation to adjust operator-mode safe scopes after restore."""
    adjustment_id: str = ""
    scope_or_domain: str = ""
    recommended_action: str = ""  # narrow | suspend | allow_after_review | no_change
    reason: str = ""
    created_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "adjustment_id": self.adjustment_id,
            "scope_or_domain": self.scope_or_domain,
            "recommended_action": self.recommended_action,
            "reason": self.reason,
            "created_utc": self.created_utc,
        }


@dataclass
class RecommendedOperatingPosture:
    """Single recommended operating posture after restore."""
    posture_id: str = ""
    label: str = ""
    description: str = ""
    production_cut_narrowed: bool = False
    operator_mode_trusted: bool = False
    require_review_before_production: bool = False
    next_review_action: str = ""
    created_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "posture_id": self.posture_id,
            "label": self.label,
            "description": self.description,
            "production_cut_narrowed": self.production_cut_narrowed,
            "operator_mode_trusted": self.operator_mode_trusted,
            "require_review_before_production": self.require_review_before_production,
            "next_review_action": self.next_review_action,
            "created_utc": self.created_utc,
        }


# ----- M49L.1 Device classes + post-restore operating presets -----


@dataclass
class DeviceClass:
    """Device class: full local workstation, constrained laptop, recovery-safe environment, etc."""
    class_id: str = ""
    label: str = ""
    description: str = ""
    edge_tiers: list[str] = field(default_factory=list)  # e.g. ["dev_full", "local_standard"]
    requires_llm_backend: bool = False
    typical_backends: list[str] = field(default_factory=list)
    safe_for_operator_mode_default: bool = False
    when_to_use: str = ""
    created_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "class_id": self.class_id,
            "label": self.label,
            "description": self.description,
            "edge_tiers": list(self.edge_tiers),
            "requires_llm_backend": self.requires_llm_backend,
            "typical_backends": list(self.typical_backends),
            "safe_for_operator_mode_default": self.safe_for_operator_mode_default,
            "when_to_use": self.when_to_use,
            "created_utc": self.created_utc,
        }


@dataclass
class PostRestoreOperatingPreset:
    """Post-restore operating preset: how to run the product safely after migration."""
    preset_id: str = ""
    label: str = ""
    description: str = ""
    recommended_routing_policy_id: str = ""
    production_cut_narrowed: bool = False
    operator_mode_trusted: bool = False
    require_review_before_production: bool = False
    do_after_migration: list[str] = field(default_factory=list)
    avoid_after_migration: list[str] = field(default_factory=list)
    next_review_action: str = ""
    when_to_use: str = ""
    created_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "preset_id": self.preset_id,
            "label": self.label,
            "description": self.description,
            "recommended_routing_policy_id": self.recommended_routing_policy_id,
            "production_cut_narrowed": self.production_cut_narrowed,
            "operator_mode_trusted": self.operator_mode_trusted,
            "require_review_before_production": self.require_review_before_production,
            "do_after_migration": list(self.do_after_migration),
            "avoid_after_migration": list(self.avoid_after_migration),
            "next_review_action": self.next_review_action,
            "when_to_use": self.when_to_use,
            "created_utc": self.created_utc,
        }


@dataclass
class PostRestoreSafeOperatingGuidance:
    """Operator-facing guidance: how to run the product safely after migration."""
    device_class_id: str = ""
    device_class_label: str = ""
    recommended_preset_id: str = ""
    recommended_preset_label: str = ""
    do_after_migration: list[str] = field(default_factory=list)
    avoid_after_migration: list[str] = field(default_factory=list)
    summary: str = ""
    next_review_action: str = ""
    generated_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_class_id": self.device_class_id,
            "device_class_label": self.device_class_label,
            "recommended_preset_id": self.recommended_preset_id,
            "recommended_preset_label": self.recommended_preset_label,
            "do_after_migration": list(self.do_after_migration),
            "avoid_after_migration": list(self.avoid_after_migration),
            "summary": self.summary,
            "next_review_action": self.next_review_action,
            "generated_at_utc": self.generated_at_utc,
        }
