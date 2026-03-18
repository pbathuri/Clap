"""
M49A–M49D: Tests for portable continuity bundle — create, inspect, validate, components, explain.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.continuity_bundle import (
    create_bundle,
    inspect_bundle,
    validate_bundle,
    list_components,
    get_portability_boundaries,
    explain_component,
    continuity_bundle_slice,
    get_component,
    list_profiles,
    get_profile,
    resolve_profile_components,
    list_sensitivity_policies,
    get_sensitivity_policy,
    apply_policy_to_boundaries,
    get_portability_report,
    format_portability_report_text,
)
from workflow_dataset.continuity_bundle.models import TransferClass
from workflow_dataset.continuity_bundle.profiles import PROFILE_PERSONAL_CORE, PROFILE_MAINTENANCE_SAFE
from workflow_dataset.continuity_bundle.sensitivity_policies import POLICY_EXCLUDE_SENSITIVE, POLICY_STRICT_SAFE_ONLY


def test_create_bundle(tmp_path: Path) -> None:
    """Bundle creation writes manifest and returns ContinuityBundle."""
    bundle = create_bundle(tmp_path)
    assert bundle.bundle_id.startswith("cb_")
    assert bundle.product_version
    assert bundle.created_at_utc
    assert len(bundle.components) >= 1
    manifest_path = tmp_path / "data/local/continuity_bundle/bundles" / bundle.bundle_id / "manifest.json"
    assert manifest_path.exists()
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert raw["bundle_id"] == bundle.bundle_id
    assert "components" in raw


def test_inspect_bundle_latest(tmp_path: Path) -> None:
    """Inspect latest loads the most recent bundle."""
    create_bundle(tmp_path)
    bundle = inspect_bundle("latest", tmp_path)
    assert bundle is not None
    assert bundle.bundle_id.startswith("cb_")
    assert len(bundle.components) >= 1


def test_inspect_bundle_nonexistent(tmp_path: Path) -> None:
    """Inspect nonexistent bundle returns None."""
    assert inspect_bundle("nonexistent_cb_xyz", tmp_path) is None
    assert inspect_bundle("latest", tmp_path) is None


def test_validate_bundle_valid(tmp_path: Path) -> None:
    """Validate a valid bundle returns valid=True."""
    create_bundle(tmp_path)
    result = validate_bundle("latest", tmp_path)
    assert result["valid"] is True
    assert result["bundle_id"]
    assert result["component_count"] >= 1
    assert "errors" in result
    assert len(result["errors"]) == 0


def test_validate_bundle_invalid(tmp_path: Path) -> None:
    """Validate nonexistent bundle returns valid=False and errors."""
    result = validate_bundle("nonexistent_cb_xyz", tmp_path)
    assert result["valid"] is False
    assert "Bundle not found" in str(result.get("errors", []))


def test_list_components_classification(tmp_path: Path) -> None:
    """List components returns registry with transfer classes; exclude local_only by default."""
    comps = list_components(repo_root=tmp_path)
    ids = [c.component_id for c in comps]
    assert "background_queue" not in ids  # local_only excluded by default
    comps_all = list_components(include_local_only=True, repo_root=tmp_path)
    ids_all = [c.component_id for c in comps_all]
    assert "background_queue" in ids_all
    safe = [c for c in comps_all if c.transfer_class == TransferClass.SAFE_TO_TRANSFER.value]
    assert len(safe) >= 1


def test_selective_include_exclude(tmp_path: Path) -> None:
    """Create with include/exclude filters components correctly."""
    bundle_inc = create_bundle(tmp_path, include_components=["workday", "continuity_shutdown"])
    assert len(bundle_inc.components) <= 2
    assert all(c.component_id in ("workday", "continuity_shutdown") for c in bundle_inc.components)
    bundle_exc = create_bundle(tmp_path, exclude_components=["workday"])
    workday_ids = [c.component_id for c in bundle_exc.components if c.component_id == "workday"]
    assert len(workday_ids) == 0


def test_sensitive_components_in_registry(tmp_path: Path) -> None:
    """Sensitive/review components are marked in registry."""
    comps = list_components(include_local_only=True, repo_root=tmp_path)
    sensitive = [c for c in comps if c.sensitive]
    review = [c for c in comps if c.review_required]
    # production_cut, trust_contracts are transfer_with_review + sensitive
    assert any(c.component_id in ("production_cut", "trust_contracts") for c in sensitive)


def test_explain_component(tmp_path: Path) -> None:
    """Explain returns transfer_class, rationale, on_restore for known component."""
    out = explain_component("workday", tmp_path)
    assert out["found"] is True
    assert out["component_id"] == "workday"
    assert out["transfer_class"] in (TransferClass.SAFE_TO_TRANSFER.value, TransferClass.LOCAL_ONLY.value)
    assert out["rationale"]
    assert out["on_restore"]


def test_explain_component_unknown(tmp_path: Path) -> None:
    """Explain unknown component returns found=False."""
    out = explain_component("unknown_component_xyz", tmp_path)
    assert out["found"] is False
    assert "Unknown" in out.get("reason", "")


def test_portability_boundaries(tmp_path: Path) -> None:
    """get_portability_boundaries returns all transfer classes and summary."""
    boundaries = get_portability_boundaries(tmp_path)
    assert "safe_to_transfer" in boundaries
    assert "transfer_with_review" in boundaries
    assert "local_only" in boundaries
    assert "summary" in boundaries
    assert "background_queue" in boundaries.get("local_only", [])


def test_mission_control_slice(tmp_path: Path) -> None:
    """continuity_bundle_slice returns latest_bundle_id, transfer_sensitive, excluded_local_only."""
    slice_data = continuity_bundle_slice(tmp_path)
    assert "latest_bundle_id" in slice_data
    assert "transfer_sensitive_components" in slice_data
    assert "excluded_local_only" in slice_data
    assert "next_portability_review" in slice_data
    # No bundle yet
    assert slice_data["latest_bundle_id"] is None or slice_data["latest_bundle_id"].startswith("cb_")
    create_bundle(tmp_path)
    slice_after = continuity_bundle_slice(tmp_path)
    assert slice_after["latest_bundle_id"] is not None
    assert slice_after["latest_bundle_id"].startswith("cb_")


def test_no_portable_state_edge_case(tmp_path: Path) -> None:
    """Exclude everything: bundle has zero components or only excluded list."""
    reg = list_components(include_local_only=True, repo_root=tmp_path)
    all_ids = [c.component_id for c in reg]
    bundle = create_bundle(tmp_path, exclude_components=all_ids)
    assert len(bundle.components) == 0
    assert len(bundle.excluded_component_ids) == len(all_ids)
    result = validate_bundle(bundle.bundle_id, tmp_path)
    assert result["valid"] is True
    assert result["component_count"] == 0


def test_get_component(tmp_path: Path) -> None:
    """get_component returns component by id or None."""
    c = get_component("workday", tmp_path)
    assert c is not None
    assert c.component_id == "workday"
    assert get_component("nonexistent_xyz", tmp_path) is None


# ----- M49D.1 Bundle profiles + sensitivity policies + report -----


def test_list_profiles() -> None:
    """list_profiles returns at least personal_core, production_cut, maintenance_safe."""
    profiles = list_profiles()
    ids = [p.profile_id for p in profiles]
    assert "personal_core" in ids
    assert "production_cut" in ids
    assert "maintenance_safe" in ids


def test_get_profile_personal_core() -> None:
    """get_profile returns profile with exclude list for personal_core."""
    p = get_profile(PROFILE_PERSONAL_CORE)
    assert p is not None
    assert p.profile_id == "personal_core"
    assert "production_cut" in p.exclude_component_ids
    assert "trust_contracts" in p.exclude_component_ids


def test_resolve_profile_components_maintenance_safe() -> None:
    """maintenance_safe profile restricts to safe_to_transfer only."""
    all_ids = ["workday", "production_cut", "background_queue"]
    inc, exc, classes = resolve_profile_components(PROFILE_MAINTENANCE_SAFE, all_ids)
    assert classes is not None
    assert TransferClass.SAFE_TO_TRANSFER.value in classes
    assert TransferClass.TRANSFER_WITH_REVIEW.value not in classes


def test_create_bundle_with_profile(tmp_path: Path) -> None:
    """create_bundle with profile_id uses profile exclude/include/transfer_classes."""
    bundle = create_bundle(tmp_path, profile_id=PROFILE_PERSONAL_CORE)
    assert bundle.profile_id == PROFILE_PERSONAL_CORE
    comp_ids = [c.component_id for c in bundle.components]
    assert "production_cut" not in comp_ids
    assert "trust_contracts" not in comp_ids
    manifest_path = tmp_path / "data/local/continuity_bundle/bundles" / bundle.bundle_id / "manifest.json"
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert raw.get("profile_id") == PROFILE_PERSONAL_CORE


def test_inspect_bundle_includes_profile_id(tmp_path: Path) -> None:
    """inspect_bundle returns bundle with profile_id when present in manifest."""
    create_bundle(tmp_path, profile_id=PROFILE_MAINTENANCE_SAFE)
    bundle = inspect_bundle("latest", tmp_path)
    assert bundle is not None
    assert bundle.profile_id == PROFILE_MAINTENANCE_SAFE


def test_list_sensitivity_policies() -> None:
    """list_sensitivity_policies returns transfer_with_review, exclude_sensitive, strict_safe_only."""
    policies = list_sensitivity_policies()
    ids = [p.policy_id for p in policies]
    assert "transfer_with_review" in ids
    assert "exclude_sensitive" in ids
    assert "strict_safe_only" in ids


def test_apply_policy_exclude_sensitive(tmp_path: Path) -> None:
    """exclude_sensitive policy puts transfer_with_review into excluded, not portable."""
    boundaries = get_portability_boundaries(tmp_path)
    policy = get_sensitivity_policy(POLICY_EXCLUDE_SENSITIVE)
    assert policy is not None
    applied = apply_policy_to_boundaries(boundaries, policy)
    assert "production_cut" in applied["excluded"] or "trust_contracts" in applied["excluded"]
    assert applied["review_required_count"] == 0


def test_get_portability_report(tmp_path: Path) -> None:
    """get_portability_report returns portable, review_required, excluded, rebuild_only with counts."""
    report = get_portability_report(tmp_path)
    assert "portable" in report
    assert "review_required" in report
    assert "excluded" in report
    assert "rebuild_only" in report
    assert "portable_count" in report
    assert "summary" in report
    assert "sensitivity_policy_id" in report


def test_get_portability_report_strict_safe(tmp_path: Path) -> None:
    """get_portability_report with strict_safe_only has review_required_count 0."""
    report = get_portability_report(tmp_path, sensitivity_policy_id=POLICY_STRICT_SAFE_ONLY)
    assert report["review_required_count"] == 0
    assert report["sensitivity_policy_id"] == POLICY_STRICT_SAFE_ONLY


def test_format_portability_report_text(tmp_path: Path) -> None:
    """format_portability_report_text returns string with Portable, Review required, Excluded, Rebuild only."""
    report = get_portability_report(tmp_path)
    text = format_portability_report_text(report)
    assert "Portability report" in text
    assert "Portable" in text
    assert "Review required" in text
    assert "Excluded" in text
    assert "Rebuild only" in text


def test_mission_control_slice_includes_portability_report(tmp_path: Path) -> None:
    """continuity_bundle_slice includes portability_report_summary and portable/review_required/excluded counts."""
    slice_data = continuity_bundle_slice(tmp_path)
    assert "portability_report_summary" in slice_data
    assert "portable_count" in slice_data
    assert "review_required_count" in slice_data
    assert "excluded_count" in slice_data
    assert "rebuild_only_count" in slice_data
