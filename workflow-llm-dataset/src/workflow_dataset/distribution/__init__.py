"""
M24R–M24U: Distribution layer — install bundle, pack-aware install profile,
field deployment profile, update planner, field checklists, deploy readiness.
Local-first; no cloud; no auto-update.
"""

from workflow_dataset.distribution.models import InstallBundle, FieldDeploymentProfile, PackAwareInstallProfile
from workflow_dataset.distribution.bundle import build_install_bundle, write_install_bundle
from workflow_dataset.distribution.install_profile import (
    build_pack_aware_install_profile,
    build_field_deployment_profile,
)
from workflow_dataset.distribution.update_planner import (
    build_update_plan,
    format_update_plan,
    UpdatePlan,
)
from workflow_dataset.distribution.checklists import (
    build_field_checklist,
    format_field_checklist,
    list_checklist_packs,
)
from workflow_dataset.distribution.readiness import build_deploy_readiness, format_deploy_readiness
from workflow_dataset.distribution.handoff_pack import (
    build_handoff_pack,
    write_handoff_pack,
    format_handoff_readme,
    format_release_bundle_summary,
)

__all__ = [
    "InstallBundle",
    "FieldDeploymentProfile",
    "PackAwareInstallProfile",
    "build_install_bundle",
    "write_install_bundle",
    "build_pack_aware_install_profile",
    "build_field_deployment_profile",
    "build_update_plan",
    "format_update_plan",
    "UpdatePlan",
    "build_field_checklist",
    "format_field_checklist",
    "list_checklist_packs",
    "build_deploy_readiness",
    "format_deploy_readiness",
    "build_handoff_pack",
    "write_handoff_pack",
    "format_handoff_readme",
    "format_release_bundle_summary",
]
