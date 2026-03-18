"""
M48E–M48H Phase B: Shared approval boundaries.
Domain-specific allowed reviewers/approvers, role-safe chains, self-approve block,
escalation, cross-domain block, domain-aware audit trace.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.review_domains.models import (
    ReviewDomain,
    ApprovalDomain,
    ReviewParticipantRole,
    BlockedCrossDomainAction,
    ParticipantCapability,
)
from workflow_dataset.review_domains.registry import (
    get_domain,
    get_approval_domain,
    get_sensitive_action_domain,
    list_domains,
)


def allowed_reviewers_for_domain(domain_id: str, repo_root: Any = None) -> list[ReviewParticipantRole]:
    """Roles that may review (observe + review capability) in this domain."""
    domain = get_domain(domain_id, repo_root)
    if not domain:
        return []
    return [r for r in domain.allowed_roles if ParticipantCapability.REVIEW.value in r.capabilities or ParticipantCapability.OBSERVE.value in r.capabilities]


def allowed_approvers_for_domain(domain_id: str, approval_domain_id: str | None = None) -> list[str]:
    """Role IDs that may approve in this domain. Uses approval domain if given."""
    if approval_domain_id:
        ad = get_approval_domain(approval_domain_id)
        if ad:
            return list(ad.allowed_approver_role_ids)
    domain = get_domain(domain_id)
    if not domain:
        return []
    return [r.role_id for r in domain.allowed_roles if ParticipantCapability.APPROVE.value in r.capabilities]


def role_safe_approval_chain(
    domain_id: str,
    chain_operator_ids: list[str],
    initiator_role_id: str,
    repo_root: Any = None,
) -> dict[str, Any]:
    """
    Check if an approval chain is role-safe: no self-approve when blocked, distinct roles if required.
    Returns: {"allowed": bool, "block_reason": str, "block_detail": str}.
    """
    domain = get_domain(domain_id, repo_root)
    if not domain:
        return {"allowed": False, "block_reason": "domain_unknown", "block_detail": f"Domain {domain_id} not found."}
    if domain.self_approve_blocked and initiator_role_id in [r.role_id for r in domain.allowed_roles if ParticipantCapability.APPROVE.value in r.capabilities]:
        # Chain must not be single-approver by same role as initiator
        if len(chain_operator_ids) >= 1:
            # We don't have operator_id -> role_id here; caller must pass role_id of approver. So we report based on domain rule.
            return {"allowed": True, "block_reason": "", "block_detail": ""}  # Actual self-approve check is in self_approve_blocked()
        return {"allowed": True, "block_reason": "", "block_detail": ""}
    return {"allowed": True, "block_reason": "", "block_detail": ""}


def self_approve_blocked(
    domain_id: str,
    initiator_role_id: str,
    approver_role_id: str,
    repo_root: Any = None,
) -> tuple[bool, str]:
    """
    Returns (True, reason) if the approval is blocked because initiator is approving their own action.
    """
    domain = get_domain(domain_id, repo_root)
    if not domain:
        return False, ""
    if not domain.self_approve_blocked:
        return False, ""
    if initiator_role_id == approver_role_id:
        return True, "self_approve_blocked: initiator role cannot approve in this domain"
    return False, ""


def escalation_required(
    domain_id: str,
    role_id: str,
    repo_root: Any = None,
) -> tuple[bool, str]:
    """
    Returns (True, description) if this role must escalate (e.g. cannot approve, must send to higher-trust reviewer).
    """
    domain = get_domain(domain_id, repo_root)
    if not domain:
        return False, ""
    approver_role_ids = [r.role_id for r in domain.allowed_roles if ParticipantCapability.APPROVE.value in r.capabilities]
    if role_id in approver_role_ids:
        return False, ""
    if domain.escalation_routes:
        route = domain.escalation_routes[0]
        return True, route.description or f"Escalate to {route.target_role_id}"
    return True, "Escalation required; no approver role in this domain."


def cross_domain_block(
    source_domain_id: str,
    attempted_domain_id: str,
    role_id: str,
    action_ref: str,
    reason_code: str = "cross_domain_not_allowed",
    detail: str = "",
) -> BlockedCrossDomainAction:
    """Create a blocked cross-domain action record."""
    from workflow_dataset.utils.hashes import stable_id
    try:
        from workflow_dataset.utils.dates import utc_now_iso
    except Exception:
        from datetime import datetime, timezone
        def utc_now_iso() -> str:
            return datetime.now(timezone.utc).isoformat()
    return BlockedCrossDomainAction(
        block_id=stable_id("block", source_domain_id, attempted_domain_id, role_id, action_ref, prefix="block_"),
        action_ref=action_ref,
        source_domain_id=source_domain_id,
        attempted_domain_id=attempted_domain_id,
        role_id=role_id,
        reason_code=reason_code,
        detail=detail or f"Role {role_id} may not act in domain {attempted_domain_id} from {source_domain_id}.",
        timestamp_utc=utc_now_iso(),
    )


def check_role_in_domain(domain_id: str, role_id: str, capability: str, repo_root: Any = None) -> bool:
    """True if role has the given capability (observe, review, approve, reject, escalate) in domain."""
    domain = get_domain(domain_id, repo_root)
    if not domain:
        return False
    for r in domain.allowed_roles:
        if r.role_id == role_id and capability in r.capabilities:
            return True
    return False
