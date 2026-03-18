"""
M30A–M30D: Install bundle + upgrade / migration manager. Local-first; operator-controlled.
"""

from workflow_dataset.install_upgrade.models import (
    ProductVersion,
    EnvRequirements,
    EnabledModulesSnapshot,
    PackRuntimeSnapshot,
    InstallProfile,
    MigrationRequirement,
    RollbackCheckpoint,
    ReleaseChannel,
    CHANNEL_STABLE,
    CHANNEL_PREVIEW,
    CHANNEL_INTERNAL,
)
from workflow_dataset.install_upgrade.version import (
    read_current_version,
    write_current_version,
    get_package_version_from_pyproject,
    get_current_version_display,
    get_install_dir,
)
from workflow_dataset.install_upgrade.upgrade_plan import (
    build_upgrade_plan,
    format_upgrade_plan,
    UpgradePlan,
)
from workflow_dataset.install_upgrade.apply_upgrade import (
    apply_upgrade,
    list_rollback_checkpoints,
    perform_rollback,
    create_rollback_checkpoint,
)
from workflow_dataset.install_upgrade.reports import build_migration_report, format_migration_report
from workflow_dataset.install_upgrade.channels import get_channel, list_channels, RELEASE_CHANNELS
from workflow_dataset.install_upgrade.compatibility import (
    build_compatibility_matrix,
    format_compatibility_matrix,
    check_upgrade_path,
    get_unsafe_upgrade_warnings,
)

__all__ = [
    "ProductVersion",
    "EnvRequirements",
    "EnabledModulesSnapshot",
    "PackRuntimeSnapshot",
    "InstallProfile",
    "MigrationRequirement",
    "RollbackCheckpoint",
    "ReleaseChannel",
    "CHANNEL_STABLE",
    "CHANNEL_PREVIEW",
    "CHANNEL_INTERNAL",
    "read_current_version",
    "write_current_version",
    "get_package_version_from_pyproject",
    "get_current_version_display",
    "get_install_dir",
    "build_upgrade_plan",
    "format_upgrade_plan",
    "UpgradePlan",
    "apply_upgrade",
    "list_rollback_checkpoints",
    "perform_rollback",
    "create_rollback_checkpoint",
    "build_migration_report",
    "format_migration_report",
    "get_channel",
    "list_channels",
    "RELEASE_CHANNELS",
    "build_compatibility_matrix",
    "format_compatibility_matrix",
    "check_upgrade_path",
    "get_unsafe_upgrade_warnings",
]
