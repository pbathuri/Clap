"""
M48C: Authority checks — can role perform action; review vs approve.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.governance.models import CheckResult, EscalationPath
from workflow_dataset.governance.roles import get_role
from workflow_dataset.governance.bindings import get_effective_binding
from workflow_dataset.trust.tiers import get_tier, tier_allows_action


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def can_role_perform_action(
    role_id: str,
    action_class: str,
    scope_hint: str | None = None,
    surface_id: str | None = None,
    repo_root: Path | str | None = None,
) -> CheckResult:
    """
    Check whether the role may perform the action (and optionally on the surface).
    Returns CheckResult(allowed, reason, required_review, required_approval, escalation_path).
    """
    root = _root(repo_root)
    role = get_role(role_id)
    if role is None:
        return CheckResult(
            allowed=False,
            reason=f"Unknown role: {role_id}.",
            binding_scope="",
        )
    binding = get_effective_binding(role_id, scope_hint, root)
    if binding is None:
        return CheckResult(
            allowed=False,
            reason="No effective binding for role at scope.",
            binding_scope=scope_hint or "product_wide",
        )
    if surface_id and binding.effective_surface_ids and surface_id not in binding.effective_surface_ids:
        return CheckResult(
            allowed=False,
            reason=f"Surface '{surface_id}' not in effective surfaces for this role at scope.",
            required_review=binding.review_required,
            binding_scope=binding.scope_level,
        )
    if role.forbidden_surface_ids and surface_id and surface_id in role.forbidden_surface_ids:
        return CheckResult(
            allowed=False,
            reason=f"Surface '{surface_id}' is forbidden for role '{role_id}'.",
            escalation_path=EscalationPath(
                from_role_id=role_id,
                to_role_id="approver" if role_id != "approver" else "maintainer",
                trigger="blocked",
                description="Escalate to approver or maintainer for this surface.",
            ),
            binding_scope=binding.scope_level,
        )
    if action_class in role.forbidden_action_classes:
        return CheckResult(
            allowed=False,
            reason=f"Action '{action_class}' is forbidden for role '{role_id}'.",
            required_approval=True,
            escalation_path=EscalationPath(
                from_role_id=role_id,
                to_role_id="approver",
                trigger="blocked",
                description="Approver may grant or execute in designated domain.",
            ),
            binding_scope=binding.scope_level,
        )
    if binding.effective_action_classes and action_class not in binding.effective_action_classes:
        return CheckResult(
            allowed=False,
            reason=f"Action '{action_class}' not in effective action set at this scope (trust cap: {binding.authority_tier_id}).",
            required_review=binding.review_required,
            required_approval=binding.override_required,
            escalation_path=EscalationPath(
                from_role_id=role_id,
                to_role_id="maintainer" if role_id != "maintainer" else "support_reviewer",
                trigger="blocked",
                description="Escalate for higher authority scope.",
            ),
            binding_scope=binding.scope_level,
        )
    tier = get_tier(binding.authority_tier_id)
    if tier and not tier_allows_action(tier, action_class):
        return CheckResult(
            allowed=False,
            reason=f"Trust tier '{binding.authority_tier_id}' does not allow action '{action_class}'.",
            required_approval=True,
            binding_scope=binding.scope_level,
        )
    return CheckResult(
        allowed=True,
        reason="Role has effective binding and action is permitted.",
        required_review=binding.review_required,
        required_approval=binding.review_required and not role.may_approve,
        binding_scope=binding.scope_level,
    )


def check_review_vs_approve(role_id: str, domain_id: str, repo_root: Path | str | None = None) -> dict:
    """Return whether role may review only or may approve in this domain."""
    role = get_role(role_id)
    if role is None:
        return {"may_review": False, "may_approve": False, "reason": "Unknown role."}
    return {
        "may_review": role.may_review,
        "may_approve": role.may_approve,
        "reason": "Review only" if role.may_review and not role.may_approve else ("May approve" if role.may_approve else "No review/approve"),
    }
