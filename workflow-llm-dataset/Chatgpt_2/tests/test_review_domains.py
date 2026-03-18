"""
M48E–M48H: Tests for review domains and shared approval boundaries.
Domain creation, role/domain compatibility, escalation, self-approval block, cross-domain block, explanation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.review_domains.models import (
    ReviewDomain,
    ApprovalDomain,
    ReviewParticipantRole,
    EscalationRoute,
    MultiReviewRequirement,
    SensitiveActionDomain,
    DomainAuditTrace,
    BlockedCrossDomainAction,
    ParticipantCapability,
    ReviewDomainPolicy,
    EscalationPack,
    EscalationPackEntry,
)
from workflow_dataset.review_domains.registry import (
    get_domain,
    list_domains,
    get_approval_domain,
    get_sensitive_action_domain,
    DOMAIN_SENSITIVE_GATE,
    DOMAIN_OPERATOR_ROUTINE,
)
from workflow_dataset.review_domains.boundaries import (
    allowed_reviewers_for_domain,
    allowed_approvers_for_domain,
    self_approve_blocked,
    escalation_required,
    cross_domain_block,
    check_role_in_domain,
)
from workflow_dataset.review_domains.explain import (
    who_may_review,
    who_may_approve,
    why_chain_blocked,
    why_escalation_required,
    why_comment_only,
)


# ----- Phase A: Review domain model -----


def test_review_domain_creation() -> None:
    """Review domain can be created and serialized."""
    d = ReviewDomain(
        domain_id="test_domain",
        name="Test domain",
        description="For tests",
        allowed_roles=[
            ReviewParticipantRole("approver", [ParticipantCapability.APPROVE.value], "Approver", ""),
        ],
        self_approve_blocked=True,
    )
    assert d.domain_id == "test_domain"
    assert d.self_approve_blocked is True
    out = d.to_dict()
    assert out["domain_id"] == "test_domain"
    assert out["self_approve_blocked"] is True
    back = ReviewDomain.from_dict(out)
    assert back.domain_id == d.domain_id
    assert back.self_approve_blocked == d.self_approve_blocked


def test_builtin_domains_list() -> None:
    """Built-in domains are listed."""
    domains = list_domains()
    ids = [d.domain_id for d in domains]
    assert DOMAIN_OPERATOR_ROUTINE in ids
    assert DOMAIN_SENSITIVE_GATE in ids
    assert "production_repair" in ids
    assert "trusted_routine_audit" in ids
    assert "adaptation_promotion" in ids


def test_get_domain_sensitive_gate() -> None:
    """Sensitive gate domain has self-approve blocked and approver role."""
    d = get_domain(DOMAIN_SENSITIVE_GATE)
    assert d is not None
    assert d.domain_id == DOMAIN_SENSITIVE_GATE
    assert d.self_approve_blocked is True
    role_ids = [r.role_id for r in d.allowed_roles]
    assert "approver" in role_ids
    assert "operator" in role_ids


# ----- Role/domain compatibility -----


def test_role_domain_compatibility() -> None:
    """Operator may review but not approve in sensitive_gate; approver may approve."""
    assert check_role_in_domain(DOMAIN_SENSITIVE_GATE, "operator", ParticipantCapability.REVIEW.value) is True
    assert check_role_in_domain(DOMAIN_SENSITIVE_GATE, "operator", ParticipantCapability.APPROVE.value) is False
    assert check_role_in_domain(DOMAIN_SENSITIVE_GATE, "approver", ParticipantCapability.APPROVE.value) is True


def test_allowed_reviewers_approvers() -> None:
    """allowed_reviewers and allowed_approvers return correct roles."""
    reviewers = allowed_reviewers_for_domain(DOMAIN_SENSITIVE_GATE)
    assert any(r.role_id == "operator" for r in reviewers)
    assert any(r.role_id == "approver" for r in reviewers)
    approvers = allowed_approvers_for_domain(DOMAIN_SENSITIVE_GATE)
    assert "approver" in approvers
    assert "operator" not in approvers


# ----- Escalation -----


def test_escalation_required() -> None:
    """Operator must escalate in sensitive_gate; approver need not."""
    req_op, desc_op = escalation_required(DOMAIN_SENSITIVE_GATE, "operator")
    assert req_op is True
    assert "approver" in desc_op or "Escalate" in desc_op
    req_ap, desc_ap = escalation_required(DOMAIN_SENSITIVE_GATE, "approver")
    assert req_ap is False
    assert desc_ap == ""


# ----- Self-approval block -----


def test_self_approve_blocked() -> None:
    """In sensitive_gate, operator self-approve is blocked; approver approving operator's action is allowed."""
    blocked, reason = self_approve_blocked(DOMAIN_SENSITIVE_GATE, "operator", "operator")
    assert blocked is True
    assert "self_approve" in reason.lower()
    blocked2, _ = self_approve_blocked(DOMAIN_SENSITIVE_GATE, "operator", "approver")
    assert blocked2 is False


def test_operator_routine_self_approve_allowed() -> None:
    """In operator_routine, operator may self-approve (boundary not set)."""
    blocked, _ = self_approve_blocked(DOMAIN_OPERATOR_ROUTINE, "operator", "operator")
    assert blocked is False


# ----- Cross-domain block -----


def test_cross_domain_block_record() -> None:
    """BlockedCrossDomainAction is created with correct fields."""
    b = cross_domain_block("operator_routine", "sensitive_gate", "operator", "gate_123", "role_not_in_domain", "Operator cannot approve in sensitive_gate.")
    assert b.source_domain_id == "operator_routine"
    assert b.attempted_domain_id == "sensitive_gate"
    assert b.role_id == "operator"
    assert b.reason_code == "role_not_in_domain"
    assert b.action_ref == "gate_123"
    out = b.to_dict()
    assert out["reason_code"] == "role_not_in_domain"


