"""
M40E–M40H: Production deployment bundle — bundle model, packaging, validation, upgrade/rollback, recovery report, health.
"""

from workflow_dataset.deploy_bundle.models import (
    ProductionDeploymentBundle,
    BundleContents,
    RequiredRuntimeProfile,
    RequiredPacksAssets,
    SupportedUpgradePath,
    SupportedRollbackPath,
    RecoveryPosture,
    DeploymentHealthSummary,
    ExcludedSurfaceMetadata,
    DeploymentProfile,
    MaintenanceMode,
    MaintenanceModeReport,
    PROFILE_DEMO,
    PROFILE_INTERNAL_PRODUCTION_LIKE,
    PROFILE_CAREFUL_PRODUCTION_CUT,
    MODE_UPGRADE,
    MODE_RECOVERY,
    MODE_AUDIT_REVIEW,
    MODE_SAFE_PAUSE,
)
from workflow_dataset.deploy_bundle.registry import (
    get_deployment_bundle,
    list_deployment_bundle_ids,
    BUILTIN_DEPLOYMENT_BUNDLES,
)
from workflow_dataset.deploy_bundle.store import (
    get_active_bundle,
    set_active_bundle,
    set_deployment_profile,
    set_maintenance_mode,
    get_deploy_bundle_dir,
)
from workflow_dataset.deploy_bundle.profiles import (
    get_deployment_profile,
    list_deployment_profile_ids,
    BUILTIN_DEPLOYMENT_PROFILES,
)
from workflow_dataset.deploy_bundle.maintenance_modes import (
    get_maintenance_mode,
    list_maintenance_mode_ids,
    build_maintenance_mode_report,
    BUILTIN_MAINTENANCE_MODES,
)
from workflow_dataset.deploy_bundle.packaging import build_bundle_manifest, write_bundle_manifest
from workflow_dataset.deploy_bundle.validation import validate_bundle, BundleValidationResult
from workflow_dataset.deploy_bundle.upgrade_rollback import (
    get_supported_upgrade_path,
    get_rollback_readiness,
    get_risky_upgrade_warnings,
)
from workflow_dataset.deploy_bundle.recovery_report import build_recovery_report
from workflow_dataset.deploy_bundle.health import build_deployment_health_summary

__all__ = [
    "ProductionDeploymentBundle",
    "BundleContents",
    "RequiredRuntimeProfile",
    "RequiredPacksAssets",
    "SupportedUpgradePath",
    "SupportedRollbackPath",
    "RecoveryPosture",
    "DeploymentHealthSummary",
    "ExcludedSurfaceMetadata",
    "DeploymentProfile",
    "MaintenanceMode",
    "MaintenanceModeReport",
    "PROFILE_DEMO",
    "PROFILE_INTERNAL_PRODUCTION_LIKE",
    "PROFILE_CAREFUL_PRODUCTION_CUT",
    "MODE_UPGRADE",
    "MODE_RECOVERY",
    "MODE_AUDIT_REVIEW",
    "MODE_SAFE_PAUSE",
    "get_deployment_bundle",
    "list_deployment_bundle_ids",
    "BUILTIN_DEPLOYMENT_BUNDLES",
    "get_active_bundle",
    "set_active_bundle",
    "set_deployment_profile",
    "set_maintenance_mode",
    "get_deploy_bundle_dir",
    "get_deployment_profile",
    "list_deployment_profile_ids",
    "BUILTIN_DEPLOYMENT_PROFILES",
    "get_maintenance_mode",
    "list_maintenance_mode_ids",
    "build_maintenance_mode_report",
    "BUILTIN_MAINTENANCE_MODES",
    "build_bundle_manifest",
    "write_bundle_manifest",
    "validate_bundle",
    "BundleValidationResult",
    "get_supported_upgrade_path",
    "get_rollback_readiness",
    "get_risky_upgrade_warnings",
    "build_recovery_report",
    "build_deployment_health_summary",
]
