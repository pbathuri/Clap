"""
M48E–M48H: Built-in review domains and registry.
operator_routine, sensitive_gate, production_repair, trusted_routine_audit, adaptation_promotion.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.review_domains.models import (
    ReviewDomain,
    ApprovalDomain,
    ReviewParticipantRole,
    EscalationRoute,
    MultiReviewRequirement,
    SensitiveActionDomain,
    ParticipantCapability,
)


# Domain IDs
DOMAIN_OPERATOR_ROUTINE = "operator_routine"
DOMAIN_SENSITIVE_GATE = "sensitive_gate"
DOMAIN_PRODUCTION_REPAIR = "production_repair"
DOMAIN_TRUSTED_ROUTINE_AUDIT = "trusted_routine_audit"
DOMAIN_ADAPTATION_PROMOTION = "adaptation_promotion"


def _builtin_domains() -> list[ReviewDomain]:
    return [
        ReviewDomain(
            domain_id=DOMAIN_OPERATOR_ROUTINE,
            name="Operator routine review",
            description="Routine operator actions: queue approval, batch approve, daily sweep.",
            scope_note="Supervised loop queue, operator policy batch limits.",
            allowed_roles=[
                ReviewParticipantRole("operator", [ParticipantCapability.OBSERVE.value, ParticipantCapability.REVIEW.value, ParticipantCapability.APPROVE.value], "Operator", "Daily operator; may approve within policy."),
                ReviewParticipantRole("reviewer", [ParticipantCapability.OBSERVE.value, ParticipantCapability.REVIEW.value], "Reviewer", "May review and comment; separate approval when required."),
            ],
            escalation_routes=[
                EscalationRoute("", "reviewer", "manual", "Escalate to reviewer for second sign-off."),
            ],
            multi_review=MultiReviewRequirement(1, 1, False, "Single approver within policy."),
            self_approve_blocked=False,
            linked_authority_tier_ids=["queued_execute", "bounded_trusted_real"],
        ),
        ReviewDomain(
            domain_id=DOMAIN_SENSITIVE_GATE,
            name="Sensitive gate approval",
            description="Commit, send, apply candidates; requires explicit sign-off.",
            scope_note="SensitiveActionGate (commit/send/apply) candidates.",
            allowed_roles=[
                ReviewParticipantRole("operator", [ParticipantCapability.OBSERVE.value, ParticipantCapability.REVIEW.value], "Operator", "May review and comment; cannot self-approve sensitive gate."),
                ReviewParticipantRole("approver", [ParticipantCapability.OBSERVE.value, ParticipantCapability.REVIEW.value, ParticipantCapability.APPROVE.value, ParticipantCapability.REJECT.value], "Approver", "May approve or reject sensitive actions."),
                ReviewParticipantRole("auditor", [ParticipantCapability.OBSERVE.value], "Auditor", "Observe only; audit trail visibility."),
            ],
            escalation_routes=[
                EscalationRoute(DOMAIN_SENSITIVE_GATE, "approver", "self_approve_blocked", "Operator must escalate to approver for sign-off."),
            ],
            multi_review=MultiReviewRequirement(1, 1, True, "At least one approver; distinct from initiator when self-approve blocked."),
            self_approve_blocked=True,
            linked_authority_tier_ids=["commit_or_send_candidate"],
        ),
        ReviewDomain(
            domain_id=DOMAIN_PRODUCTION_REPAIR,
            name="Production repair approval",
            description="Repair loops, production fixes, rollback decisions.",
            scope_note="Repair loops, production cut, rollback actions.",
            allowed_roles=[
                ReviewParticipantRole("operator", [ParticipantCapability.OBSERVE.value, ParticipantCapability.REVIEW.value], "Operator", "May initiate; approval by higher role."),
                ReviewParticipantRole("approver", [ParticipantCapability.OBSERVE.value, ParticipantCapability.REVIEW.value, ParticipantCapability.APPROVE.value, ParticipantCapability.REJECT.value, ParticipantCapability.ESCALATE.value], "Approver", "May approve production repair or escalate."),
            ],
            escalation_routes=[
                EscalationRoute("", "approver", "manual", "Escalate to approver for production repair sign-off."),
            ],
            multi_review=MultiReviewRequirement(1, 1, True, "Approver must be distinct from operator for production repair."),
            self_approve_blocked=True,
            linked_authority_tier_ids=["bounded_trusted_real"],
        ),
        ReviewDomain(
            domain_id=DOMAIN_TRUSTED_ROUTINE_AUDIT,
            name="Trusted routine audit review",
            description="Audit review of trusted routine execution and promotion.",
            scope_note="Trusted routines, routine audit ledger.",
            allowed_roles=[
                ReviewParticipantRole("operator", [ParticipantCapability.OBSERVE.value, ParticipantCapability.REVIEW.value], "Operator", "May review; approval by auditor/approver."),
                ReviewParticipantRole("auditor", [ParticipantCapability.OBSERVE.value, ParticipantCapability.REVIEW.value, ParticipantCapability.APPROVE.value], "Auditor", "May approve audit closure."),
            ],
            escalation_routes=[],
            multi_review=MultiReviewRequirement(1, 1, False, "Single auditor sign-off."),
            self_approve_blocked=True,
            linked_authority_tier_ids=["bounded_trusted_real"],
        ),
        ReviewDomain(
            domain_id=DOMAIN_ADAPTATION_PROMOTION,
            name="Adaptation / promotion review",
            description="Model adaptation, candidate promotion, rollout decisions.",
            scope_note="Adaptive execution promotion, candidate model studio promotion.",
            allowed_roles=[
                ReviewParticipantRole("operator", [ParticipantCapability.OBSERVE.value, ParticipantCapability.REVIEW.value], "Operator", "May suggest; approval by approver."),
                ReviewParticipantRole("approver", [ParticipantCapability.OBSERVE.value, ParticipantCapability.REVIEW.value, ParticipantCapability.APPROVE.value, ParticipantCapability.REJECT.value], "Approver", "May approve promotion."),
            ],
            escalation_routes=[
                EscalationRoute("", "approver", "manual", "Escalate to approver for promotion."),
            ],
            multi_review=MultiReviewRequirement(1, 1, True, "Approver distinct from operator."),
            self_approve_blocked=True,
            linked_authority_tier_ids=["commit_or_send_candidate"],
        ),
    ]


def _builtin_approval_domains() -> list[ApprovalDomain]:
    return [
        ApprovalDomain("operator_routine_approval", DOMAIN_OPERATOR_ROUTINE, "Operator routine approval", ["operator"], 1, None, False),
        ApprovalDomain("sensitive_gate_approval", DOMAIN_SENSITIVE_GATE, "Sensitive gate approval", ["approver"], 1, EscalationRoute(DOMAIN_SENSITIVE_GATE, "approver", "self_approve_blocked", "Escalate to approver."), True),
        ApprovalDomain("production_repair_approval", DOMAIN_PRODUCTION_REPAIR, "Production repair approval", ["approver"], 1, EscalationRoute("", "approver", "manual", "Escalate to approver."), True),
        ApprovalDomain("trusted_routine_audit_approval", DOMAIN_TRUSTED_ROUTINE_AUDIT, "Trusted routine audit approval", ["auditor"], 1, None, True),
        ApprovalDomain("adaptation_promotion_approval", DOMAIN_ADAPTATION_PROMOTION, "Adaptation promotion approval", ["approver"], 1, EscalationRoute("", "approver", "manual", "Escalate to approver."), True),
    ]


def _builtin_sensitive_action_domains() -> list[SensitiveActionDomain]:
    return [
        SensitiveActionDomain("commit", DOMAIN_SENSITIVE_GATE, "sensitive_gate_approval", "high"),
        SensitiveActionDomain("send", DOMAIN_SENSITIVE_GATE, "sensitive_gate_approval", "high"),
        SensitiveActionDomain("apply", DOMAIN_SENSITIVE_GATE, "sensitive_gate_approval", "high"),
        SensitiveActionDomain("production_repair", DOMAIN_PRODUCTION_REPAIR, "production_repair_approval", "high"),
        SensitiveActionDomain("trusted_routine_audit", DOMAIN_TRUSTED_ROUTINE_AUDIT, "trusted_routine_audit_approval", "medium"),
        SensitiveActionDomain("adaptation_promotion", DOMAIN_ADAPTATION_PROMOTION, "adaptation_promotion_approval", "high"),
    ]


def _load_custom_domains(repo_root: Path) -> list[ReviewDomain]:
    custom: list[ReviewDomain] = []
    config_dir = Path(repo_root) / "data" / "local" / "review_domains"
    if not config_dir.is_dir():
        return custom
    domains_file = config_dir / "domains.yaml"
    if not domains_file.is_file():
        domains_file = config_dir / "domains.json"
    if not domains_file.is_file():
        return custom
    try:
        import json
        raw = domains_file.read_text()
        if domains_file.suffix == ".json":
            data = json.loads(raw)
        else:
            import yaml
            data = yaml.safe_load(raw) or {}
        for item in data.get("domains", []) if isinstance(data, dict) else []:
            custom.append(ReviewDomain.from_dict(item))
    except Exception:
        pass
    return custom


def get_domain(domain_id: str, repo_root: Path | str | None = None) -> ReviewDomain | None:
    """Return review domain by id; built-in first, then custom from data/local/review_domains."""
    for d in _builtin_domains():
        if d.domain_id == domain_id:
            return d
    root = Path(repo_root) if repo_root else Path.cwd()
    for d in _load_custom_domains(root):
        if d.domain_id == domain_id:
            return d
    return None


def list_domains(repo_root: Path | str | None = None) -> list[ReviewDomain]:
    """List all review domains (built-in then custom)."""
    root = Path(repo_root) if repo_root else Path.cwd()
    seen: set[str] = set()
    out: list[ReviewDomain] = []
    for d in _builtin_domains() + _load_custom_domains(root):
        if d.domain_id not in seen:
            seen.add(d.domain_id)
            out.append(d)
    return out


def get_approval_domain(approval_domain_id: str) -> ApprovalDomain | None:
    """Return approval domain by id (built-in only for first draft)."""
    for a in _builtin_approval_domains():
        if a.approval_domain_id == approval_domain_id:
            return a
    return None


def get_sensitive_action_domain(action_kind: str) -> SensitiveActionDomain | None:
    """Return sensitive action domain for action kind (commit, send, apply, production_repair, etc.)."""
    for s in _builtin_sensitive_action_domains():
        if s.action_kind == action_kind:
            return s
    return None
