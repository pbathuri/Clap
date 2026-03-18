"""
M35A–M35D: Trust contract scope and inheritance — precedence, conflict rules, effective contract.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.trust.contracts import (
    TrustedRoutineContract,
    load_contracts,
    get_contracts_for_routine,
)
from workflow_dataset.trust.tiers import get_tier, AuthorityTier, tier_allows_action


# Scope order: more specific wins (higher index = more specific)
SCOPE_ORDER = ["global", "project", "pack", "workflow", "recurring_routine", "worker_lane"]


def _scope_rank(scope: str) -> int:
    if not scope:
        return -1
    base = scope.split(":")[0] if ":" in scope else scope
    try:
        return SCOPE_ORDER.index(base)
    except ValueError:
        return 0


def effective_contract(
    routine_id: str,
    context: dict[str, Any] | None = None,
    repo_root: Path | str | None = None,
) -> TrustedRoutineContract | None:
    """
    Return the effective contract for this routine: highest-precedence matching contract.
    context may include: project_id, pack_id, workflow_id, scope_hint.
    """
    candidates = get_contracts_for_routine(routine_id, repo_root)
    if not candidates:
        return None
    context = context or {}
    project_id = context.get("project_id", "")
    pack_id = context.get("pack_id", "")
    workflow_id = context.get("workflow_id", "")

    best: TrustedRoutineContract | None = None
    best_rank = -1
    for c in candidates:
        scope_base = c.scope.split(":")[0] if ":" in c.scope else c.scope
        if scope_base == "global":
            rank = _scope_rank("global")
        elif scope_base == "project" and c.scope_id == project_id:
            rank = _scope_rank("project")
        elif scope_base == "pack" and c.scope_id == pack_id:
            rank = _scope_rank("pack")
        elif scope_base == "workflow" and (c.scope_id == workflow_id or not c.scope_id):
            rank = _scope_rank("workflow")
        elif scope_base == "recurring_routine":
            rank = _scope_rank("recurring_routine")
        elif scope_base == "worker_lane":
            rank = _scope_rank("worker_lane")
        else:
            if scope_base == "global":
                rank = 0
            else:
                continue
        if rank > best_rank:
            best_rank = rank
            best = c
    return best


def merge_contract_with_tier(
    contract: TrustedRoutineContract | None,
    tier: AuthorityTier | None,
) -> dict[str, Any]:
    """
    Merge contract and tier into effective permitted/excluded and requirements.
    Conflict rule: excluded always wins; required_approvals union; tier limits cap contract.
    """
    out: dict[str, Any] = {
        "permitted_action_classes": [],
        "excluded_action_classes": [],
        "required_approvals": [],
        "required_review_gates": [],
        "audit_required": False,
        "authority_tier_id": "",
    }
    if tier:
        out["authority_tier_id"] = tier.tier_id
        out["permitted_action_classes"] = list(tier.allowed_action_classes)
        out["excluded_action_classes"] = list(tier.forbidden_action_classes)
        out["audit_required"] = tier.audit_required
    if contract:
        out["required_approvals"] = list(set(out.get("required_approvals", []) + contract.required_approvals))
        out["required_review_gates"] = list(set(out.get("required_review_gates", []) + contract.required_review_gates))
        out["excluded_action_classes"] = list(set(out.get("excluded_action_classes", []) + contract.excluded_action_classes))
        if contract.permitted_action_classes:
            permitted = [a for a in contract.permitted_action_classes if a not in out["excluded_action_classes"]]
            if permitted:
                out["permitted_action_classes"] = [a for a in out["permitted_action_classes"] if a in permitted] or permitted
        out["audit_required"] = out["audit_required"] or contract.audit_required
    return out
