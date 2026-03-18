"""
M48E–M48H: Review domains and shared approval boundaries.
Explicit review/approval domains, role-safe approval chains, escalation, cross-domain block, explanation.
"""

from workflow_dataset.review_domains.models import (
    ReviewDomain,
    ApprovalDomain,
    ReviewParticipantRole,
    EscalationRoute,
    MultiReviewRequirement,
    SensitiveActionDomain,
    DomainAuditTrace,
    BlockedCrossDomainAction,
    ReviewDomainPolicy,
    EscalationPack,
    EscalationPackEntry,
)
from workflow_dataset.review_domains.registry import (
    get_domain,
    list_domains,
    DOMAIN_OPERATOR_ROUTINE,
    DOMAIN_SENSITIVE_GATE,
    DOMAIN_PRODUCTION_REPAIR,
    DOMAIN_TRUSTED_ROUTINE_AUDIT,
    DOMAIN_ADAPTATION_PROMOTION,
)
from workflow_dataset.review_domains.boundaries import (
    allowed_reviewers_for_domain,
    allowed_approvers_for_domain,
    role_safe_approval_chain,
    self_approve_blocked,
    escalation_required,
    cross_domain_block,
)
from workflow_dataset.review_domains.explain import (
    who_may_review,
    who_may_approve,
    why_chain_blocked,
    why_escalation_required,
    why_comment_only,
)

__all__ = [
    "ReviewDomain",
    "ApprovalDomain",
    "ReviewParticipantRole",
    "EscalationRoute",
    "MultiReviewRequirement",
    "SensitiveActionDomain",
    "DomainAuditTrace",
    "BlockedCrossDomainAction",
    "ReviewDomainPolicy",
    "EscalationPack",
    "EscalationPackEntry",
    "get_domain",
    "list_domains",
    "DOMAIN_OPERATOR_ROUTINE",
    "DOMAIN_SENSITIVE_GATE",
    "DOMAIN_PRODUCTION_REPAIR",
    "DOMAIN_TRUSTED_ROUTINE_AUDIT",
    "DOMAIN_ADAPTATION_PROMOTION",
    "allowed_reviewers_for_domain",
    "allowed_approvers_for_domain",
    "role_safe_approval_chain",
    "self_approve_blocked",
    "escalation_required",
    "cross_domain_block",
    "who_may_review",
    "who_may_approve",
    "why_chain_blocked",
    "why_escalation_required",
    "why_comment_only",
    "get_domain_policy",
    "list_domain_policies",
    "get_escalation_pack",
    "list_escalation_packs",
    "get_escalation_entries_for_action",
    "ESCALATION_PACK_SENSITIVE_ACTIONS",
    "separation_of_duties_summary",
    "separation_of_duties_summary_all",
    "format_separation_summary_text",
]
