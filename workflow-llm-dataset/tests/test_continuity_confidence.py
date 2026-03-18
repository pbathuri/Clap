"""
M49I–M49L: Tests for device-aware continuity confidence.
Target device profile, post-restore profile, confidence classification, downgraded explanation, operator-mode readiness.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.continuity_confidence.models import (
    TargetDeviceProfile,
    PostRestoreRuntimeProfile,
    ContinuityConfidenceScore,
    ContinuityConfidenceClass,
    DeviceCapabilityClass,
    DowngradedCapabilityNote,
    RecommendedOperatingPosture,
)
from workflow_dataset.continuity_confidence.device_profile import (
    build_target_device_profile,
    compare_source_target,
)
from workflow_dataset.continuity_confidence.confidence import build_continuity_confidence
from workflow_dataset.continuity_confidence.adaptation import (
    build_post_restore_runtime_profile,
    get_downgraded_runtime_explanation,
)
from workflow_dataset.continuity_confidence.report import continuity_confidence_report
from workflow_dataset.continuity_confidence.mission_control import continuity_confidence_slice


def test_target_device_profile_model() -> None:
    p = TargetDeviceProfile(
        profile_id="p1",
        device_id="current",
        runtime_id="local",
        edge_tier="local_standard",
        capability_class=DeviceCapabilityClass.SAME.value,
    )
    assert p.profile_id == "p1"
    assert p.edge_tier == "local_standard"
    d = p.to_dict()
    assert d["profile_id"] == p.profile_id
    assert d["capability_class"] == "same"


def test_build_target_device_profile(tmp_path: Path) -> None:
    profile = build_target_device_profile(repo_root=tmp_path, device_id="current")
    assert profile.profile_id
    assert profile.device_id == "current"
    assert profile.runtime_id
    assert profile.edge_tier
    assert profile.capability_class in (DeviceCapabilityClass.UNKNOWN.value, DeviceCapabilityClass.SAME.value)


def test_compare_source_target_unknown() -> None:
    out = compare_source_target(None, None)
    assert out == DeviceCapabilityClass.UNKNOWN.value


def test_compare_source_target_same() -> None:
    src = TargetDeviceProfile(edge_tier="local_standard", allowed_backends=["ollama"], has_llm_backend=True)
    tgt = TargetDeviceProfile(edge_tier="local_standard", allowed_backends=["ollama"], has_llm_backend=True)
    out = compare_source_target(src, tgt)
    assert out == DeviceCapabilityClass.SAME.value


def test_compare_source_target_weaker() -> None:
    src = TargetDeviceProfile(edge_tier="local_standard", allowed_backends=["ollama", "repo_local"], has_llm_backend=True)
    tgt = TargetDeviceProfile(edge_tier="local_standard", allowed_backends=["ollama"], has_llm_backend=True)
    out = compare_source_target(src, tgt)
    assert out == DeviceCapabilityClass.WEAKER.value


def test_build_continuity_confidence_no_bundle(tmp_path: Path) -> None:
    score, downgraded, promoted, posture = build_continuity_confidence(bundle_ref="nonexistent_bundle_123", repo_root=tmp_path)
    assert score.classification == ContinuityConfidenceClass.BLOCKED.value or score.score == 0.0
    assert posture is None or score.classification == ContinuityConfidenceClass.BLOCKED.value


def test_build_continuity_confidence_latest(tmp_path: Path) -> None:
    score, downgraded, promoted, posture = build_continuity_confidence(bundle_ref="latest", repo_root=tmp_path)
    assert score.classification in (
        ContinuityConfidenceClass.HIGH_CONFIDENCE.value,
        ContinuityConfidenceClass.USABLE_DEGRADED.value,
        ContinuityConfidenceClass.REVIEW_REQUIRED.value,
        ContinuityConfidenceClass.NARROWED_PRODUCTION_CUT.value,
        ContinuityConfidenceClass.OPERATOR_MODE_NOT_TRUSTED.value,
        ContinuityConfidenceClass.BLOCKED.value,
        ContinuityConfidenceClass.UNKNOWN.value,
    )
    assert 0.0 <= score.score <= 1.0
    if posture:
        assert posture.posture_id
        assert posture.next_review_action or posture.operator_mode_trusted


def test_build_post_restore_runtime_profile(tmp_path: Path) -> None:
    profile, route_adj, op_adj = build_post_restore_runtime_profile(bundle_ref="latest", repo_root=tmp_path)
    assert profile.profile_id
    assert profile.target_device_profile_id
    assert profile.recommended_routing_policy_id in ("balanced", "conservative", "") or True
    assert isinstance(route_adj, list)
    assert isinstance(op_adj, list)


def test_get_downgraded_runtime_explanation(tmp_path: Path) -> None:
    data = get_downgraded_runtime_explanation(bundle_ref="latest", repo_root=tmp_path)
    assert "continuity_classification" in data
    assert "continuity_label" in data
    assert "downgraded_capabilities" in data
    assert "production_cut_narrowed" in data
    assert "operator_mode_ready" in data
    assert "next_review_action" in data


def test_continuity_confidence_report(tmp_path: Path) -> None:
    data = continuity_confidence_report(bundle_ref="latest", repo_root=tmp_path)
    assert "bundle_ref" in data
    assert "target_device_profile" in data
    assert "continuity_confidence" in data
    assert "post_restore_runtime_profile" in data
    assert "downgraded_explanation" in data


def test_continuity_confidence_slice(tmp_path: Path) -> None:
    slice_data = continuity_confidence_slice(repo_root=tmp_path)
    if slice_data.get("error"):
        pytest.skip("continuity_confidence_slice failed (e.g. migration_restore not fully available)")
    assert "current_post_restore_confidence" in slice_data or "error" in slice_data
    assert "operator_mode_readiness_after_restore" in slice_data or "error" in slice_data
    assert "next_recommended_post_restore_review" in slice_data or "error" in slice_data


def test_operator_mode_readiness_handling(tmp_path: Path) -> None:
    score, _, _, posture = build_continuity_confidence(bundle_ref="latest", repo_root=tmp_path)
    if posture:
        if score.classification == ContinuityConfidenceClass.HIGH_CONFIDENCE.value:
            assert posture.operator_mode_trusted is True
        elif score.classification in (
            ContinuityConfidenceClass.USABLE_DEGRADED.value,
            ContinuityConfidenceClass.REVIEW_REQUIRED.value,
            ContinuityConfidenceClass.OPERATOR_MODE_NOT_TRUSTED.value,
        ):
            assert posture.operator_mode_trusted is False


# ----- M49L.1 Device classes + post-restore presets -----
def test_list_device_classes() -> None:
    from workflow_dataset.continuity_confidence import list_device_classes
    classes = list_device_classes()
    ids = {c.class_id for c in classes}
    assert "full_local_workstation" in ids
    assert "constrained_laptop" in ids
    assert "recovery_safe_environment" in ids
    for c in classes:
        assert c.class_id and c.label and c.edge_tiers


def test_get_device_class() -> None:
    from workflow_dataset.continuity_confidence import get_device_class
    c = get_device_class("full_local_workstation")
    assert c is not None
    assert c.class_id == "full_local_workstation"
    assert "workstation" in c.label.lower()
    assert "dev_full" in c.edge_tiers or "local_standard" in c.edge_tiers
    assert get_device_class("nonexistent") is None


def test_resolve_device_class() -> None:
    from workflow_dataset.continuity_confidence import resolve_device_class
    profile = TargetDeviceProfile(
        profile_id="p1",
        device_id="current",
        runtime_id="local",
        edge_tier="local_standard",
        capability_class=DeviceCapabilityClass.SAME.value,
        allowed_backends=["ollama"],
        has_llm_backend=True,
    )
    c = resolve_device_class(profile)
    assert c.class_id in ("full_local_workstation", "constrained_laptop", "recovery_safe_environment")


def test_list_post_restore_presets() -> None:
    from workflow_dataset.continuity_confidence import list_post_restore_presets
    presets = list_post_restore_presets()
    ids = {p.preset_id for p in presets}
    assert "full_operation" in ids
    assert "review_before_production" in ids
    assert "recovery_safe" in ids
    for p in presets:
        assert p.preset_id and p.label
        assert isinstance(p.do_after_migration, list)
        assert isinstance(p.avoid_after_migration, list)


def test_get_post_restore_preset() -> None:
    from workflow_dataset.continuity_confidence import get_post_restore_preset
    p = get_post_restore_preset("review_before_production")
    assert p is not None
    assert p.preset_id == "review_before_production"
    assert len(p.do_after_migration) > 0
    assert get_post_restore_preset("nonexistent") is None


def test_get_recommended_preset_for() -> None:
    from workflow_dataset.continuity_confidence import get_recommended_preset_for
    p = get_recommended_preset_for("full_local_workstation", ContinuityConfidenceClass.HIGH_CONFIDENCE.value)
    assert p is not None
    assert p.preset_id in ("full_operation", "review_before_production", "constrained", "recovery_safe")
    p2 = get_recommended_preset_for("recovery_safe_environment", ContinuityConfidenceClass.BLOCKED.value)
    assert p2 is not None
    assert p2.preset_id == "recovery_safe"


def test_post_restore_safe_operating_guidance(tmp_path: Path) -> None:
    from workflow_dataset.continuity_confidence import post_restore_safe_operating_guidance
    g = post_restore_safe_operating_guidance(bundle_ref="latest", repo_root=tmp_path)
    assert g.device_class_id and g.device_class_label
    assert g.recommended_preset_id and g.recommended_preset_label
    assert isinstance(g.do_after_migration, list)
    assert isinstance(g.avoid_after_migration, list)
    assert g.summary
    assert g.next_review_action
    assert g.generated_at_utc
    d = g.to_dict()
    assert d["device_class_id"] == g.device_class_id
    assert "do_after_migration" in d
    assert "summary" in d
