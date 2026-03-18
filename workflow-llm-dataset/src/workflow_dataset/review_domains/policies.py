"""
M48H.1: Review-domain policies and escalation packs.
Built-in domain policies (separation of duties, rationale) and escalation packs for sensitive actions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.review_domains.models import (
    ReviewDomainPolicy,
    EscalationPack,
    EscalationPackEntry,
)
from workflow_dataset.review_domains.registry import (
    DOMAIN_SENSITIVE_GATE,
    DOMAIN_PRODUCTION_REPAIR,
    DOMAIN_TRUSTED_ROUTINE_AUDIT,
    DOMAIN_ADAPTATION_PROMOTION,
)


# ----- Built-in domain policies -----


def _builtin_domain_policies() -> list[ReviewDomainPolicy]:
    return [
        ReviewDomainPolicy(
            policy_id="sensitive_gate_policy",
            domain_id=DOMAIN_SENSITIVE_GATE,
            name="Sensitive gate separation of duties",
            description="Commit, send, and apply actions require a distinct approver; initiator cannot self-approve.",
            separation_of_duties_required=True,
            initiator_cannot_approve=True,
            min_distinct_approvers=1,
            policy_rationale="Sensitive actions (commit/send/apply) must be signed off by a role other than the initiator to reduce single-party risk and preserve audit clarity.",
            scope_note="SensitiveActionGate candidates.",
        ),
        ReviewDomainPolicy(
            policy_id="production_repair_policy",
            domain_id=DOMAIN_PRODUCTION_REPAIR,
            name="Production repair separation of duties",
            description="Production repair and rollback require approver distinct from operator.",
            separation_of_duties_required=True,
            initiator_cannot_approve=True,
            min_distinct_approvers=1,
            policy_rationale="Production changes and rollbacks require a second party to confirm intent and reduce mistaken or unilateral execution.",
            scope_note="Repair loops, production cut, rollback.",
        ),
        ReviewDomainPolicy(
            policy_id="trusted_routine_audit_policy",
            domain_id=DOMAIN_TRUSTED_ROUTINE_AUDIT,
            name="Trusted routine audit separation",
            description="Audit closure must be approved by auditor; operator cannot self-close audit.",
            separation_of_duties_required=True,
            initiator_cannot_approve=True,
            min_distinct_approvers=1,
            policy_rationale="Audit trail integrity requires that the party under audit does not approve closure of the same audit.",
            scope_note="Trusted routine audit ledger.",
        ),
        ReviewDomainPolicy(
            policy_id="adaptation_promotion_policy",
            domain_id=DOMAIN_ADAPTATION_PROMOTION,
            name="Adaptation promotion separation",
            description="Model/candidate promotion requires approver distinct from operator.",
            separation_of_duties_required=True,
            initiator_cannot_approve=True,
            min_distinct_approvers=1,
            policy_rationale="Promotion decisions affect production readiness; a distinct approver reduces bias and improves accountability.",
            scope_note="Adaptive execution, candidate model studio promotion.",
        ),
    ]


def get_domain_policy(domain_id: str, repo_root: Path | str | None = None) -> ReviewDomainPolicy | None:
    """Return the policy for a review domain (built-in first, then custom from data/local/review_domains)."""
    for p in _builtin_domain_policies():
        if p.domain_id == domain_id:
            return p
    root = Path(repo_root).resolve() if repo_root else Path.cwd()
    for p in _load_custom_policies(root):
        if p.domain_id == domain_id:
            return p
    return None


def list_domain_policies(repo_root: Path | str | None = None) -> list[ReviewDomainPolicy]:
    """List all domain policies (built-in then custom)."""
    root = Path(repo_root).resolve() if repo_root else Path.cwd()
    seen: set[str] = set()
    out: list[ReviewDomainPolicy] = []
    for p in _builtin_domain_policies() + _load_custom_policies(root):
        if p.policy_id not in seen:
            seen.add(p.policy_id)
            out.append(p)
    return out


def _load_custom_policies(repo_root: Path) -> list[ReviewDomainPolicy]:
    custom: list[ReviewDomainPolicy] = []
    config_dir = Path(repo_root) / "data" / "local" / "review_domains"
    path = config_dir / "policies.yaml"
    if not path.is_file():
        path = config_dir / "policies.json"
    if not path.is_file():
        return custom
    try:
        import json
        raw = path.read_text()
        if path.suffix == ".json":
            data = json.loads(raw)
        else:
            import yaml
            data = yaml.safe_load(raw) or {}
        for item in data.get("policies", []) if isinstance(data, dict) else []:
            custom.append(ReviewDomainPolicy.from_dict(item))
    except Exception:
        pass
    return custom


# ----- Built-in escalation packs -----


ESCALATION_PACK_SENSITIVE_ACTIONS = "sensitive_actions"


def _builtin_escalation_packs() -> list[EscalationPack]:
    return [
        EscalationPack(
            pack_id=ESCALATION_PACK_SENSITIVE_ACTIONS,
            name="Sensitive actions escalation",
            description="Escalation steps for commit, send, apply, production repair, and promotion.",
            sensitivity_label="high",
            entries=[
                EscalationPackEntry("commit", DOMAIN_SENSITIVE_GATE, "approver", "self_approve_blocked", "Operator must escalate to approver for commit sign-off.", 1),
                EscalationPackEntry("send", DOMAIN_SENSITIVE_GATE, "approver", "self_approve_blocked", "Operator must escalate to approver for send sign-off.", 2),
                EscalationPackEntry("apply", DOMAIN_SENSITIVE_GATE, "approver", "self_approve_blocked", "Operator must escalate to approver for apply sign-off.", 3),
                EscalationPackEntry("production_repair", DOMAIN_PRODUCTION_REPAIR, "approver", "manual", "Escalate to approver for production repair sign-off.", 4),
                EscalationPackEntry("adaptation_promotion", DOMAIN_ADAPTATION_PROMOTION, "approver", "manual", "Escalate to approver for promotion.", 5),
            ],
        ),
    ]


def get_escalation_pack(pack_id: str, repo_root: Path | str | None = None) -> EscalationPack | None:
    """Return escalation pack by id."""
    for p in _builtin_escalation_packs():
        if p.pack_id == pack_id:
            return p
    root = Path(repo_root).resolve() if repo_root else Path.cwd()
    for p in _load_custom_escalation_packs(root):
        if p.pack_id == pack_id:
            return p
    return None


def list_escalation_packs(repo_root: Path | str | None = None) -> list[EscalationPack]:
    """List all escalation packs."""
    root = Path(repo_root).resolve() if repo_root else Path.cwd()
    seen: set[str] = set()
    out: list[EscalationPack] = []
    for p in _builtin_escalation_packs() + _load_custom_escalation_packs(root):
        if p.pack_id not in seen:
            seen.add(p.pack_id)
            out.append(p)
    return out


def get_escalation_entries_for_action(action_kind: str, repo_root: Path | str | None = None) -> list[EscalationPackEntry]:
    """Return escalation pack entries that apply to this action kind (from any pack)."""
    entries: list[EscalationPackEntry] = []
    for pack in list_escalation_packs(repo_root):
        for e in pack.entries:
            if e.action_kind == action_kind:
                entries.append(e)
    entries.sort(key=lambda x: x.step_order)
    return entries


def _load_custom_escalation_packs(repo_root: Path) -> list[EscalationPack]:
    custom: list[EscalationPack] = []
    config_dir = Path(repo_root) / "data" / "local" / "review_domains"
    path = config_dir / "escalation_packs.yaml"
    if not path.is_file():
        path = config_dir / "escalation_packs.json"
    if not path.is_file():
        return custom
    try:
        import json
        raw = path.read_text()
        if path.suffix == ".json":
            data = json.loads(raw)
        else:
            import yaml
            data = yaml.safe_load(raw) or {}
        for item in data.get("escalation_packs", []) if isinstance(data, dict) else []:
            custom.append(EscalationPack.from_dict(item))
    except Exception:
        pass
    return custom
