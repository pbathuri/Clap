"""
M28I–M28L: Policy evaluation — is action always manual, may batch, may delegate, etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.human_policy.models import (
    HumanPolicyConfig,
    OverrideRecord,
    SCOPE_PROJECT,
    SCOPE_PACK,
)
from workflow_dataset.human_policy.store import load_policy_config, load_overrides


@dataclass
class PolicyEvalResult:
    """Result of evaluating policy for a given context."""
    is_always_manual: bool = True
    may_batch: bool = False
    may_delegate: bool = False
    may_use_worker_lanes: bool = False
    pack_may_override_defaults: bool = False
    simulate_only: bool = False
    blocked: bool = False
    explanation: list[str] = field(default_factory=list)


def _apply_overrides_to_result(
    result: PolicyEvalResult,
    overrides: list[OverrideRecord],
    project_id: str,
    pack_id: str,
    now: str,
) -> None:
    """Apply active overrides to result in place."""
    for ov in overrides:
        if not ov.is_active(now):
            continue
        if ov.scope == SCOPE_PROJECT and ov.scope_id != project_id:
            continue
        if ov.scope == SCOPE_PACK and ov.scope_id != pack_id:
            continue
        if ov.scope == "global" or ov.scope_id == project_id or ov.scope_id == pack_id:
            key, val = ov.rule_key, ov.rule_value
            if key == "manual_only":
                result.is_always_manual = bool(val)
                result.explanation.append(f"override {ov.override_id}: manual_only={val}")
            elif key == "simulate_only":
                if project_id and ov.scope == SCOPE_PROJECT:
                    result.simulate_only = bool(val)
                    result.explanation.append(f"override {ov.override_id}: project simulate_only={val}")
            elif key == "may_delegate":
                result.may_delegate = bool(val)
                result.explanation.append(f"override {ov.override_id}: may_delegate={val}")
            elif key == "may_use_worker_lanes":
                result.may_use_worker_lanes = bool(val)
                result.explanation.append(f"override {ov.override_id}: may_use_worker_lanes={val}")


def _get_action_policy(config: HumanPolicyConfig, action_class: str) -> tuple[bool, bool, bool]:
    """Return (require_approval, allow_batch, allow_auto) for action_class."""
    for p in config.action_class_policies:
        if p.action_class == action_class:
            return (p.require_approval, p.allow_batch, p.allow_auto)
    return (True, False, False)


# Need ApprovalRequirementPolicy.from_dict - add to models if missing. For now use a simple approach: approval_defaults is already a dataclass, we can copy by building new from attributes.
def evaluate(
    action_class: str = "",
    project_id: str = "",
    pack_id: str = "",
    repo_root: Path | str | None = None,
) -> PolicyEvalResult:
    """
    Evaluate policy for the given action and context.
    Returns is_always_manual, may_batch, may_delegate, may_use_worker_lanes, pack_may_override, simulate_only, blocked, explanation.
    """
    root = Path(repo_root).resolve() if repo_root else None
    config = load_policy_config(root)
    overrides = load_overrides(root)
    now = utc_now_iso()
    out = PolicyEvalResult(explanation=[])

    # Blocked list (any scope matching project/pack/global)
    for b in config.blocked_actions:
        if b.scope == "global" or (b.scope == SCOPE_PROJECT and b.scope_id == project_id) or (b.scope == SCOPE_PACK and b.scope_id == pack_id):
            if action_class in b.blocked_action_classes:
                out.blocked = True
                out.is_always_manual = True
                out.explanation.append(f"blocked: {action_class} in blocked_actions for scope {b.scope}:{b.scope_id}")
                return out

    require_approval, allow_batch, allow_auto = _get_action_policy(config, action_class)
    out.is_always_manual = config.approval_defaults.always_manual and require_approval
    out.may_batch = allow_batch and bool(config.approval_defaults.may_batch_for_risk)
    out.may_delegate = config.delegation_default.may_delegate
    out.may_use_worker_lanes = config.delegation_default.may_delegate
    out.pack_may_override_defaults = config.pack_may_override_defaults.get(pack_id, False) if pack_id else False
    out.simulate_only = config.project_simulate_only.get(project_id, False) if project_id else False
    _apply_overrides_to_result(out, overrides, project_id, pack_id, now)
    if not out.explanation:
        out.explanation.append(f"action_class={action_class} require_approval={require_approval} allow_batch={allow_batch} allow_auto={allow_auto}")
    return out
