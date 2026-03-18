"""
M40E–M40H: Tests for production deployment bundle — model, validation, upgrade path, rollback, recovery report.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from workflow_dataset.deploy_bundle.models import (
    ProductionDeploymentBundle,
    BundleContents,
    DeploymentHealthSummary,
)
from workflow_dataset.deploy_bundle.registry import (
    get_deployment_bundle,
    list_deployment_bundle_ids,
    BUILTIN_DEPLOYMENT_BUNDLES,
)
from workflow_dataset.deploy_bundle.store import get_active_bundle, set_active_bundle, get_deploy_bundle_dir
from workflow_dataset.deploy_bundle.packaging import build_bundle_manifest, write_bundle_manifest
from workflow_dataset.deploy_bundle.validation import validate_bundle, BundleValidationResult
from workflow_dataset.deploy_bundle.upgrade_rollback import (
    get_supported_upgrade_path,
    get_rollback_readiness,
    get_risky_upgrade_warnings,
)
from workflow_dataset.deploy_bundle.recovery_report import build_recovery_report
from workflow_dataset.deploy_bundle.health import build_deployment_health_summary
from workflow_dataset.deploy_bundle.profiles import (
    get_deployment_profile,
    list_deployment_profile_ids,
    BUILTIN_DEPLOYMENT_PROFILES,
)
from workflow_dataset.deploy_bundle.maintenance_modes import (
    get_maintenance_mode,
    list_maintenance_mode_ids,
    build_maintenance_mode_report,
    BUILTIN_MAINTENANCE_MODES,
)
from workflow_dataset.deploy_bundle.store import set_deployment_profile, set_maintenance_mode
from workflow_dataset.deploy_bundle.models import (
    PROFILE_CAREFUL_PRODUCTION_CUT,
    MODE_SAFE_PAUSE,
)


def test_bundle_model() -> None:
    bundle = get_deployment_bundle("founder_operator_prod")
    assert bundle is not None
    assert bundle.bundle_id == "founder_operator_prod"
    assert bundle.curated_pack_id == "founder_operator_core"
    assert bundle.contents.required_packs.value_pack_id == "founder_ops_plus"
    assert "supervised_operator" in bundle.contents.allowed_trust_preset_ids
    assert bundle.supported_rollback_path.supported
    assert len(bundle.recovery_posture.applicable_recovery_case_ids) >= 1
    d = bundle.to_dict()
    assert d["bundle_id"] == "founder_operator_prod"
    assert "contents" in d and "supported_upgrade_path" in d


def test_bundle_validation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        result = validate_bundle("founder_operator_prod", repo_root=root)
        assert result.bundle_id == "founder_operator_prod"
        assert isinstance(result.passed, bool)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
    result_invalid = validate_bundle("nonexistent_bundle_xyz", repo_root=Path("/nonexistent"))
    assert not result_invalid.passed
    assert any("not found" in e.lower() for e in result_invalid.errors)


def test_upgrade_path() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        out = get_supported_upgrade_path("founder_operator_prod", repo_root=root)
        assert out.get("bundle_id") == "founder_operator_prod"
        assert "supported_upgrade_path" in out
        assert "current_version" in out
        assert "can_proceed" in out
    out_bad = get_supported_upgrade_path("nonexistent", repo_root=root)
    assert out_bad.get("error")
    assert out_bad.get("supported") is False


def test_rollback_readiness() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        out = get_rollback_readiness("founder_operator_prod", repo_root=root)
        assert out.get("bundle_id") == "founder_operator_prod"
        assert "supported_rollback_path" in out
        assert "ready" in out
        assert "rollback_hints" in out


def test_recovery_report() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        report = build_recovery_report("founder_operator_prod", repo_root=root)
        assert report.get("bundle_id") == "founder_operator_prod"
        assert "recovery_posture" in report
        assert "applicable_recovery_cases" in report
        assert "vertical_playbook_recovery_ref" in report
        assert "founder_operator" in report.get("vertical_playbook_recovery_ref", "")


def test_invalid_bundle() -> None:
    bundle = get_deployment_bundle("nonexistent")
    assert bundle is None
    ids = list_deployment_bundle_ids()
    assert "founder_operator_prod" in ids
    assert len(ids) == len(BUILTIN_DEPLOYMENT_BUNDLES)
    manifest = build_bundle_manifest("nonexistent")
    assert manifest.get("error")
    with tempfile.TemporaryDirectory() as tmp:
        with pytest.raises(ValueError):
            write_bundle_manifest("nonexistent", repo_root=Path(tmp))


def test_build_manifest_and_active() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        manifest = build_bundle_manifest("founder_operator_prod", repo_root=root)
        assert "error" not in manifest
        assert manifest.get("bundle_id") == "founder_operator_prod"
        path = write_bundle_manifest("founder_operator_prod", repo_root=root)
        assert path.exists()
        set_active_bundle("founder_operator_prod", repo_root=root)
        active = get_active_bundle(repo_root=root)
        assert active.get("active_bundle_id") == "founder_operator_prod"


def test_deployment_health_summary() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        health = build_deployment_health_summary("founder_operator_prod", repo_root=root)
        assert health.bundle_id == "founder_operator_prod"
        assert isinstance(health.validation_passed, bool)
        assert isinstance(health.upgrade_readiness, bool)
        assert isinstance(health.rollback_readiness, bool)
        assert isinstance(health.blocked_deployment_risks, list)
        d = health.to_dict()
        assert "validation_passed" in d and "blocked_deployment_risks" in d


# ----- M40H.1 Deployment profiles + maintenance modes -----


def test_deployment_profile() -> None:
    p = get_deployment_profile(PROFILE_CAREFUL_PRODUCTION_CUT)
    assert p is not None
    assert p.profile_id == PROFILE_CAREFUL_PRODUCTION_CUT
    assert "production" in p.name.lower() or "careful" in p.name.lower()
    assert p.pause_guidance
    assert p.repair_guidance
    assert "founder_operator_prod" in p.recommended_bundle_ids
    d = p.to_dict()
    assert d["profile_id"] == PROFILE_CAREFUL_PRODUCTION_CUT
    ids = list_deployment_profile_ids()
    assert PROFILE_CAREFUL_PRODUCTION_CUT in ids
    assert "demo" in ids
    assert len(ids) == len(BUILTIN_DEPLOYMENT_PROFILES)


def test_maintenance_mode() -> None:
    m = get_maintenance_mode(MODE_SAFE_PAUSE)
    assert m is not None
    assert m.mode_id == MODE_SAFE_PAUSE
    assert m.blocks_real_run
    assert m.operator_guidance_pause
    assert m.operator_guidance_repair
    d = m.to_dict()
    assert d["mode_id"] == MODE_SAFE_PAUSE
    ids = list_maintenance_mode_ids()
    assert "upgrade" in ids
    assert "recovery" in ids
    assert "audit_review" in ids
    assert "safe_pause" in ids
    assert len(ids) == len(BUILTIN_MAINTENANCE_MODES)


def test_maintenance_mode_report() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        set_deployment_profile(PROFILE_CAREFUL_PRODUCTION_CUT, repo_root=root)
        set_maintenance_mode(MODE_SAFE_PAUSE, repo_root=root)
        r = build_maintenance_mode_report(repo_root=root)
        assert r.active_profile_id == PROFILE_CAREFUL_PRODUCTION_CUT
        assert r.active_maintenance_mode_id == MODE_SAFE_PAUSE
        assert r.should_pause is True
        assert "profile" in r.to_dict()
        assert "maintenance_mode" in r.to_dict()
        assert r.operator_guidance_summary or r.pause_reason
