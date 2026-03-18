"""
M48I–M48L: Mission control slice — active/suspended delegations, highest-risk scope, reauthorization needed, next action.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.governed_operator.store import (
    list_scope_ids,
    get_scope,
    load_governed_state,
)
from workflow_dataset.governed_operator.models import GovernedOperatorStatus


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def governed_operator_slice(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Build mission-control slice: active governed delegations, suspended, revoked, highest-risk scope, reauthorization needed, next action."""
    root = _root(repo_root)
    try:
        state = load_governed_state(repo_root=root)
        scope_ids = list_scope_ids(repo_root=root)
        revoked = set(state.get("revoked_scope_ids", []))
        suspended = set(state.get("suspended_scope_ids", []))
        reauth_needed = state.get("reauthorization_needed_scope_ids", [])

        active = [s for s in scope_ids if s not in revoked and s not in suspended]
        suspended_list = [s for s in scope_ids if s in suspended]

        highest_risk_scope_id = ""
        highest_risk_label = ""
        for sid in active:
            sc = get_scope(sid, repo_root=root)
            if not sc:
                continue
            if sc.authority_tier_id in ("commit_or_send_candidate", "bounded_trusted_real") or not highest_risk_scope_id:
                highest_risk_scope_id = sid
                highest_risk_label = sc.label or sid
                if sc.authority_tier_id == "commit_or_send_candidate":
                    break

        if reauth_needed:
            next_action = "workflow-dataset governed-operator scopes (reauthorization needed)"
        elif suspended_list:
            next_action = "workflow-dataset governed-operator suspend --clear --id " + (suspended_list[0] if suspended_list else "")
        elif active:
            next_action = "workflow-dataset governed-operator check --role operator --routine <routine_id>"
        else:
            next_action = "workflow-dataset governed-operator scopes (create a scope)"

        return {
            "active_governed_delegation_scope_ids": active,
            "suspended_delegation_scope_ids": suspended_list,
            "revoked_scope_ids": list(revoked),
            "reauthorization_needed_scope_ids": list(reauth_needed),
            "highest_risk_active_scope_id": highest_risk_scope_id,
            "highest_risk_active_scope_label": highest_risk_label,
            "next_governance_action": next_action,
            "scope_count": len(scope_ids),
        }
    except Exception as e:
        return {"error": str(e)}
