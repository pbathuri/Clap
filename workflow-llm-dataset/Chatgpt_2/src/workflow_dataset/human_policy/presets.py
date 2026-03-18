"""
M28L.1: Policy presets and trust modes.
First-draft presets: strict_manual, supervised_daily_operator, bounded_delegation, demo_mode, rollout_safe_mode.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.human_policy.models import (
    HumanPolicyConfig,
    ActionClassPolicy,
    ApprovalRequirementPolicy,
    DelegationPolicy,
    ExceptionPolicy,
    ACTION_EXECUTE_SIMULATE,
    ACTION_PLANNER_COMPILE,
    ACTION_EXECUTE_TRUSTED_REAL,
    ACTION_EXECUTOR_RESUME,
    ACTION_DELEGATE_GOAL,
    ACTION_USE_WORKER_LANE,
    ACTION_ROUTING,
)
from workflow_dataset.human_policy.store import load_policy_config, save_policy_config

# Preset identifiers (trust modes)
PRESET_STRICT_MANUAL = "strict_manual"
PRESET_SUPERVISED_DAILY_OPERATOR = "supervised_daily_operator"
PRESET_BOUNDED_DELEGATION = "bounded_delegation"
PRESET_DEMO_MODE = "demo_mode"
PRESET_ROLLOUT_SAFE = "rollout_safe_mode"

PRESET_NAMES = (
    PRESET_STRICT_MANUAL,
    PRESET_SUPERVISED_DAILY_OPERATOR,
    PRESET_BOUNDED_DELEGATION,
    PRESET_DEMO_MODE,
    PRESET_ROLLOUT_SAFE,
)

# One-line descriptions for list/explain
PRESET_DESCRIPTIONS: dict[str, str] = {
    PRESET_STRICT_MANUAL: "All actions require explicit approval; no batch, no delegation, no worker lanes.",
    PRESET_SUPERVISED_DAILY_OPERATOR: "Batch low-risk simulate/plan; trusted real and resume still manual; no delegation.",
    PRESET_BOUNDED_DELEGATION: "Delegation and worker lanes allowed with approval; batch medium-risk; trusted real manual.",
    PRESET_DEMO_MODE: "Relaxed for demos: simulate/plan auto; delegation allowed; trusted real requires approval.",
    PRESET_ROLLOUT_SAFE: "Rollout-safe: batch low only; no delegation; keep projects simulate-only until explicitly allowed.",
}


def _base_action_policies() -> list[ActionClassPolicy]:
    """Common action-class list; presets override specific entries."""
    return [
        ActionClassPolicy(action_class=ACTION_EXECUTE_SIMULATE, allow_auto=False, require_approval=True, allow_batch=True),
        ActionClassPolicy(action_class=ACTION_PLANNER_COMPILE, allow_auto=False, require_approval=True, allow_batch=True),
        ActionClassPolicy(action_class=ACTION_EXECUTE_TRUSTED_REAL, allow_auto=False, require_approval=True, allow_batch=False),
        ActionClassPolicy(action_class=ACTION_EXECUTOR_RESUME, allow_auto=False, require_approval=True, allow_batch=False),
        ActionClassPolicy(action_class=ACTION_DELEGATE_GOAL, allow_auto=False, require_approval=True, allow_batch=False),
        ActionClassPolicy(action_class=ACTION_USE_WORKER_LANE, allow_auto=False, require_approval=True, allow_batch=False),
        ActionClassPolicy(action_class=ACTION_ROUTING, allow_auto=True, require_approval=False, allow_batch=False),
    ]


def _preset_strict_manual() -> HumanPolicyConfig:
    return HumanPolicyConfig(
        action_class_policies=_base_action_policies(),
        approval_defaults=ApprovalRequirementPolicy(always_manual=True, may_batch_for_risk=""),
        delegation_default=DelegationPolicy(may_delegate=False),
        exception_policy=ExceptionPolicy(allow_exceptions=False, expiry_hours=24),
        project_simulate_only={},
        pack_may_override_defaults={},
        active_preset=PRESET_STRICT_MANUAL,
    )


def _preset_supervised_daily_operator() -> HumanPolicyConfig:
    return HumanPolicyConfig(
        action_class_policies=_base_action_policies(),
        approval_defaults=ApprovalRequirementPolicy(always_manual=True, may_batch_for_risk="low"),
        delegation_default=DelegationPolicy(may_delegate=False),
        exception_policy=ExceptionPolicy(allow_exceptions=False, expiry_hours=24),
        project_simulate_only={},
        pack_may_override_defaults={},
        active_preset=PRESET_SUPERVISED_DAILY_OPERATOR,
    )


def _preset_bounded_delegation() -> HumanPolicyConfig:
    return HumanPolicyConfig(
        action_class_policies=[
            ActionClassPolicy(action_class=ACTION_EXECUTE_SIMULATE, allow_auto=False, require_approval=True, allow_batch=True),
            ActionClassPolicy(action_class=ACTION_PLANNER_COMPILE, allow_auto=False, require_approval=True, allow_batch=True),
            ActionClassPolicy(action_class=ACTION_EXECUTE_TRUSTED_REAL, allow_auto=False, require_approval=True, allow_batch=False),
            ActionClassPolicy(action_class=ACTION_EXECUTOR_RESUME, allow_auto=False, require_approval=True, allow_batch=False),
            ActionClassPolicy(action_class=ACTION_DELEGATE_GOAL, allow_auto=False, require_approval=True, allow_batch=True),
            ActionClassPolicy(action_class=ACTION_USE_WORKER_LANE, allow_auto=False, require_approval=True, allow_batch=True),
            ActionClassPolicy(action_class=ACTION_ROUTING, allow_auto=True, require_approval=False, allow_batch=False),
        ],
        approval_defaults=ApprovalRequirementPolicy(always_manual=True, may_batch_for_risk="medium"),
        delegation_default=DelegationPolicy(may_delegate=True),
        exception_policy=ExceptionPolicy(allow_exceptions=True, expiry_hours=24),
        project_simulate_only={},
        pack_may_override_defaults={},
        active_preset=PRESET_BOUNDED_DELEGATION,
    )


def _preset_demo_mode() -> HumanPolicyConfig:
    return HumanPolicyConfig(
        action_class_policies=[
            ActionClassPolicy(action_class=ACTION_EXECUTE_SIMULATE, allow_auto=True, require_approval=False, allow_batch=True),
            ActionClassPolicy(action_class=ACTION_PLANNER_COMPILE, allow_auto=True, require_approval=False, allow_batch=True),
            ActionClassPolicy(action_class=ACTION_EXECUTE_TRUSTED_REAL, allow_auto=False, require_approval=True, allow_batch=True),
            ActionClassPolicy(action_class=ACTION_EXECUTOR_RESUME, allow_auto=False, require_approval=True, allow_batch=True),
            ActionClassPolicy(action_class=ACTION_DELEGATE_GOAL, allow_auto=False, require_approval=True, allow_batch=True),
            ActionClassPolicy(action_class=ACTION_USE_WORKER_LANE, allow_auto=False, require_approval=True, allow_batch=True),
            ActionClassPolicy(action_class=ACTION_ROUTING, allow_auto=True, require_approval=False, allow_batch=False),
        ],
        approval_defaults=ApprovalRequirementPolicy(always_manual=False, may_batch_for_risk="medium"),
        delegation_default=DelegationPolicy(may_delegate=True),
        exception_policy=ExceptionPolicy(allow_exceptions=True, expiry_hours=24),
        project_simulate_only={},
        pack_may_override_defaults={},
        active_preset=PRESET_DEMO_MODE,
    )


def _preset_rollout_safe() -> HumanPolicyConfig:
    return HumanPolicyConfig(
        action_class_policies=_base_action_policies(),
        approval_defaults=ApprovalRequirementPolicy(always_manual=True, may_batch_for_risk="low"),
        delegation_default=DelegationPolicy(may_delegate=False),
        exception_policy=ExceptionPolicy(allow_exceptions=False, expiry_hours=24),
        project_simulate_only={},
        pack_may_override_defaults={},
        active_preset=PRESET_ROLLOUT_SAFE,
    )


def _get_preset_config(name: str) -> HumanPolicyConfig | None:
    if name == PRESET_STRICT_MANUAL:
        return _preset_strict_manual()
    if name == PRESET_SUPERVISED_DAILY_OPERATOR:
        return _preset_supervised_daily_operator()
    if name == PRESET_BOUNDED_DELEGATION:
        return _preset_bounded_delegation()
    if name == PRESET_DEMO_MODE:
        return _preset_demo_mode()
    if name == PRESET_ROLLOUT_SAFE:
        return _preset_rollout_safe()
    return None


def get_preset_config(preset_name: str) -> HumanPolicyConfig | None:
    """Return full HumanPolicyConfig for a preset, or None if unknown."""
    return _get_preset_config(preset_name)


def list_presets() -> list[dict[str, Any]]:
    """Return list of preset id, description for board/CLI."""
    return [
        {"id": n, "description": PRESET_DESCRIPTIONS.get(n, "")}
        for n in PRESET_NAMES
    ]


def apply_preset(
    preset_name: str,
    repo_root: Path | str | None = None,
) -> HumanPolicyConfig | None:
    """Apply a preset: write its config to policy_config.json and return it. Returns None if unknown preset."""
    config = get_preset_config(preset_name)
    if config is None:
        return None
    save_policy_config(config, repo_root)
    return config


def get_trust_mode_explanation(
    preset_name: str | None = None,
    repo_root: Path | str | None = None,
) -> list[str]:
    """
    Return human-readable trust-mode explanation.
    If preset_name is given, explain that preset; else explain current config (from active_preset or 'custom').
    """
    if preset_name:
        config = get_preset_config(preset_name)
        if not config:
            return [f"Unknown preset: {preset_name}"]
        label = preset_name
    else:
        config = load_policy_config(repo_root)
        label = config.active_preset or "custom"

    lines: list[str] = []
    lines.append(f"Trust mode: {label}")
    lines.append("")
    # Approval defaults
    a = config.approval_defaults
    lines.append("Approval defaults:")
    lines.append(f"  always_manual: {a.always_manual}")
    lines.append(f"  may_batch_for_risk: {a.may_batch_for_risk or '(none)'}")
    lines.append("")
    # Delegation
    d = config.delegation_default
    lines.append("Delegation:")
    lines.append(f"  may_delegate: {d.may_delegate}")
    lines.append("")
    # Simulate vs trusted-real posture (from action-class policies)
    execute_real = next((p for p in config.action_class_policies if p.action_class == ACTION_EXECUTE_TRUSTED_REAL), None)
    execute_sim = next((p for p in config.action_class_policies if p.action_class == ACTION_EXECUTE_SIMULATE), None)
    lines.append("Simulate vs trusted-real posture:")
    if execute_sim:
        lines.append(f"  execute_simulate: require_approval={execute_sim.require_approval} allow_auto={execute_sim.allow_auto} allow_batch={execute_sim.allow_batch}")
    if execute_real:
        lines.append(f"  execute_trusted_real: require_approval={execute_real.require_approval} allow_auto={execute_real.allow_auto} allow_batch={execute_real.allow_batch}")
    lines.append("")
    # Pack / worker-lane restrictions
    delegate_goal = next((p for p in config.action_class_policies if p.action_class == ACTION_DELEGATE_GOAL), None)
    worker_lane = next((p for p in config.action_class_policies if p.action_class == ACTION_USE_WORKER_LANE), None)
    lines.append("Pack / worker-lane restrictions:")
    lines.append(f"  pack_may_override_defaults: {list(config.pack_may_override_defaults.keys()) or '(none)'}")
    if delegate_goal:
        lines.append(f"  delegate_goal: require_approval={delegate_goal.require_approval} allow_batch={delegate_goal.allow_batch}")
    if worker_lane:
        lines.append(f"  use_worker_lane: require_approval={worker_lane.require_approval} allow_batch={worker_lane.allow_batch}")
    if config.blocked_actions:
        blocked = []
        for b in config.blocked_actions:
            blocked.extend(b.blocked_action_classes)
        lines.append(f"  blocked_action_classes: {blocked}")
    lines.append("")
    lines.append("Project simulate_only (project_id -> must stay simulate):")
    lines.append(f"  {list(config.project_simulate_only.keys()) or '(none)'}")
    return lines
