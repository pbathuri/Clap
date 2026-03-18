"""
M48I–M48L: Governed operator mode and delegation safety.
Binds operator mode to role and review domains; delegation scope, suspend/revoke, explanation.
"""

from workflow_dataset.governed_operator.models import (
    GovernedOperatorMode,
    GovernedOperatorStatus,
    DelegatedScope,
    DelegatedActionBoundary,
    DelegationSafeLoop,
    SuspensionTrigger,
    RevocationTrigger,
    GovernedContinuationApproval,
    OperatorModeDomainConflict,
    DelegationExplanation,
    TriggerKind,
    DelegationPreset,
    ReauthorizationPlaybook,
    SuspensionRevocationGuidance,
)
from workflow_dataset.governed_operator.presets import (
    list_delegation_presets,
    get_delegation_preset,
)
from workflow_dataset.governed_operator.playbooks import (
    list_reauthorization_playbooks,
    get_reauthorization_playbook,
    get_playbook_for_situation,
)
from workflow_dataset.governed_operator.guidance import suspension_revocation_guidance
from workflow_dataset.governed_operator.store import (
    list_scope_ids,
    get_scope,
    save_scope,
    load_governed_state,
    save_governed_state,
    list_loop_ids,
    get_loop,
    save_loop,
)
from workflow_dataset.governed_operator.controls import (
    role_safe_delegation,
    domain_bound_delegation,
    action_restrictions_by_role_scope,
    supervised_continuation_allowed,
    suspend_on_policy_or_confidence,
    revoke_on_unsafe_or_conflict,
    check_delegation,
)
from workflow_dataset.governed_operator.flows import (
    suspend_delegated_loop,
    revoke_delegated_scope,
    require_reauthorization,
    narrow_operator_scope,
    explain_delegation,
    clear_suspension,
)
from workflow_dataset.governed_operator.mission_control import governed_operator_slice

__all__ = [
    "GovernedOperatorMode",
    "GovernedOperatorStatus",
    "DelegatedScope",
    "DelegatedActionBoundary",
    "DelegationSafeLoop",
    "SuspensionTrigger",
    "RevocationTrigger",
    "GovernedContinuationApproval",
    "OperatorModeDomainConflict",
    "DelegationExplanation",
    "TriggerKind",
    "list_scope_ids",
    "get_scope",
    "save_scope",
    "load_governed_state",
    "save_governed_state",
    "list_loop_ids",
    "get_loop",
    "save_loop",
    "role_safe_delegation",
    "domain_bound_delegation",
    "action_restrictions_by_role_scope",
    "supervised_continuation_allowed",
    "suspend_on_policy_or_confidence",
    "revoke_on_unsafe_or_conflict",
    "check_delegation",
    "suspend_delegated_loop",
    "revoke_delegated_scope",
    "require_reauthorization",
    "narrow_operator_scope",
    "explain_delegation",
    "clear_suspension",
    "governed_operator_slice",
    "DelegationPreset",
    "ReauthorizationPlaybook",
    "SuspensionRevocationGuidance",
    "list_delegation_presets",
    "get_delegation_preset",
    "list_reauthorization_playbooks",
    "get_reauthorization_playbook",
    "get_playbook_for_situation",
    "suspension_revocation_guidance",
]
