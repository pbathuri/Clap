"""
M35A–M35D: Explain why a routine/action is allowed or blocked (authority tier + contract).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.trust.contracts import get_contracts_for_routine, TrustedRoutineContract
from workflow_dataset.trust.tiers import get_tier, tier_allows_action
from workflow_dataset.trust.scope import effective_contract, merge_contract_with_tier


def explain_why_allowed(
    routine_id: str,
    action_class: str,
    context: dict[str, Any] | None = None,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Explain why this action is allowed for this routine.
    Returns: allowed=True, tier_id, contract_id, explanation lines, effective permitted/excluded.
    """
    root = Path(repo_root).resolve() if repo_root else None
    context = context or {}
    contract = effective_contract(routine_id, context, root)
    tier = get_tier(contract.authority_tier_id) if contract else None
    if not tier:
        return {
            "allowed": False,
            "routine_id": routine_id,
            "action_class": action_class,
            "explanation": ["No effective contract or tier for this routine; default is blocked."],
            "tier_id": "",
            "contract_id": "",
        }
    merged = merge_contract_with_tier(contract, tier)
    permitted = merged.get("permitted_action_classes", [])
    excluded = merged.get("excluded_action_classes", [])
    if action_class in excluded:
        return explain_why_blocked(routine_id, action_class, context, repo_root)
    allowed = action_class in permitted or (not permitted and tier_allows_action(tier, action_class))
    lines: list[str] = []
    lines.append(f"Tier '{tier.tier_id}' allows action class '{action_class}'.")
    if contract:
        lines.append(f"Contract '{contract.contract_id}' applies (scope={contract.scope}).")
    if permitted and action_class in permitted:
        lines.append("Action is in permitted list.")
    return {
        "allowed": allowed,
        "routine_id": routine_id,
        "action_class": action_class,
        "tier_id": tier.tier_id,
        "contract_id": contract.contract_id if contract else "",
        "explanation": lines,
        "effective_permitted": permitted,
        "effective_excluded": excluded,
    }


def explain_why_blocked(
    routine_id: str,
    action_class: str,
    context: dict[str, Any] | None = None,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Explain why this action is blocked for this routine.
    Returns: allowed=False, reason, tier_id, contract_id, explanation lines.
    """
    root = Path(repo_root).resolve() if repo_root else None
    context = context or {}
    contract = effective_contract(routine_id, context, root)
    tier = get_tier(contract.authority_tier_id) if contract else get_tier("sandbox_write")
    lines: list[str] = []
    if not contract and not get_contracts_for_routine(routine_id, root):
        return {
            "allowed": False,
            "routine_id": routine_id,
            "action_class": action_class,
            "reason": "no_contract",
            "explanation": ["No trusted routine contract found for this routine; actions are blocked by default."],
            "tier_id": "",
            "contract_id": "",
        }
    if not tier:
        return {
            "allowed": False,
            "routine_id": routine_id,
            "action_class": action_class,
            "reason": "unknown_tier",
            "explanation": [f"Contract references unknown tier: {contract.authority_tier_id}"],
            "tier_id": contract.authority_tier_id if contract else "",
            "contract_id": contract.contract_id if contract else "",
        }
    merged = merge_contract_with_tier(contract, tier)
    excluded = merged.get("excluded_action_classes", [])
    if action_class in excluded:
        lines.append(f"Action class '{action_class}' is in excluded list (tier or contract).")
    elif not tier_allows_action(tier, action_class):
        lines.append(f"Tier '{tier.tier_id}' does not allow action class '{action_class}'.")
    if contract and contract.excluded_action_classes and action_class in contract.excluded_action_classes:
        lines.append(f"Contract '{contract.contract_id}' explicitly excludes this action.")
    return {
        "allowed": False,
        "routine_id": routine_id,
        "action_class": action_class,
        "reason": "forbidden_by_tier_or_contract",
        "explanation": lines or ["Action is not permitted by effective tier or contract."],
        "tier_id": tier.tier_id,
        "contract_id": contract.contract_id if contract else "",
    }


def explain_routine(routine_id: str, context: dict[str, Any] | None = None, repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Full explanation for a routine: effective contract, tier, permitted/excluded, required approvals/gates.
    """
    root = Path(repo_root).resolve() if repo_root else None
    context = context or {}
    contract = effective_contract(routine_id, context, root)
    tier = get_tier(contract.authority_tier_id) if contract else None
    merged = merge_contract_with_tier(contract, tier) if tier else {}
    return {
        "routine_id": routine_id,
        "contract_id": contract.contract_id if contract else "",
        "contract_label": contract.label if contract else "",
        "authority_tier_id": contract.authority_tier_id if contract else "",
        "tier_name": tier.name if tier else "",
        "permitted_action_classes": merged.get("permitted_action_classes", []),
        "excluded_action_classes": merged.get("excluded_action_classes", []),
        "required_approvals": merged.get("required_approvals", []),
        "required_review_gates": merged.get("required_review_gates", []),
        "audit_required": merged.get("audit_required", False),
        "blocked": not contract or not tier,
        "explanation": "No contract or tier" if not contract or not tier else f"Governed by contract {contract.contract_id} and tier {tier.tier_id}",
    }
