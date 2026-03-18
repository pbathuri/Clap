"""
M48I–M48L: Takeover / suspend / reauthorize flows; explain why delegation allowed, paused, or revoked.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.governed_operator.models import (
    DelegatedScope,
    DelegationExplanation,
    GovernedOperatorStatus,
)
from workflow_dataset.governed_operator.guidance import suspension_revocation_guidance
from workflow_dataset.governed_operator.store import (
    get_scope,
    load_governed_state,
    save_governed_state,
    save_scope,
)


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def suspend_delegated_loop(
    scope_id: str,
    reason: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Suspend a delegated scope (add to suspended_scope_ids). Returns state slice and message."""
    root = _root(repo_root)
    scope = get_scope(scope_id, repo_root=root)
    if not scope:
        return {"ok": False, "message": f"Scope {scope_id} not found.", "suspended_scope_ids": []}
    state = load_governed_state(repo_root=root)
    suspended = list(state.get("suspended_scope_ids", []))
    if scope_id not in suspended:
        suspended.append(scope_id)
    state["suspended_scope_ids"] = suspended
    state["updated_utc"] = utc_now_iso()
    save_governed_state(state, repo_root=root)
    return {"ok": True, "message": f"Scope {scope_id} suspended." + (f" Reason: {reason}" if reason else ""), "suspended_scope_ids": suspended}


