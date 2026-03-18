"""
M35A–M35D: Trusted routine contract model — permitted/excluded actions, approvals, review gates,
allowed targets, stop conditions, audit, fallback.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from workflow_dataset.trust.tiers import get_tier, AuthorityTier, tier_allows_action


@dataclass
class TrustedRoutineContract:
    """Contract for one trusted routine: scope, actions, approvals, gates, targets, stop conditions, audit, fallback."""
    contract_id: str = ""
    label: str = ""
    description: str = ""
    scope: str = "global"                    # global | project:<id> | pack:<id> | workflow:<id> | recurring_routine:<id> | worker_lane:<id>
    scope_id: str = ""
    authority_tier_id: str = ""              # tier from trust/tiers (e.g. sandbox_write, bounded_trusted_real)
    routine_id: str = ""                     # routine_id or workflow_id this contract applies to
    permitted_action_classes: list[str] = field(default_factory=list)
    excluded_action_classes: list[str] = field(default_factory=list)
    required_approvals: list[str] = field(default_factory=list)   # e.g. approval_registry, checkpoint_before_real
    required_review_gates: list[str] = field(default_factory=list)  # e.g. inbox_studio, review_studio
    allowed_targets: list[str] = field(default_factory=list)     # path patterns or resource ids; empty = no restriction
    excluded_targets: list[str] = field(default_factory=list)
    stop_conditions: list[str] = field(default_factory=list)      # e.g. artifact_produced, step_count_max, manual_stop
    audit_required: bool = False
    audit_note: str = ""
    fallback_behavior: str = ""              # e.g. downgrade_to_simulate, handoff_to_review, stop
    enabled: bool = True
    created_utc: str = ""
    updated_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "label": self.label,
            "description": self.description,
            "scope": self.scope,
            "scope_id": self.scope_id,
            "authority_tier_id": self.authority_tier_id,
            "routine_id": self.routine_id,
            "permitted_action_classes": list(self.permitted_action_classes),
            "excluded_action_classes": list(self.excluded_action_classes),
            "required_approvals": list(self.required_approvals),
            "required_review_gates": list(self.required_review_gates),
            "allowed_targets": list(self.allowed_targets),
            "excluded_targets": list(self.excluded_targets),
            "stop_conditions": list(self.stop_conditions),
            "audit_required": self.audit_required,
            "audit_note": self.audit_note,
            "fallback_behavior": self.fallback_behavior,
            "enabled": self.enabled,
            "created_utc": self.created_utc,
            "updated_utc": self.updated_utc,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TrustedRoutineContract":
        return cls(
            contract_id=d.get("contract_id", ""),
            label=d.get("label", ""),
            description=d.get("description", ""),
            scope=d.get("scope", "global"),
            scope_id=d.get("scope_id", ""),
            authority_tier_id=d.get("authority_tier_id", ""),
            routine_id=d.get("routine_id", ""),
            permitted_action_classes=list(d.get("permitted_action_classes") or []),
            excluded_action_classes=list(d.get("excluded_action_classes") or []),
            required_approvals=list(d.get("required_approvals") or []),
            required_review_gates=list(d.get("required_review_gates") or []),
            allowed_targets=list(d.get("allowed_targets") or []),
            excluded_targets=list(d.get("excluded_targets") or []),
            stop_conditions=list(d.get("stop_conditions") or []),
            audit_required=bool(d.get("audit_required", False)),
            audit_note=d.get("audit_note", ""),
            fallback_behavior=d.get("fallback_behavior", ""),
            enabled=bool(d.get("enabled", True)),
            created_utc=d.get("created_utc", ""),
            updated_utc=d.get("updated_utc", ""),
        )


CONTRACTS_DIR = "data/local/trust"
CONTRACTS_FILE = "contracts.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _contracts_path(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / CONTRACTS_DIR / CONTRACTS_FILE


def load_contracts(repo_root: Path | str | None = None) -> list[TrustedRoutineContract]:
    path = _contracts_path(repo_root)
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [TrustedRoutineContract.from_dict(d) for d in raw.get("contracts", [])]
    except Exception:
        return []


def save_contracts(contracts: list[TrustedRoutineContract], repo_root: Path | str | None = None) -> Path:
    path = _contracts_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"contracts": [c.to_dict() for c in contracts]}, indent=2), encoding="utf-8")
    return path


def get_contract(contract_id: str, repo_root: Path | str | None = None) -> TrustedRoutineContract | None:
    for c in load_contracts(repo_root):
        if c.contract_id == contract_id:
            return c
    return None


def get_contracts_for_routine(routine_id: str, repo_root: Path | str | None = None) -> list[TrustedRoutineContract]:
    return [c for c in load_contracts(repo_root) if c.enabled and c.routine_id == routine_id]


def validate_contract(contract: TrustedRoutineContract) -> tuple[bool, list[str]]:
    """
    Validate contract: consistent with tier, no conflicting rules.
    Returns (valid, list of error messages).
    """
    errors: list[str] = []
    if not contract.contract_id:
        errors.append("contract_id is required")
    if not contract.authority_tier_id:
        errors.append("authority_tier_id is required")
    tier = get_tier(contract.authority_tier_id)
    if not tier:
        errors.append(f"Unknown authority_tier_id: {contract.authority_tier_id}")
    else:
        for action in contract.excluded_action_classes:
            if action in contract.permitted_action_classes:
                errors.append(f"Action {action} cannot be both permitted and excluded")
        for action in (contract.permitted_action_classes or []):
            if not tier_allows_action(tier, action):
                errors.append(f"Tier {tier.tier_id} does not allow action_class {action}")
    if contract.scope and contract.scope != "global" and not contract.scope_id:
        errors.append("scope_id required when scope is not global")
    return len(errors) == 0, errors
