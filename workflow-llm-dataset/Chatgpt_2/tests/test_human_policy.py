"""
M28I–M28L: Tests for human policy engine and override board.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.human_policy.models import (
    HumanPolicyConfig,
    ActionClassPolicy,
    ApprovalRequirementPolicy,
    DelegationPolicy,
    OverrideRecord,
    SCOPE_GLOBAL,
    SCOPE_PROJECT,
    ACTION_EXECUTE_SIMULATE,
    ACTION_EXECUTE_TRUSTED_REAL,
)
from workflow_dataset.human_policy.store import (
    get_policy_dir,
    load_policy_config,
    save_policy_config,
    load_overrides,
    save_overrides,
)
from workflow_dataset.human_policy.evaluate import evaluate, PolicyEvalResult
from workflow_dataset.human_policy.board import (
    list_active_effects,
    list_overrides,
    apply_override,
    revoke_override,
    explain_why_blocked,
    explain_why_allowed,
)


def test_policy_config_roundtrip(tmp_path: Path) -> None:
    config = HumanPolicyConfig(
        action_class_policies=[
            ActionClassPolicy(action_class=ACTION_EXECUTE_SIMULATE, allow_auto=False, require_approval=True, allow_batch=True),
        ],
        approval_defaults=ApprovalRequirementPolicy(always_manual=True, may_batch_for_risk="low"),
        delegation_default=DelegationPolicy(may_delegate=False),
        project_simulate_only={"founder_case_alpha": True},
    )
    save_policy_config(config, tmp_path)
    loaded = load_policy_config(tmp_path)
    assert len(loaded.action_class_policies) >= 1
    assert loaded.approval_defaults.always_manual is True
    assert loaded.project_simulate_only.get("founder_case_alpha") is True


def test_evaluate_defaults(tmp_path: Path) -> None:
    result = evaluate(action_class=ACTION_EXECUTE_TRUSTED_REAL, repo_root=tmp_path)
    assert result.is_always_manual is True
    assert result.blocked is False
    assert result.may_delegate is False


def test_evaluate_project_simulate_only(tmp_path: Path) -> None:
    config = load_policy_config(tmp_path)
    config.project_simulate_only["proj_1"] = True
    save_policy_config(config, tmp_path)
    result = evaluate(action_class=ACTION_EXECUTE_SIMULATE, project_id="proj_1", repo_root=tmp_path)
    assert result.simulate_only is True


def test_override_apply_and_list(tmp_path: Path) -> None:
    rec = apply_override(scope=SCOPE_PROJECT, scope_id="founder_case_alpha", rule_key="manual_only", rule_value=False, reason="test", repo_root=tmp_path)
    assert rec.override_id.startswith("ov_")
    overrides = list_overrides(active_only=True, repo_root=tmp_path)
    assert len(overrides) == 1
    assert overrides[0].rule_key == "manual_only"
    assert overrides[0].rule_value is False


def test_override_revoke(tmp_path: Path) -> None:
    rec = apply_override(scope=SCOPE_GLOBAL, scope_id="", rule_key="may_delegate", rule_value=True, repo_root=tmp_path)
    revoked = revoke_override(rec.override_id, tmp_path)
    assert revoked is not None
    assert revoked.revoked_at != ""
    active = list_overrides(active_only=True, repo_root=tmp_path)
    assert len(active) == 0


def test_explain_blocked(tmp_path: Path) -> None:
    from workflow_dataset.human_policy.models import BlockedActionPolicy
    config = load_policy_config(tmp_path)
    config.blocked_actions.append(
        BlockedActionPolicy(scope=SCOPE_GLOBAL, scope_id="", blocked_action_classes=[ACTION_EXECUTE_TRUSTED_REAL])
    )
    save_policy_config(config, tmp_path)
    lines = explain_why_blocked(action_class=ACTION_EXECUTE_TRUSTED_REAL, repo_root=tmp_path)
    assert len(lines) >= 1
    assert "blocked" in lines[0].lower() or "blocked_actions" in lines[0].lower()


def test_explain_allowed(tmp_path: Path) -> None:
    lines = explain_why_allowed(action_class=ACTION_EXECUTE_SIMULATE, repo_root=tmp_path)
    assert len(lines) >= 1
    assert "action_class" in lines[0]


def test_list_active_effects(tmp_path: Path) -> None:
    effects = list_active_effects(project_id="", pack_id="", repo_root=tmp_path)
    assert len(effects) >= 1
    keys = [e.effect_key for e in effects]
    assert "always_manual" in keys or "may_batch_for_risk" in keys


def test_override_record_is_active() -> None:
    r = OverrideRecord(override_id="ov_1", revoked_at="")
    assert r.is_active() is True
    r.revoked_at = "2025-01-01T00:00:00Z"
    assert r.is_active() is False


# M28L.1 Presets + trust modes
from workflow_dataset.human_policy.presets import (
    PRESET_NAMES,
    list_presets,
    get_preset_config,
    apply_preset,
    get_trust_mode_explanation,
    PRESET_STRICT_MANUAL,
    PRESET_DEMO_MODE,
)


def test_list_presets() -> None:
    presets = list_presets()
    assert len(presets) == len(PRESET_NAMES)
    ids = [p["id"] for p in presets]
    assert PRESET_STRICT_MANUAL in ids
    assert PRESET_DEMO_MODE in ids
    assert all(p.get("description") for p in presets)


def test_get_preset_config() -> None:
    for name in PRESET_NAMES:
        config = get_preset_config(name)
        assert config is not None
        assert config.active_preset == name
    assert get_preset_config("unknown_preset") is None


def test_apply_preset(tmp_path: Path) -> None:
    config = apply_preset(PRESET_STRICT_MANUAL, tmp_path)
    assert config is not None
    assert config.active_preset == PRESET_STRICT_MANUAL
    assert config.approval_defaults.always_manual is True
    assert config.delegation_default.may_delegate is False
    loaded = load_policy_config(tmp_path)
    assert loaded.active_preset == PRESET_STRICT_MANUAL


def test_trust_mode_explanation_preset() -> None:
    lines = get_trust_mode_explanation(preset_name=PRESET_STRICT_MANUAL)
    assert any("strict_manual" in line for line in lines)
    assert any("Approval" in line for line in lines)
    assert any("Delegation" in line for line in lines)
    assert any("always_manual" in line for line in lines)
    assert any("may_delegate" in line for line in lines)


def test_trust_mode_explanation_current(tmp_path: Path) -> None:
    apply_preset(PRESET_DEMO_MODE, tmp_path)
    lines = get_trust_mode_explanation(preset_name=None, repo_root=tmp_path)
    assert any("demo_mode" in line or "Trust mode" in line for line in lines)
    assert any("may_delegate" in line for line in lines)
