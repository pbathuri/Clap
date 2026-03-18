"""
M48A: Built-in human role definitions.
"""

from __future__ import annotations

from workflow_dataset.trust.tiers import (
    ACTION_OBSERVE,
    ACTION_SUGGEST,
    ACTION_DRAFT,
    ACTION_EXECUTE_SIMULATE,
    ACTION_SANDBOX_WRITE,
    ACTION_QUEUED_EXECUTE,
    ACTION_EXECUTE_TRUSTED_REAL,
    ACTION_COMMIT_OR_SEND,
    AuthorityTierId,
)
from workflow_dataset.governance.models import HumanRole, RoleType


def _builtin_roles() -> list[HumanRole]:
    return [
        HumanRole(
            role_id="observer",
            role_type=RoleType.OBSERVER.value,
            label="Observer",
            description="Read-only; may view surfaces and status but not execute or approve.",
            allowed_surface_ids=[],
            forbidden_surface_ids=["operator_mode", "review_studio_approve", "trust_cockpit_approve"],
            allowed_action_classes=[ACTION_OBSERVE],
            forbidden_action_classes=[ACTION_EXECUTE_SIMULATE, ACTION_QUEUED_EXECUTE, ACTION_EXECUTE_TRUSTED_REAL, ACTION_COMMIT_OR_SEND],
            may_review=False,
            may_approve=False,
            may_execute=False,
            may_request_only=False,
            observe_only=True,
            default_authority_tier_id=AuthorityTierId.OBSERVE_ONLY.value,
            order=0,
        ),
        HumanRole(
            role_id="operator",
            role_type=RoleType.OPERATOR.value,
            label="Operator",
            description="Execute within approved scope; queue and simulate; real run after approval.",
            allowed_surface_ids=["workspace_home", "day_status", "queue_summary", "continuity_carry_forward", "operator_mode", "inbox"],
            forbidden_surface_ids=["review_studio_approve", "trust_cockpit_approve", "sensitive_gate_approve"],
            allowed_action_classes=[ACTION_OBSERVE, ACTION_SUGGEST, ACTION_DRAFT, ACTION_SANDBOX_WRITE, ACTION_EXECUTE_SIMULATE, ACTION_QUEUED_EXECUTE],
            forbidden_action_classes=[ACTION_COMMIT_OR_SEND],
            may_review=True,
            may_approve=False,
            may_execute=True,
            may_request_only=False,
            observe_only=False,
            default_authority_tier_id=AuthorityTierId.QUEUED_EXECUTE.value,
            order=1,
        ),
        HumanRole(
            role_id="reviewer",
            role_type=RoleType.REVIEWER.value,
            label="Reviewer",
            description="Review and comment; may approve in designated domains; no direct execution.",
            allowed_surface_ids=["workspace_home", "queue_summary", "review_studio", "inbox", "approvals_urgent"],
            forbidden_surface_ids=["operator_mode_execute", "trust_cockpit_grant"],
            allowed_action_classes=[ACTION_OBSERVE, ACTION_SUGGEST, ACTION_DRAFT],
            forbidden_action_classes=[ACTION_QUEUED_EXECUTE, ACTION_EXECUTE_TRUSTED_REAL, ACTION_COMMIT_OR_SEND],
            may_review=True,
            may_approve=True,
            may_execute=False,
            may_request_only=True,
            observe_only=False,
            default_authority_tier_id=AuthorityTierId.DRAFT_ONLY.value,
            order=2,
        ),
        HumanRole(
            role_id="approver",
            role_type=RoleType.APPROVER.value,
            label="Approver",
            description="Approve sensitive gates and real execution; separation of duties from operator.",
            allowed_surface_ids=["review_studio", "approvals_urgent", "trust_cockpit", "sensitive_gates"],
            forbidden_surface_ids=["operator_mode_execute"],
            allowed_action_classes=[ACTION_OBSERVE, ACTION_SUGGEST, ACTION_DRAFT],
            forbidden_action_classes=[ACTION_QUEUED_EXECUTE, ACTION_EXECUTE_TRUSTED_REAL, ACTION_COMMIT_OR_SEND],
            may_review=True,
            may_approve=True,
            may_execute=False,
            may_request_only=False,
            observe_only=False,
            default_authority_tier_id=AuthorityTierId.DRAFT_ONLY.value,
            order=3,
        ),
        HumanRole(
            role_id="maintainer",
            role_type=RoleType.MAINTAINER.value,
            label="Maintainer",
            description="Full scope within vertical: operate, review, approve; bounded trusted real with audit.",
            allowed_surface_ids=[],  # all not forbidden
            forbidden_surface_ids=[],
            allowed_action_classes=[ACTION_OBSERVE, ACTION_SUGGEST, ACTION_DRAFT, ACTION_SANDBOX_WRITE, ACTION_EXECUTE_SIMULATE, ACTION_QUEUED_EXECUTE, ACTION_EXECUTE_TRUSTED_REAL],
            forbidden_action_classes=[ACTION_COMMIT_OR_SEND],
            may_review=True,
            may_approve=True,
            may_execute=True,
            may_request_only=False,
            observe_only=False,
            default_authority_tier_id=AuthorityTierId.BOUNDED_TRUSTED_REAL.value,
            order=4,
        ),
        HumanRole(
            role_id="support_reviewer",
            role_type=RoleType.SUPPORT_REVIEWER.value,
            label="Support reviewer",
            description="Escalation reviewer; may approve in support domain when operator/reviewer blocked.",
            allowed_surface_ids=["review_studio", "approvals_urgent", "support_recovery"],
            forbidden_surface_ids=["operator_mode_execute", "trust_cockpit_grant"],
            allowed_action_classes=[ACTION_OBSERVE, ACTION_SUGGEST, ACTION_DRAFT],
            forbidden_action_classes=[ACTION_QUEUED_EXECUTE, ACTION_EXECUTE_TRUSTED_REAL, ACTION_COMMIT_OR_SEND],
            may_review=True,
            may_approve=True,
            may_execute=False,
            may_request_only=False,
            observe_only=False,
            default_authority_tier_id=AuthorityTierId.DRAFT_ONLY.value,
            order=5,
        ),
    ]


def get_role(role_id: str) -> HumanRole | None:
    """Return built-in role by id."""
    for r in _builtin_roles():
        if r.role_id == role_id:
            return r
    return None


def list_roles() -> list[HumanRole]:
    """Return all built-in roles in order."""
    return list(_builtin_roles())
