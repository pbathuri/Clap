"""
M28I–M28L: Override board — list active effects, overrides, apply/revoke, explain why.
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

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:16]

from workflow_dataset.human_policy.models import OverrideRecord, SCOPE_GLOBAL, SCOPE_PROJECT, SCOPE_PACK
from workflow_dataset.human_policy.store import load_policy_config, load_overrides, save_overrides
from workflow_dataset.human_policy.evaluate import evaluate, PolicyEvalResult


@dataclass
class ActiveEffect:
    """One active policy effect for board display."""
    scope: str = ""
    scope_id: str = ""
    effect_key: str = ""
    effect_value: Any = None
    source: str = "config"  # config | override


def list_active_effects(
    project_id: str = "",
    pack_id: str = "",
    repo_root: Path | str | None = None,
) -> list[ActiveEffect]:
    """List active policy effects that apply to the given context."""
    config = load_policy_config(repo_root)
    overrides = [o for o in load_overrides(repo_root) if o.is_active(utc_now_iso())]
    effects: list[ActiveEffect] = []
    effects.append(ActiveEffect(scope=SCOPE_GLOBAL, effect_key="always_manual", effect_value=config.approval_defaults.always_manual, source="config"))
    effects.append(ActiveEffect(scope=SCOPE_GLOBAL, effect_key="may_batch_for_risk", effect_value=config.approval_defaults.may_batch_for_risk or "low", source="config"))
    effects.append(ActiveEffect(scope=SCOPE_GLOBAL, effect_key="may_delegate", effect_value=config.delegation_default.may_delegate, source="config"))
    if project_id and config.project_simulate_only.get(project_id):
        effects.append(ActiveEffect(scope=SCOPE_PROJECT, scope_id=project_id, effect_key="simulate_only", effect_value=True, source="config"))
    if pack_id and config.pack_may_override_defaults.get(pack_id):
        effects.append(ActiveEffect(scope=SCOPE_PACK, scope_id=pack_id, effect_key="pack_may_override_defaults", effect_value=True, source="config"))
    for ov in overrides:
        if ov.scope == SCOPE_PROJECT and ov.scope_id != project_id:
            continue
        if ov.scope == SCOPE_PACK and ov.scope_id != pack_id:
            continue
        effects.append(ActiveEffect(scope=ov.scope, scope_id=ov.scope_id, effect_key=ov.rule_key, effect_value=ov.rule_value, source="override"))
    return effects


def list_overrides(
    active_only: bool = True,
    repo_root: Path | str | None = None,
) -> list[OverrideRecord]:
    """List override records; active_only=False includes revoked/expired."""
    records = load_overrides(repo_root)
    if active_only:
        now = utc_now_iso()
        records = [r for r in records if r.is_active(now)]
    return records


def apply_override(
    scope: str,
    scope_id: str,
    rule_key: str,
    rule_value: Any,
    reason: str = "",
    expires_at: str = "",
    repo_root: Path | str | None = None,
) -> OverrideRecord:
    """Add a temporary override. Returns the new record."""
    records = load_overrides(repo_root)
    now = utc_now_iso()
    override_id = stable_id("ov", scope, scope_id, rule_key, now, prefix="ov_")
    record = OverrideRecord(
        override_id=override_id,
        scope=scope,
        scope_id=scope_id,
        rule_key=rule_key,
        rule_value=rule_value,
        reason=reason,
        created_at=now,
        expires_at=expires_at,
    )
    records.append(record)
    save_overrides(records, repo_root)
    return record


def revoke_override(
    override_id: str,
    repo_root: Path | str | None = None,
) -> OverrideRecord | None:
    """Revoke an override by id. Returns updated record or None if not found."""
    records = load_overrides(repo_root)
    now = utc_now_iso()
    for i, r in enumerate(records):
        if r.override_id == override_id:
            records[i] = OverrideRecord(
                override_id=r.override_id,
                scope=r.scope,
                scope_id=r.scope_id,
                rule_key=r.rule_key,
                rule_value=r.rule_value,
                reason=r.reason,
                created_at=r.created_at,
                expires_at=r.expires_at,
                revoked_at=now,
            )
            save_overrides(records, repo_root)
            return records[i]
    return None


def explain_why_blocked(
    action_class: str,
    project_id: str = "",
    pack_id: str = "",
    repo_root: Path | str | None = None,
) -> list[str]:
    """Return human-readable explanation of why an action is blocked (if it is)."""
    result = evaluate(action_class=action_class, project_id=project_id, pack_id=pack_id, repo_root=repo_root)
    if result.blocked:
        return result.explanation
    if result.is_always_manual:
        return ["Action requires manual approval (policy: always_manual)."] + result.explanation
    return []


def explain_why_allowed(
    action_class: str,
    project_id: str = "",
    pack_id: str = "",
    repo_root: Path | str | None = None,
) -> list[str]:
    """Return human-readable explanation of why an action is allowed."""
    result = evaluate(action_class=action_class, project_id=project_id, pack_id=pack_id, repo_root=repo_root)
    if result.blocked:
        return []
    lines = [f"action_class={action_class} is_always_manual={result.is_always_manual} may_batch={result.may_batch}"]
    lines.extend(result.explanation)
    return lines
