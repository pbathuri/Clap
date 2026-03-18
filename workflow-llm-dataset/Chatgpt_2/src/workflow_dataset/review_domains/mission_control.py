"""
M48E–M48H Phase D: Mission control slice for review domains.
Active domains, domain-blocked approvals, required escalations, most sensitive pending, next recommended adjustment.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.review_domains.registry import list_domains, get_domain, get_sensitive_action_domain
from workflow_dataset.review_domains.boundaries import escalation_required


def review_domains_mission_control_slice(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Build mission-control slice: active review domains, domain-blocked approvals, required escalations, most sensitive pending, next recommended adjustment."""
    root = Path(repo_root).resolve() if repo_root else None
    domains = list_domains(root)
    active_domain_ids = [d.domain_id for d in domains]
    domain_blocked_approvals: list[dict[str, Any]] = []
    required_escalations: list[dict[str, Any]] = []
    most_sensitive_pending: str | None = None
    next_recommended_adjustment: str = ""

    # Domain-blocked: report from sensitive gates pending with domain context
    try:
        from workflow_dataset.sensitive_gates.store import load_gates
        gates = load_gates(repo_root=root)
        pending = [g for g in gates if g.status == "pending"]
    except Exception:
        pending = []
    for g in pending[:10]:
        sad = get_sensitive_action_domain(g.action_kind)
        if sad:
            domain_blocked_approvals.append({
                "gate_id": g.gate_id,
                "domain_id": sad.review_domain_id,
                "sensitivity": sad.sensitivity_label,
            })
    if domain_blocked_approvals and not most_sensitive_pending:
        high = [b for b in domain_blocked_approvals if b.get("sensitivity") == "high"]
        most_sensitive_pending = high[0].get("gate_id") if high else domain_blocked_approvals[0].get("gate_id")

    # Required escalations: roles that must escalate per domain (operator in sensitive_gate, etc.)
    for d in domains:
        for r in d.allowed_roles:
            req, desc = escalation_required(d.domain_id, r.role_id, repo_root=root)
            if req:
                required_escalations.append({
                    "domain_id": d.domain_id,
                    "role_id": r.role_id,
                    "reason": desc,
                })

    # Next recommended: if pending gates, suggest review-domains explain for sensitive_gate; else list
    if most_sensitive_pending:
        next_recommended_adjustment = f"workflow-dataset review-domains explain --id sensitive_gate"
    elif required_escalations:
        next_recommended_adjustment = "workflow-dataset review-domains list"
    else:
        next_recommended_adjustment = "workflow-dataset review-domains list"

    return {
        "active_review_domains": active_domain_ids,
        "active_review_domain_count": len(active_domain_ids),
        "domain_blocked_approvals": domain_blocked_approvals,
        "domain_blocked_approvals_count": len(domain_blocked_approvals),
        "required_escalations": required_escalations,
        "required_escalations_count": len(required_escalations),
        "most_sensitive_pending_review": most_sensitive_pending,
        "next_recommended_review_domain_adjustment": next_recommended_adjustment,
    }
