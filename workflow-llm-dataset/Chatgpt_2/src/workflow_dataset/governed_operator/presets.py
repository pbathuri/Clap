"""
M48L.1: Delegation presets — narrow trusted routine, supervised operator, maintenance-only.
"""

from __future__ import annotations

from workflow_dataset.governed_operator.models import DelegationPreset

# Action classes aligned with trust.tiers
ACTION_OBSERVE = "observe"
ACTION_SUGGEST = "suggest"
ACTION_DRAFT = "draft"
ACTION_EXECUTE_SIMULATE = "execute_simulate"
ACTION_SANDBOX_WRITE = "sandbox_write"
ACTION_QUEUED_EXECUTE = "queued_execute"
ACTION_EXECUTE_TRUSTED_REAL = "execute_trusted_real"
ACTION_COMMIT_OR_SEND = "commit_or_send"


def _builtin_presets() -> list[DelegationPreset]:
    return [
        DelegationPreset(
            preset_id="narrow_trusted_routine",
            label="Narrow trusted routine",
            description="Single or few trusted routines; bounded real execution within one review domain.",
            authority_tier_id="bounded_trusted_real",
            trust_preset_id="bounded_trusted_routine",
            allowed_action_classes=[
                ACTION_OBSERVE,
                ACTION_SUGGEST,
                ACTION_DRAFT,
                ACTION_SANDBOX_WRITE,
                ACTION_EXECUTE_SIMULATE,
                ACTION_QUEUED_EXECUTE,
                ACTION_EXECUTE_TRUSTED_REAL,
            ],
            forbidden_action_classes=[ACTION_COMMIT_OR_SEND],
            default_review_domain_id="operator_routine",
            default_role_id="operator",
            max_routine_ids=3,
            when_to_use="Use when delegating one or a small set of trusted routines (e.g. morning_digest, approval_sweep) with real execution but no commit/send.",
        ),
        DelegationPreset(
            preset_id="supervised_operator",
            label="Supervised operator",
            description="Operator runs with approval queue and review gates; no direct real run without approval.",
            authority_tier_id="queued_execute",
            trust_preset_id="supervised_operator",
            allowed_action_classes=[
                ACTION_OBSERVE,
                ACTION_SUGGEST,
                ACTION_DRAFT,
                ACTION_SANDBOX_WRITE,
                ACTION_EXECUTE_SIMULATE,
                ACTION_QUEUED_EXECUTE,
            ],
            forbidden_action_classes=[ACTION_EXECUTE_TRUSTED_REAL, ACTION_COMMIT_OR_SEND],
            default_review_domain_id="operator_routine",
            default_role_id="operator",
            max_routine_ids=0,
            when_to_use="Use when operator mode should run with every execution queued for approval; safest for shared or high-friction environments.",
        ),
        DelegationPreset(
            preset_id="maintenance_only",
            label="Maintenance only",
            description="Read-only and lightweight maintenance; no execution or draft that affects production.",
            authority_tier_id="sandbox_write",
            trust_preset_id="cautious",
            allowed_action_classes=[ACTION_OBSERVE, ACTION_SUGGEST, ACTION_DRAFT, ACTION_SANDBOX_WRITE, ACTION_EXECUTE_SIMULATE],
            forbidden_action_classes=[ACTION_QUEUED_EXECUTE, ACTION_EXECUTE_TRUSTED_REAL, ACTION_COMMIT_OR_SEND],
            default_review_domain_id="operator_routine",
            default_role_id="operator",
            max_routine_ids=0,
            when_to_use="Use for maintenance windows or when delegation must not perform any real execution or commit/send.",
        ),
    ]


_PRESETS: list[DelegationPreset] | None = None


def list_delegation_presets() -> list[DelegationPreset]:
    """Return all built-in delegation presets."""
    global _PRESETS
    if _PRESETS is None:
        _PRESETS = _builtin_presets()
    return list(_PRESETS)


def get_delegation_preset(preset_id: str) -> DelegationPreset | None:
    """Return the preset with the given preset_id, or None."""
    for p in list_delegation_presets():
        if p.preset_id == preset_id:
            return p
    return None
