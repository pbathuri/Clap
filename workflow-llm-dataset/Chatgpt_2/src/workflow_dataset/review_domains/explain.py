"""
M48E–M48H Phase C: Review/approval explanation.
Who may review, who may approve, why chain blocked, why escalation required, why comment-only.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.review_domains.registry import get_domain, get_approval_domain
from workflow_dataset.review_domains.boundaries import (
    allowed_reviewers_for_domain,
    allowed_approvers_for_domain,
    self_approve_blocked,
    escalation_required,
    check_role_in_domain,
)
from workflow_dataset.review_domains.models import ParticipantCapability


def who_may_review(domain_id: str, repo_root: Any = None) -> list[dict[str, Any]]:
    """Return list of roles that may review (observe + review) in this domain."""
    roles = allowed_reviewers_for_domain(domain_id, repo_root)
    return [{"role_id": r.role_id, "display_name": r.display_name, "description": r.description} for r in roles]


def who_may_approve(domain_id: str, approval_domain_id: str | None = None, repo_root: Any = None) -> list[str]:
    """Return role IDs that may approve in this domain."""
    return allowed_approvers_for_domain(domain_id, approval_domain_id)


def why_chain_blocked(
    domain_id: str,
    context: dict[str, Any],
    repo_root: Any = None,
) -> str:
    """
    Explain why an approval chain is blocked. context may include: initiator_role_id, approver_role_id, chain_operator_ids.
    """
    domain = get_domain(domain_id, repo_root)
    if not domain:
        return f"Domain {domain_id} not found."
    initiator = context.get("initiator_role_id", "")
    approver = context.get("approver_role_id", "")
    if initiator and approver:
        blocked, reason = self_approve_blocked(domain_id, initiator, approver, repo_root)
        if blocked:
            return reason
    if approver and not check_role_in_domain(domain_id, approver, ParticipantCapability.APPROVE.value, repo_root):
        return f"Role {approver} does not have approve capability in domain {domain_id}."
    return ""


def why_escalation_required(domain_id: str, role_id: str, repo_root: Any = None) -> str:
    """Explain why escalation is required for this role in this domain."""
    required, desc = escalation_required(domain_id, role_id, repo_root)
    if required:
        return desc
    return ""


def why_comment_only(domain_id: str, role_id: str, repo_root: Any = None) -> str:
    """Explain why this role may comment but not approve (e.g. reviewer vs approver)."""
    domain = get_domain(domain_id, repo_root)
    if not domain:
        return f"Domain {domain_id} not found."
    can_review = check_role_in_domain(domain_id, role_id, ParticipantCapability.REVIEW.value, repo_root)
    can_approve = check_role_in_domain(domain_id, role_id, ParticipantCapability.APPROVE.value, repo_root)
    if can_approve:
        return ""
    if can_review:
        approvers = who_may_approve(domain_id, repo_root=repo_root)
        return f"Role {role_id} may review and comment but not approve; approvers in this domain: {', '.join(approvers)}."
    return f"Role {role_id} has no review or approve capability in domain {domain_id}."
