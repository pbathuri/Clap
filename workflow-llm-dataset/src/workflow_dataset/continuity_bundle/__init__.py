"""
M49A–M49D: Portable state model + continuity bundle — local-first portable continuity.
"""

from workflow_dataset.continuity_bundle.models import (
    PortableStateClass,
    NonPortableStateClass,
    BundleComponent,
    ContinuityBundle,
    BundleProvenance,
    TransferClass,
)
from workflow_dataset.continuity_bundle.components import (
    get_component,
    list_components,
    get_component_registry,
)
from workflow_dataset.continuity_bundle.build import (
    create_bundle,
    inspect_bundle,
    validate_bundle,
)
from workflow_dataset.continuity_bundle.portability import (
    get_portability_boundaries,
    explain_component,
)
from workflow_dataset.continuity_bundle.mission_control import continuity_bundle_slice
from workflow_dataset.continuity_bundle.profiles import (
    get_profile,
    list_profiles,
    resolve_profile_components,
    BundleProfile,
    PROFILE_PERSONAL_CORE,
    PROFILE_PRODUCTION_CUT,
    PROFILE_MAINTENANCE_SAFE,
)
from workflow_dataset.continuity_bundle.sensitivity_policies import (
    get_sensitivity_policy,
    list_sensitivity_policies,
    apply_policy_to_boundaries,
    SensitivityPolicy,
    POLICY_TRANSFER_WITH_REVIEW,
    POLICY_EXCLUDE_SENSITIVE,
    POLICY_STRICT_SAFE_ONLY,
)
from workflow_dataset.continuity_bundle.reports import (
    get_portability_report,
    format_portability_report_text,
)

__all__ = [
    "BundleComponent",
    "BundleProvenance",
    "ContinuityBundle",
    "NonPortableStateClass",
    "PortableStateClass",
    "TransferClass",
    "create_bundle",
    "explain_component",
    "get_component",
    "get_component_registry",
    "get_portability_boundaries",
    "inspect_bundle",
    "list_components",
    "continuity_bundle_slice",
    "validate_bundle",
    "get_profile",
    "list_profiles",
    "resolve_profile_components",
    "BundleProfile",
    "PROFILE_PERSONAL_CORE",
    "PROFILE_PRODUCTION_CUT",
    "PROFILE_MAINTENANCE_SAFE",
    "get_sensitivity_policy",
    "list_sensitivity_policies",
    "apply_policy_to_boundaries",
    "SensitivityPolicy",
    "POLICY_TRANSFER_WITH_REVIEW",
    "POLICY_EXCLUDE_SENSITIVE",
    "POLICY_STRICT_SAFE_ONLY",
    "get_portability_report",
    "format_portability_report_text",
]