def revoke_delegated_scope(
    scope_id: str,
    reason: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Revoke a delegated scope (add to revoked_scope_ids, remove from suspended). Returns state slice and message."""
    root = _root(repo_root)
    scope = get_scope(scope_id, repo_root=root)
    if not scope:
        return {"ok": False, "message": f"Scope {scope_id} not found.", "revoked_scope_ids": []}
    state = load_governed_state(repo_root=root)
    revoked = list(state.get("revoked_scope_ids", []))
    if scope_id not in revoked:
        revoked.append(scope_id)
    suspended = [s for s in state.get("suspended_scope_ids", []) if s != scope_id]
    state["revoked_scope_ids"] = revoked
    state["suspended_scope_ids"] = suspended
    state["updated_utc"] = utc_now_iso()
    save_governed_state(state, repo_root=root)
    return {"ok": True, "message": f"Scope {scope_id} revoked." + (f" Reason: {reason}" if reason else ""), "revoked_scope_ids": revoked}


def require_reauthorization(
    scope_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Mark scope as needing reauthorization (add to reauthorization_needed_scope_ids)."""
    root = _root(repo_root)
    scope = get_scope(scope_id, repo_root=root)
    if not scope:
        return {"ok": False, "message": f"Scope {scope_id} not found."}
    state = load_governed_state(repo_root=root)
    reauth = list(state.get("reauthorization_needed_scope_ids", []))
    if scope_id not in reauth:
        reauth.append(scope_id)
    state["reauthorization_needed_scope_ids"] = reauth
    state["updated_utc"] = utc_now_iso()
    save_governed_state(state, repo_root=root)
    return {"ok": True, "message": f"Scope {scope_id} marked reauthorization needed."}


def narrow_operator_scope(
    scope_id: str,
    new_routine_ids: list[str] | None = None,
    new_allowed_action_classes: list[str] | None = None,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Narrow a scope's routine set or allowed actions (explicit; no silent expansion)."""
    root = _root(repo_root)
    scope = get_scope(scope_id, repo_root=root)
    if not scope:
        return {"ok": False, "message": f"Scope {scope_id} not found."}
    if new_routine_ids is not None:
        scope.routine_ids = list(new_routine_ids)
    if new_allowed_action_classes is not None:
        scope.allowed_action_classes = list(new_allowed_action_classes)
    scope.updated_utc = utc_now_iso()
    save_scope(scope, repo_root=root)
    return {"ok": True, "message": f"Scope {scope_id} narrowed.", "scope_id": scope_id}


def explain_delegation(
    scope_id: str,
    role_id: str | None = None,
    routine_id: str | None = None,
    repo_root: Path | str | None = None,
) -> DelegationExplanation:
    """Explain why delegation is allowed, paused, or revoked for this scope."""
    root = _root(repo_root)
    now = utc_now_iso()
    scope = get_scope(scope_id, repo_root=root)
    if not scope:
        return DelegationExplanation(
            scope_id=scope_id,
            status="unknown",
            allowed=False,
            reason="scope_not_found",
            detail=f"Scope {scope_id} not found.",
            recommendation="List scopes: workflow-dataset governed-operator scopes.",
            generated_at_utc=now,
        )
    state = load_governed_state(repo_root=root)
    revoked = state.get("revoked_scope_ids", [])
    suspended = state.get("suspended_scope_ids", [])
    reauth_needed = state.get("reauthorization_needed_scope_ids", [])

    if scope_id in revoked:
        guidance = suspension_revocation_guidance(scope_id, repo_root=root)
        return DelegationExplanation(
            scope_id=scope_id,
            status=GovernedOperatorStatus.REVOKED.value,
            allowed=False,
            reason="scope_revoked",
            detail="This delegated scope has been revoked. Operator-mode actions under this scope are not allowed.",
            recommendation="To use this scope again, create a new scope (governed-operator scopes --create <new_id> ...). See guidance for next steps.",
            generated_at_utc=now,
            suggested_playbook_id=guidance.suggested_playbook_id,
            guidance_summary=guidance.what_happens,
        )
    if scope_id in suspended:
        guidance = suspension_revocation_guidance(scope_id, repo_root=root)
        return DelegationExplanation(
            scope_id=scope_id,
            status=GovernedOperatorStatus.SUSPENDED.value,
            allowed=False,
            reason="scope_suspended",
            detail="This delegated scope is suspended. Continuation requires reauthorization.",
            recommendation="Run: workflow-dataset governed-operator suspend --clear --id " + scope_id + " to resume, or revoke and re-create scope. See guidance for next steps.",
            generated_at_utc=now,
            suggested_playbook_id=guidance.suggested_playbook_id,
            guidance_summary=guidance.what_happens,
        )
    if scope_id in reauth_needed:
        guidance = suspension_revocation_guidance(scope_id, repo_root=root)
        return DelegationExplanation(
            scope_id=scope_id,
            status=GovernedOperatorStatus.REAUTHORIZATION_NEEDED.value,
            allowed=False,
            reason="reauthorization_needed",
            detail="This scope has been marked as requiring reauthorization before use.",
            recommendation="Complete reauthorization for this scope, then clear the reauthorization-needed flag. See guidance for next steps.",
            generated_at_utc=now,
            suggested_playbook_id=guidance.suggested_playbook_id,
            guidance_summary=guidance.what_happens,
        )

    if role_id:
        from workflow_dataset.governed_operator.controls import role_safe_delegation
        role_ok = role_safe_delegation(scope_id, role_id, repo_root=root)
        if not role_ok.get("allowed"):
            return DelegationExplanation(
                scope_id=scope_id,
                status=scope.status,
                allowed=False,
                reason=role_ok.get("reason", "role_not_safe"),
                detail=role_ok.get("detail", ""),
                recommendation="Use a role that is allowed in this scope's review domain.",
                generated_at_utc=now,
            )
    if routine_id and scope.routine_ids and routine_id not in scope.routine_ids:
        return DelegationExplanation(
            scope_id=scope_id,
            status=scope.status,
            allowed=False,
            reason="routine_not_in_scope",
            detail=f"Routine {routine_id} is not in this scope's routine list.",
            recommendation="Add the routine to the scope or use a scope that includes it.",
            generated_at_utc=now,
        )

    return DelegationExplanation(
        scope_id=scope_id,
        status=GovernedOperatorStatus.ACTIVE.value,
        allowed=True,
        reason="governed_scope_active",
        detail=f"Scope {scope_id} is active; role and domain checks passed.",
        recommendation="Delegation is allowed within this scope's boundaries.",
        generated_at_utc=now,
    )


def clear_suspension(
    scope_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Clear suspension for a scope (remove from suspended_scope_ids)."""
    root = _root(repo_root)
    state = load_governed_state(repo_root=root)
    suspended = [s for s in state.get("suspended_scope_ids", []) if s != scope_id]
    state["suspended_scope_ids"] = suspended
    state["updated_utc"] = utc_now_iso()
    save_governed_state(state, repo_root=root)
    return {"ok": True, "message": f"Suspension cleared for scope {scope_id}.", "suspended_scope_ids": suspended}
