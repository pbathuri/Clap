"""
M48I–M48L: Delegation safety controls.
Role-safe and domain-bound delegation; action restrictions; supervised continuation; suspend/revoke triggers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.governed_operator.models import (
    DelegatedScope,
    DelegatedActionBoundary,
    GovernedOperatorStatus,
)
from workflow_dataset.governed_operator.store import (
    get_scope,
    load_governed_state,
    list_scope_ids,
)


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def role_safe_delegation(
    scope_id: str,
    role_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Check if delegation for this scope is role-safe (role is allowed in the scope's review domain).
    Returns: {"allowed": bool, "reason": str, "detail": str}.
    """
    root = _repo_root(repo_root)
    scope = get_scope(scope_id, repo_root=root)
    if not scope:
        return {"allowed": False, "reason": "scope_not_found", "detail": f"Scope {scope_id} not found."}
    try:
        from workflow_dataset.review_domains.registry import get_domain
        from workflow_dataset.review_domains.models import ParticipantCapability
        domain = get_domain(scope.review_domain_id, repo_root=root)
        if not domain:
            return {"allowed": False, "reason": "domain_not_found", "detail": f"Review domain {scope.review_domain_id} not found."}
        role_ids_in_domain = [r.role_id for r in domain.allowed_roles]
        if role_id not in role_ids_in_domain:
            return {"allowed": False, "reason": "role_not_in_domain", "detail": f"Role {role_id} is not in domain {scope.review_domain_id}."}
        return {"allowed": True, "reason": "", "detail": ""}
    except Exception as e:
        return {"allowed": False, "reason": "check_error", "detail": str(e)}


