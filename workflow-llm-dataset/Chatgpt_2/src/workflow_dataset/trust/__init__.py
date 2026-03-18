"""
M23V/M23Q: Trust / evidence cockpit — benchmark trust, approval readiness, job/macro trust, corrections, release gates, readiness report.
M35A–M35D: Authority tiers and trusted routine contracts — tiers, contracts, scope, explain.
"""

from workflow_dataset.trust.cockpit import build_trust_cockpit
from workflow_dataset.trust.release_gates import evaluate_release_gates, safe_to_expand

# M35A–M35D authority tiers and trusted routine contracts
from workflow_dataset.trust.tiers import (
    AuthorityTier,
    AuthorityTierId,
    list_tiers,
    get_tier,
    tier_allows_action,
    BUILTIN_TIERS,
)
from workflow_dataset.trust.contracts import (
    TrustedRoutineContract,
    load_contracts,
    save_contracts,
    get_contract,
    get_contracts_for_routine,
    validate_contract,
)
from workflow_dataset.trust.scope import (
    effective_contract,
    merge_contract_with_tier,
    SCOPE_ORDER,
)
from workflow_dataset.trust.explain_contract import (
    explain_why_allowed,
    explain_why_blocked,
    explain_routine,
)
# M35D.1 trust presets and eligibility
from workflow_dataset.trust.presets import (
    TrustPreset,
    BUILTIN_PRESETS,
    get_preset,
    list_presets,
    preset_allows_tier,
)
from workflow_dataset.trust.eligibility import (
    ROUTINE_TYPES,
    routine_type_for,
    is_eligible,
    eligibility_matrix_report,
    max_tier_for_routine_under_preset,
)
from workflow_dataset.trust.validation_report import (
    TrustValidationReport,
    TrustConfigIssue,
    validate_trust_config,
    format_validation_report,
    get_active_preset_id,
)

__all__ = [
    "build_trust_cockpit",
    "evaluate_release_gates",
    "safe_to_expand",
    "AuthorityTier",
    "AuthorityTierId",
    "list_tiers",
    "get_tier",
    "tier_allows_action",
    "BUILTIN_TIERS",
    "TrustedRoutineContract",
    "load_contracts",
    "save_contracts",
    "get_contract",
    "get_contracts_for_routine",
    "validate_contract",
    "effective_contract",
    "merge_contract_with_tier",
    "SCOPE_ORDER",
    "explain_why_allowed",
    "explain_why_blocked",
    "explain_routine",
    "TrustPreset",
    "BUILTIN_PRESETS",
    "get_preset",
    "list_presets",
    "preset_allows_tier",
    "ROUTINE_TYPES",
    "routine_type_for",
    "is_eligible",
    "eligibility_matrix_report",
    "max_tier_for_routine_under_preset",
    "TrustValidationReport",
    "TrustConfigIssue",
    "validate_trust_config",
    "format_validation_report",
    "get_active_preset_id",
]
