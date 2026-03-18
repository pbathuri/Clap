"""
M40E–M40H: Production deployment bundle models — bundle, contents, runtime profile,
upgrade/rollback paths, recovery posture, deployment health.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RequiredRuntimeProfile:
    """Required runtime profile for this deployment bundle."""
    min_python: str = ""
    required_capabilities: list[str] = field(default_factory=list)
    runtime_prerequisites: list[str] = field(default_factory=list)
    machine_assumptions: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "min_python": self.min_python,
            "required_capabilities": list(self.required_capabilities),
            "runtime_prerequisites": list(self.runtime_prerequisites),
            "machine_assumptions": dict(self.machine_assumptions),
        }


@dataclass
class RequiredPacksAssets:
    """Required packs and workflow assets for this bundle."""
    pack_ids: list[str] = field(default_factory=list)
    value_pack_id: str = ""
    workflow_ids: list[str] = field(default_factory=list)
    required_approvals_setup: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pack_ids": list(self.pack_ids),
            "value_pack_id": self.value_pack_id,
            "workflow_ids": list(self.workflow_ids),
            "required_approvals_setup": list(self.required_approvals_setup),
        }


@dataclass
class BundleContents:
    """Contents of a production deployment bundle."""
    curated_pack_id: str = ""
    required_runtime: RequiredRuntimeProfile = field(default_factory=RequiredRuntimeProfile)
    required_packs: RequiredPacksAssets = field(default_factory=RequiredPacksAssets)
    allowed_trust_preset_ids: list[str] = field(default_factory=list)
    required_queue_day_workspace_refs: dict[str, str] = field(default_factory=dict)  # e.g. workday_preset_id, default_experience_profile_id
    support_recovery_refs: list[str] = field(default_factory=list)  # doc paths, runbook ids
    excluded_surface_ids: list[str] = field(default_factory=list)
    quarantined_surface_metadata: dict[str, str] = field(default_factory=dict)  # surface_id -> reason

    def to_dict(self) -> dict[str, Any]:
        return {
            "curated_pack_id": self.curated_pack_id,
            "required_runtime": self.required_runtime.to_dict(),
            "required_packs": self.required_packs.to_dict(),
            "allowed_trust_preset_ids": list(self.allowed_trust_preset_ids),
            "required_queue_day_workspace_refs": dict(self.required_queue_day_workspace_refs),
            "support_recovery_refs": list(self.support_recovery_refs),
            "excluded_surface_ids": list(self.excluded_surface_ids),
            "quarantined_surface_metadata": dict(self.quarantined_surface_metadata),
        }


@dataclass
class SupportedUpgradePath:
    """Supported upgrade path for this bundle."""
    from_version_min: str = ""
    to_version_max: str = ""
    channel_ids: list[str] = field(default_factory=list)
    reversible: bool = True
    migration_hints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_version_min": self.from_version_min,
            "to_version_max": self.to_version_max,
            "channel_ids": list(self.channel_ids),
            "reversible": self.reversible,
            "migration_hints": list(self.migration_hints),
        }


@dataclass
class SupportedRollbackPath:
    """Supported rollback path for this bundle."""
    supported: bool = True
    checkpoint_required_before_upgrade: bool = True
    rollback_hints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "supported": self.supported,
            "checkpoint_required_before_upgrade": self.checkpoint_required_before_upgrade,
            "rollback_hints": list(self.rollback_hints),
        }


@dataclass
class RecoveryPosture:
    """Recovery posture for this deployment bundle."""
    applicable_recovery_case_ids: list[str] = field(default_factory=list)
    vertical_playbook_id: str = ""
    degraded_startup_guidance: str = ""
    recovery_doc_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "applicable_recovery_case_ids": list(self.applicable_recovery_case_ids),
            "vertical_playbook_id": self.vertical_playbook_id,
            "degraded_startup_guidance": self.degraded_startup_guidance,
            "recovery_doc_refs": list(self.recovery_doc_refs),
        }


@dataclass
class DeploymentHealthSummary:
    """Deployment health summary for mission control and reports."""
    bundle_id: str = ""
    validation_passed: bool = False
    validation_errors: list[str] = field(default_factory=list)
    validation_warnings: list[str] = field(default_factory=list)
    upgrade_readiness: bool = False
    upgrade_readiness_reason: str = ""
    rollback_readiness: bool = False
    rollback_readiness_reason: str = ""
    recovery_posture_summary: str = ""
    blocked_deployment_risks: list[str] = field(default_factory=list)
    active_bundle_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "validation_passed": self.validation_passed,
            "validation_errors": list(self.validation_errors),
            "validation_warnings": list(self.validation_warnings),
            "upgrade_readiness": self.upgrade_readiness,
            "upgrade_readiness_reason": self.upgrade_readiness_reason,
            "rollback_readiness": self.rollback_readiness,
            "rollback_readiness_reason": self.rollback_readiness_reason,
            "recovery_posture_summary": self.recovery_posture_summary,
            "blocked_deployment_risks": list(self.blocked_deployment_risks),
            "active_bundle_id": self.active_bundle_id,
        }


@dataclass
class ExcludedSurfaceMetadata:
    """Metadata for an excluded or quarantined surface."""
    surface_id: str = ""
    reason: str = ""
    quarantined: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {"surface_id": self.surface_id, "reason": self.reason, "quarantined": self.quarantined}


@dataclass
class ProductionDeploymentBundle:
    """Production deployment bundle: vertical cut with contents, upgrade, rollback, recovery."""
    bundle_id: str = ""
    name: str = ""
    description: str = ""
    version: str = ""
    curated_pack_id: str = ""
    contents: BundleContents = field(default_factory=BundleContents)
    supported_upgrade_path: SupportedUpgradePath = field(default_factory=SupportedUpgradePath)
    supported_rollback_path: SupportedRollbackPath = field(default_factory=SupportedRollbackPath)
    recovery_posture: RecoveryPosture = field(default_factory=RecoveryPosture)
    generated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "curated_pack_id": self.curated_pack_id,
            "contents": self.contents.to_dict(),
            "supported_upgrade_path": self.supported_upgrade_path.to_dict(),
            "supported_rollback_path": self.supported_rollback_path.to_dict(),
            "recovery_posture": self.recovery_posture.to_dict(),
            "generated_at": self.generated_at,
        }


# ----- M40H.1 Deployment profiles + maintenance modes -----

PROFILE_DEMO = "demo"
PROFILE_INTERNAL_PRODUCTION_LIKE = "internal_production_like"
PROFILE_CAREFUL_PRODUCTION_CUT = "careful_production_cut"


@dataclass
class DeploymentProfile:
    """Deployment profile: demo, internal production-like, or careful production cut."""
    profile_id: str = ""
    name: str = ""
    description: str = ""
    profile_type: str = ""  # demo | internal_production_like | careful_production_cut
    recommended_bundle_ids: list[str] = field(default_factory=list)
    allow_operator_mode: bool = True
    allow_real_run_with_approval: bool = True
    pause_guidance: str = ""  # When to pause this profile
    repair_guidance: str = ""  # When to switch to repair/maintenance

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "description": self.description,
            "profile_type": self.profile_type,
            "recommended_bundle_ids": list(self.recommended_bundle_ids),
            "allow_operator_mode": self.allow_operator_mode,
            "allow_real_run_with_approval": self.allow_real_run_with_approval,
            "pause_guidance": self.pause_guidance,
            "repair_guidance": self.repair_guidance,
        }


MODE_UPGRADE = "upgrade"
MODE_RECOVERY = "recovery"
MODE_AUDIT_REVIEW = "audit_review"
MODE_SAFE_PAUSE = "safe_pause"


@dataclass
class MaintenanceMode:
    """Maintenance mode: upgrade, recovery, audit review, or safe pause."""
    mode_id: str = ""
    name: str = ""
    description: str = ""
    when_to_use: str = ""
    operator_guidance_pause: str = ""  # Clear guidance: when deployment should be paused
    operator_guidance_repair: str = ""  # Clear guidance: when to run repair steps
    recommended_actions: list[str] = field(default_factory=list)
    blocks_real_run: bool = False
    blocks_operator_mode: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode_id": self.mode_id,
            "name": self.name,
            "description": self.description,
            "when_to_use": self.when_to_use,
            "operator_guidance_pause": self.operator_guidance_pause,
            "operator_guidance_repair": self.operator_guidance_repair,
            "recommended_actions": list(self.recommended_actions),
            "blocks_real_run": self.blocks_real_run,
            "blocks_operator_mode": self.blocks_operator_mode,
        }


@dataclass
class MaintenanceModeReport:
    """Report of current maintenance state and operator guidance."""
    active_profile_id: str = ""
    active_maintenance_mode_id: str = ""
    should_pause: bool = False
    should_repair: bool = False
    pause_reason: str = ""
    repair_reason: str = ""
    operator_guidance_summary: str = ""
    recommended_actions: list[str] = field(default_factory=list)
    profile: dict[str, Any] = field(default_factory=dict)
    maintenance_mode: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_profile_id": self.active_profile_id,
            "active_maintenance_mode_id": self.active_maintenance_mode_id,
            "should_pause": self.should_pause,
            "should_repair": self.should_repair,
            "pause_reason": self.pause_reason,
            "repair_reason": self.repair_reason,
            "operator_guidance_summary": self.operator_guidance_summary,
            "recommended_actions": list(self.recommended_actions),
            "profile": dict(self.profile),
            "maintenance_mode": dict(self.maintenance_mode),
        }