def domain_bound_delegation(
    scope_id: str,
    review_domain_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Check if delegation is within the allowed review domain (scope's domain matches).
    Returns: {"allowed": bool, "reason": str, "detail": str}.
    """
    root = _repo_root(repo_root)
    scope = get_scope(scope_id, repo_root=root)
    if not scope:
        return {"allowed": False, "reason": "scope_not_found", "detail": f"Scope {scope_id} not found."}
    if scope.review_domain_id != review_domain_id:
        return {"allowed": False, "reason": "domain_mismatch", "detail": f"Scope domain {scope.review_domain_id} != {review_domain_id}."}
    return {"allowed": True, "reason": "", "detail": ""}


def action_restrictions_by_role_scope(
    scope_id: str,
    role_id: str,
    action_class: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Check if an action class is allowed for this role/scope (scope's allowed/forbidden + tier).
    Returns: {"allowed": bool, "reason": str, "detail": str}.
    """
    root = _repo_root(repo_root)
    scope = get_scope(scope_id, repo_root=root)
    if not scope:
        return {"allowed": False, "reason": "scope_not_found", "detail": f"Scope {scope_id} not found."}
    role_ok = role_safe_delegation(scope_id, role_id, repo_root=root)
    if not role_ok.get("allowed"):
        return role_ok
    if scope.forbidden_action_classes and action_class in scope.forbidden_action_classes:
        return {"allowed": False, "reason": "action_forbidden", "detail": f"Action {action_class} is forbidden in scope {scope_id}."}
    if scope.allowed_action_classes and action_class not in scope.allowed_action_classes:
        return {"allowed": False, "reason": "action_not_in_scope", "detail": f"Action {action_class} not in scope allowed list."}
    try:
        from workflow_dataset.trust.tiers import get_tier, tier_allows_action
        tier = get_tier(scope.authority_tier_id) if scope.authority_tier_id else None
        if tier and not tier_allows_action(tier, action_class):
            return {"allowed": False, "reason": "tier_forbids", "detail": f"Authority tier {scope.authority_tier_id} does not allow {action_class}."}
    except Exception:
        pass
    return {"allowed": True, "reason": "", "detail": ""}


def supervised_continuation_allowed(
    scope_id: str,
    loop_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Check if supervised continuation is allowed for this scope/loop (from DelegationSafeLoop and state).
    Returns: {"allowed": bool, "reason": str, "detail": str, "requires_approval": bool}.
    """
    root = _repo_root(repo_root)
    scope = get_scope(scope_id, repo_root=root)
    if not scope:
        return {"allowed": False, "reason": "scope_not_found", "detail": f"Scope {scope_id} not found.", "requires_approval": True}
    state = load_governed_state(repo_root=root)
    if scope_id in state.get("revoked_scope_ids", []):
        return {"allowed": False, "reason": "scope_revoked", "detail": "Delegated scope has been revoked.", "requires_approval": True}
    if scope_id in state.get("suspended_scope_ids", []):
        from workflow_dataset.governed_operator.store import get_loop
        loop = get_loop(loop_id, repo_root=root) if loop_id else None
        if loop and loop.supervised_continuation_allowed:
            return {"allowed": True, "reason": "", "detail": "", "requires_approval": loop.continuation_requires_approval}
        return {"allowed": False, "reason": "scope_suspended", "detail": "Scope is suspended; reauthorization needed.", "requires_approval": True}
    return {"allowed": True, "reason": "", "detail": "", "requires_approval": False}


def suspend_on_policy_or_confidence(
    scope_id: str,
    reason: str = "",
    kind: str = "policy_breach",
    repo_root: Path | str | None = None,
) -> bool:
    """Record suspension of scope (policy or confidence boundary crossing). Returns True if state updated."""
    root = _repo_root(repo_root)
    scope = get_scope(scope_id, repo_root=root)
    if not scope:
        return False
    from workflow_dataset.utils.dates import utc_now_iso
    state = load_governed_state(repo_root=root)
    suspended = list(state.get("suspended_scope_ids", []))
    if scope_id not in suspended:
        suspended.append(scope_id)
    state["suspended_scope_ids"] = suspended
    state["updated_utc"] = utc_now_iso()
    from workflow_dataset.governed_operator.store import save_governed_state
    save_governed_state(state, repo_root=root)
    return True


def revoke_on_unsafe_or_conflict(
    scope_id: str,
    reason: str = "",
    kind: str = "unsafe_authority_state",
    repo_root: Path | str | None = None,
) -> bool:
    """Record revocation of scope (unsafe or conflicting authority). Returns True if state updated."""
    root = _repo_root(repo_root)
    scope = get_scope(scope_id, repo_root=root)
    if not scope:
        return False
    from workflow_dataset.utils.dates import utc_now_iso
    state = load_governed_state(repo_root=root)
    revoked = list(state.get("revoked_scope_ids", []))
    if scope_id not in revoked:
        revoked.append(scope_id)
    suspended = [s for s in state.get("suspended_scope_ids", []) if s != scope_id]
    state["revoked_scope_ids"] = revoked
    state["suspended_scope_ids"] = suspended
    state["updated_utc"] = utc_now_iso()
    from workflow_dataset.governed_operator.store import save_governed_state
    save_governed_state(state, repo_root=root)
    return True


def check_delegation(
    role_id: str,
    routine_id: str,
    scope_id: str | None = None,
    review_domain_id: str | None = None,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Unified check: can this role run this routine in this scope (or domain)?
    If scope_id given, use it; else resolve by routine and domain.
    Returns: {"allowed": bool, "reason": str, "detail": str, "scope_id": str, "recommendation": str}.
    """
    root = _repo_root(repo_root)
    if scope_id:
        scope = get_scope(scope_id, repo_root=root)
        if not scope:
            return {"allowed": False, "reason": "scope_not_found", "detail": f"Scope {scope_id} not found.", "scope_id": scope_id, "recommendation": "Create scope or use valid scope_id."}
    else:
        scope_ids = [s for s in list_scope_ids(repo_root=root) if get_scope(s, repo_root=root) and (get_scope(s, repo_root=root).review_domain_id == review_domain_id or not review_domain_id)]
        if not scope_ids:
            return {"allowed": False, "reason": "no_scope", "detail": "No governed scope for this domain/routine.", "scope_id": "", "recommendation": "workflow-dataset governed-operator scopes to create a scope."}
        scope = get_scope(scope_ids[0], repo_root=root)
        scope_id = scope.scope_id if scope else ""

    if not scope:
        return {"allowed": False, "reason": "no_scope", "detail": "", "scope_id": "", "recommendation": ""}

    state = load_governed_state(repo_root=root)
    if scope.scope_id in state.get("revoked_scope_ids", []):
        return {"allowed": False, "reason": "scope_revoked", "detail": "Delegated scope has been revoked.", "scope_id": scope.scope_id, "recommendation": "Re-delegate with a new scope if appropriate."}
    if scope.scope_id in state.get("suspended_scope_ids", []):
        return {"allowed": False, "reason": "scope_suspended", "detail": "Scope is suspended; reauthorization needed.", "scope_id": scope.scope_id, "recommendation": "governed-operator suspend --clear <scope_id> or revoke then re-create."}

    role_ok = role_safe_delegation(scope.scope_id, role_id, repo_root=root)
    if not role_ok.get("allowed"):
        return {"allowed": False, "reason": role_ok.get("reason", ""), "detail": role_ok.get("detail", ""), "scope_id": scope.scope_id, "recommendation": "Use a role allowed in this scope's review domain."}

    if review_domain_id and scope.review_domain_id != review_domain_id:
        return {"allowed": False, "reason": "domain_mismatch", "detail": f"Scope domain {scope.review_domain_id} != {review_domain_id}.", "scope_id": scope.scope_id, "recommendation": "Use a scope for the intended review domain."}

    if scope.routine_ids and routine_id and routine_id not in scope.routine_ids:
        return {"allowed": False, "reason": "routine_not_in_scope", "detail": f"Routine {routine_id} not in scope.", "scope_id": scope.scope_id, "recommendation": "Add routine to scope or use a scope that includes this routine."}

    return {"allowed": True, "reason": "", "detail": "", "scope_id": scope.scope_id, "recommendation": ""}
