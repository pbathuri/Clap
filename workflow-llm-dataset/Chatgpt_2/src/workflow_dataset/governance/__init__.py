"""
M48A–M48D: Role model + scope-bound authority controls — local-first governance layer.
"""

from workflow_dataset.governance.models import (
    HumanRole,
    AuthorityScope,
    RoleAuthorityBinding,
    ReviewRequirement,
    OverrideRequirement,
    EscalationPath,
    ScopeConflict,
    CheckResult,
    AuthorityExplanation,
    GovernancePreset,
    ScopeTemplate,
)
from workflow_dataset.governance.roles import get_role, list_roles
from workflow_dataset.governance.presets import (
    list_presets,
    get_preset,
    get_active_preset,
    set_active_preset,
)
from workflow_dataset.governance.scope_templates import list_scope_templates, get_scope_template
from workflow_dataset.governance.reports import format_governance_preset_report
from workflow_dataset.governance.scope import (
    ScopeLevel,
    resolve_scope,
    scope_precedence_rank,
)
from workflow_dataset.governance.bindings import get_effective_binding
from workflow_dataset.governance.check import can_role_perform_action
from workflow_dataset.governance.explain import explain_authority
from workflow_dataset.governance.mission_control import governance_slice

__all__ = [
    "AuthorityExplanation",
    "AuthorityScope",
    "CheckResult",
    "EscalationPath",
    "GovernancePreset",
    "HumanRole",
    "OverrideRequirement",
    "ReviewRequirement",
    "RoleAuthorityBinding",
    "ScopeConflict",
    "ScopeLevel",
    "ScopeTemplate",
    "can_role_perform_action",
    "explain_authority",
    "format_governance_preset_report",
    "get_active_preset",
    "get_effective_binding",
    "get_preset",
    "get_role",
    "get_scope_template",
    "governance_slice",
    "list_presets",
    "list_roles",
    "list_scope_templates",
    "resolve_scope",
    "scope_precedence_rank",
    "set_active_preset",
]
