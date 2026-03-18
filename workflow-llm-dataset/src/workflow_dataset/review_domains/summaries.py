"""
M48H.1: Clearer summaries of which approvals require separation of duties and why.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.review_domains.registry import get_domain, list_domains
from workflow_dataset.review_domains.policies import get_domain_policy, list_domain_policies


def separation_of_duties_summary(domain_id: str, repo_root: Any = None) -> dict[str, Any]:
    """
    Summary for one domain: does it require separation of duties, why, and what that means.
    """
    domain = get_domain(domain_id, repo_root)
    policy = get_domain_policy(domain_id, repo_root)
    out: dict[str, Any] = {
        "domain_id": domain_id,
        "domain_name": domain.name if domain else "",
        "requires_separation_of_duties": False,
        "initiator_cannot_approve": False,
        "min_distinct_approvers": 1,
        "why_required": "",
        "policy_rationale": "",
        "approver_roles": [],
    }
    if domain:
        out["initiator_cannot_approve"] = domain.self_approve_blocked
        out["approver_roles"] = [r.role_id for r in domain.allowed_roles if "approve" in r.capabilities]
        if domain.multi_review:
            out["min_distinct_approvers"] = domain.multi_review.min_approvers
            if domain.multi_review.distinct_roles_required:
                out["requires_separation_of_duties"] = True
        if domain.self_approve_blocked:
            out["requires_separation_of_duties"] = True
        out["why_required"] = _why_separation_required(domain)
    if policy:
        out["requires_separation_of_duties"] = policy.separation_of_duties_required or out["requires_separation_of_duties"]
        out["initiator_cannot_approve"] = policy.initiator_cannot_approve or out["initiator_cannot_approve"]
        out["min_distinct_approvers"] = max(out["min_distinct_approvers"], policy.min_distinct_approvers)
        out["policy_rationale"] = policy.policy_rationale or out["policy_rationale"]
        if policy.policy_rationale and not out["why_required"]:
            out["why_required"] = policy.policy_rationale
    return out


def _why_separation_required(domain: Any) -> str:
    """One-line explanation from domain rules."""
    parts: list[str] = []
    if domain.self_approve_blocked:
        parts.append("Initiator cannot self-approve; a distinct approver is required.")
    if domain.multi_review and domain.multi_review.distinct_roles_required:
        parts.append("Approvers must be from distinct roles.")
    if domain.multi_review and domain.multi_review.description:
        parts.append(domain.multi_review.description)
    return " ".join(parts) if parts else ""


def separation_of_duties_summary_all(repo_root: Any = None) -> list[dict[str, Any]]:
    """Summaries for all domains that have policies or require separation of duties."""
    result: list[dict[str, Any]] = []
    policies = list_domain_policies(repo_root)
    domain_ids_with_policy = {p.domain_id for p in policies}
    for domain in list_domains(repo_root):
        if domain.self_approve_blocked or domain.domain_id in domain_ids_with_policy:
            result.append(separation_of_duties_summary(domain.domain_id, repo_root))
    return result


def format_separation_summary_text(summary: dict[str, Any]) -> str:
    """Human-readable block for one domain's separation summary."""
    lines = [
        f"Domain: {summary.get('domain_id', '')} — {summary.get('domain_name', '')}",
        f"  Requires separation of duties: {summary.get('requires_separation_of_duties', False)}",
        f"  Initiator cannot approve: {summary.get('initiator_cannot_approve', False)}",
        f"  Min distinct approvers: {summary.get('min_distinct_approvers', 1)}",
        f"  Approver roles: {', '.join(summary.get('approver_roles', []))}",
    ]
    if summary.get("why_required"):
        lines.append(f"  Why: {summary['why_required']}")
    if summary.get("policy_rationale"):
        lines.append(f"  Policy rationale: {summary['policy_rationale']}")
    return "\n".join(lines)
