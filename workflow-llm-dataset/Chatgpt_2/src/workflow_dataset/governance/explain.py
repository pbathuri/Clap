"""
M48C: Explain authority — why allowed or blocked for role/surface/action.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.governance.models import AuthorityExplanation
from workflow_dataset.governance.roles import get_role
from workflow_dataset.governance.bindings import get_effective_binding
from workflow_dataset.governance.check import can_role_perform_action


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def explain_authority(
    role_id: str,
    surface_id: str | None = None,
    action_class: str | None = None,
    scope_hint: str | None = None,
    repo_root: Path | str | None = None,
) -> AuthorityExplanation | None:
    """
    Explain authority for role: allowed/blocked surfaces and actions, required review/override, escalation.
    """
    root = _root(repo_root)
    role = get_role(role_id)
    if role is None:
        return AuthorityExplanation(
            role_id=role_id,
            summary=f"Unknown role: {role_id}.",
            scope_context=scope_hint or "product_wide",
        )
    binding = get_effective_binding(role_id, scope_hint, root)
    if binding is None:
        return AuthorityExplanation(
            role_id=role_id,
            summary="No effective binding for this role at scope.",
            scope_context=scope_hint or "product_wide",
        )
    allowed_surfaces = list(binding.effective_surface_ids)
    blocked_surfaces = list(role.forbidden_surface_ids)
    allowed_actions = list(binding.effective_action_classes)
    blocked_actions = list(role.forbidden_action_classes)
    if surface_id:
        check = can_role_perform_action(role_id, action_class or "observe", scope_hint, surface_id, root)
        if check.allowed:
            summary = f"Role '{role_id}' may access surface '{surface_id}' at scope {binding.scope_level}."
        else:
            summary = f"Role '{role_id}' is blocked from surface '{surface_id}': {check.reason}"
        required_review = "Review required before approval." if check.required_review else ""
        override_required = "Override or approval required." if check.required_approval else ""
        escalation_path = ""
        if check.escalation_path:
            escalation_path = f"Escalate to {check.escalation_path.to_role_id}: {check.escalation_path.description}"
        return AuthorityExplanation(
            role_id=role_id,
            summary=summary,
            allowed_surfaces=allowed_surfaces,
            blocked_surfaces=blocked_surfaces,
            allowed_actions=allowed_actions,
            blocked_actions=blocked_actions,
            required_review=required_review,
            override_required=override_required,
            escalation_path=escalation_path,
            scope_context=binding.scope_level + ("/" + binding.scope_id if binding.scope_id else ""),
        )
    if action_class:
        check = can_role_perform_action(role_id, action_class, scope_hint, None, root)
        if check.allowed:
            summary = f"Role '{role_id}' may perform '{action_class}' at scope {binding.scope_level}."
        else:
            summary = f"Role '{role_id}' cannot perform '{action_class}': {check.reason}"
        return AuthorityExplanation(
            role_id=role_id,
            summary=summary,
            allowed_surfaces=allowed_surfaces,
            blocked_surfaces=blocked_surfaces,
            allowed_actions=allowed_actions,
            blocked_actions=blocked_actions,
            required_review="Review required." if check.required_review else "",
            override_required="Approval/override required." if check.required_approval else "",
            escalation_path=check.escalation_path.description if check.escalation_path else "",
            scope_context=binding.scope_level + ("/" + binding.scope_id if binding.scope_id else ""),
        )
    summary = f"Role '{role_id}' at scope {binding.scope_level}: tier={binding.authority_tier_id}, trust_preset={binding.trust_preset_id}. May review={binding.review_required}, override_required={binding.override_required}."
    return AuthorityExplanation(
        role_id=role_id,
        summary=summary,
        allowed_surfaces=allowed_surfaces,
        blocked_surfaces=blocked_surfaces,
        allowed_actions=allowed_actions,
        blocked_actions=blocked_actions,
        required_review="Review required in this scope." if binding.review_required else "",
        override_required="Override required for some actions." if binding.override_required else "",
        escalation_path="Escalate to approver or maintainer if blocked.",
        scope_context=binding.scope_level + ("/" + binding.scope_id if binding.scope_id else ""),
    )