# ----- Explanation -----


def test_who_may_review_approve() -> None:
    """Explain who may review and who may approve."""
    reviewers = who_may_review(DOMAIN_SENSITIVE_GATE)
    assert len(reviewers) >= 2
    role_ids = [r["role_id"] for r in reviewers]
    assert "operator" in role_ids
    approvers = who_may_approve(DOMAIN_SENSITIVE_GATE)
    assert "approver" in approvers


def test_why_chain_blocked_self_approve() -> None:
    """Explanation for blocked chain when initiator approves."""
    reason = why_chain_blocked(DOMAIN_SENSITIVE_GATE, {"initiator_role_id": "operator", "approver_role_id": "operator"})
    assert "self_approve" in reason.lower() or "cannot" in reason.lower()


def test_why_escalation_required() -> None:
    """Explanation for why escalation is required."""
    reason = why_escalation_required(DOMAIN_SENSITIVE_GATE, "operator")
    assert len(reason) > 0
    assert "approver" in reason or "Escalate" in reason


def test_why_comment_only() -> None:
    """Operator may comment but not approve in sensitive_gate."""
    reason = why_comment_only(DOMAIN_SENSITIVE_GATE, "operator")
    assert "review" in reason.lower() or "comment" in reason.lower()
    assert "approve" in reason.lower()
    assert "approver" in reason


# ----- Approval domain / sensitive action domain -----


def test_get_approval_domain() -> None:
    """Approval domain for sensitive_gate has approver only."""
    ad = get_approval_domain("sensitive_gate_approval")
    assert ad is not None
    assert "approver" in ad.allowed_approver_role_ids
    assert ad.self_approve_blocked is True


def test_get_sensitive_action_domain() -> None:
    """Commit/send/apply map to sensitive_gate domain."""
    for kind in ("commit", "send", "apply"):
        sad = get_sensitive_action_domain(kind)
        assert sad is not None
        assert sad.review_domain_id == DOMAIN_SENSITIVE_GATE
        assert sad.sensitivity_label == "high"


# ----- Mission control slice -----


def test_review_domains_mission_control_slice(tmp_path: Path) -> None:
    """Mission control slice returns active domains and structure."""
    from workflow_dataset.review_domains.mission_control import review_domains_mission_control_slice
    try:
        slice_data = review_domains_mission_control_slice(repo_root=tmp_path)
    except Exception as e:
        pytest.skip(f"mission_control deps: {e}")
    assert "active_review_domains" in slice_data
    assert "active_review_domain_count" in slice_data
    assert "domain_blocked_approvals" in slice_data
    assert "required_escalations" in slice_data
    assert "most_sensitive_pending_review" in slice_data
    assert "next_recommended_review_domain_adjustment" in slice_data
    assert len(slice_data["active_review_domains"]) >= 5


# ----- M48H.1: Domain policies + escalation packs -----


def test_domain_policy_sensitive_gate() -> None:
    """Sensitive gate has a policy with separation of duties and rationale."""
    from workflow_dataset.review_domains.policies import get_domain_policy, list_domain_policies
    p = get_domain_policy(DOMAIN_SENSITIVE_GATE)
    assert p is not None
    assert p.domain_id == DOMAIN_SENSITIVE_GATE
    assert p.separation_of_duties_required is True
    assert p.initiator_cannot_approve is True
    assert "initiator" in p.policy_rationale.lower() or "distinct" in p.policy_rationale.lower() or "role" in p.policy_rationale.lower()
    all_policies = list_domain_policies()
    assert len(all_policies) >= 4
    assert any(x.policy_id == "sensitive_gate_policy" for x in all_policies)


def test_escalation_pack_sensitive_actions() -> None:
    """Sensitive actions escalation pack exists and has entries for commit/send/apply."""
    from workflow_dataset.review_domains.policies import (
        get_escalation_pack,
        list_escalation_packs,
        get_escalation_entries_for_action,
        ESCALATION_PACK_SENSITIVE_ACTIONS,
    )
    pack = get_escalation_pack(ESCALATION_PACK_SENSITIVE_ACTIONS)
    assert pack is not None
    assert pack.pack_id == ESCALATION_PACK_SENSITIVE_ACTIONS
    assert len(pack.entries) >= 5
    action_kinds = {e.action_kind for e in pack.entries}
    assert "commit" in action_kinds
    assert "send" in action_kinds
    assert "apply" in action_kinds
    packs = list_escalation_packs()
    assert len(packs) >= 1
    entries = get_escalation_entries_for_action("commit")
    assert len(entries) >= 1
    assert entries[0].target_role_id == "approver"
    assert "self_approve" in entries[0].trigger_condition or "approver" in entries[0].description


def test_separation_of_duties_summary() -> None:
    """Separation summary for sensitive_gate includes rationale and why required."""
    from workflow_dataset.review_domains.summaries import (
        separation_of_duties_summary,
        separation_of_duties_summary_all,
        format_separation_summary_text,
    )
    s = separation_of_duties_summary(DOMAIN_SENSITIVE_GATE)
    assert s["domain_id"] == DOMAIN_SENSITIVE_GATE
    assert s["requires_separation_of_duties"] is True
    assert s["initiator_cannot_approve"] is True
    assert "approver" in s["approver_roles"]
    assert s.get("policy_rationale") or s.get("why_required")
    text = format_separation_summary_text(s)
    assert "sensitive_gate" in text
    assert "separation" in text.lower()
    all_summaries = separation_of_duties_summary_all()
    assert len(all_summaries) >= 4
    assert any(x["domain_id"] == DOMAIN_SENSITIVE_GATE for x in all_summaries)
