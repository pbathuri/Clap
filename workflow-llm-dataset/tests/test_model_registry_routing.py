"""
M42A–M42D: Tests for local model registry and task-aware runtime routing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.runtime_mesh.model_catalog import (
    load_model_catalog,
    get_model_info,
    list_models_by_capability,
    ModelEntry,
)
from workflow_dataset.runtime_mesh.routing import (
    route_for_task,
    availability_check,
    build_fallback_report,
    TASK_FAMILIES,
    TASK_FAMILY_TO_CLASS,
)


def test_registry_loads_entries():
    """Registry loads model entries with M42 fields."""
    catalog = load_model_catalog(None)
    assert len(catalog) >= 1
    m = catalog[0]
    assert m.model_id
    assert hasattr(m, "task_families")
    assert hasattr(m, "production_safe")
    assert hasattr(m, "fallback_model_id")


def test_registry_entry_has_task_families_and_safe_flags():
    """At least one seed entry has task_families and production_safe."""
    catalog = load_model_catalog(None)
    with_families = [m for m in catalog if m.task_families]
    assert len(with_families) >= 1
    assert all(hasattr(m, "production_safe") for m in catalog)


def test_get_model_info():
    """get_model_info returns entry or None."""
    catalog = load_model_catalog(None)
    first_id = catalog[0].model_id
    m = get_model_info(first_id, None)
    assert m is not None
    assert m.model_id == first_id
    assert get_model_info("nonexistent_model_xyz_123", None) is None


def test_route_for_task_returns_structure():
    """route_for_task returns dict with primary_model_id, fallback_chain, explanation, is_degraded."""
    r = route_for_task("planning", repo_root=Path("/nonexistent_repo"))
    assert "task_family" in r
    assert r["task_family"] == "planning"
    assert "primary_model_id" in r
    assert "primary_backend_id" in r
    assert "fallback_chain" in r
    assert "explanation" in r
    assert "is_degraded" in r
    assert "task_class" in r


def test_route_for_task_maps_family_to_class():
    """Task family maps to task_class via TASK_FAMILY_TO_CLASS."""
    r = route_for_task("summarization", repo_root=Path("/tmp"))
    assert r.get("task_class") == "desktop_copilot"
    r2 = route_for_task("vertical_workflow", repo_root=Path("/tmp"))
    assert r2.get("task_class") == "codebase_task"


def test_availability_check_returns_backends_and_task_families():
    """availability_check returns available/missing backends and task_families_with_route/degraded."""
    out = availability_check(Path("/tmp"))
    assert "available_backend_ids" in out
    assert "missing_backend_ids" in out
    assert "task_families_with_route" in out
    assert "task_families_degraded" in out


def test_fallback_report_has_per_task_family_and_recommended_actions():
    """build_fallback_report returns per_task_family and recommended_actions."""
    out = build_fallback_report(Path("/tmp"))
    assert "availability" in out
    assert "per_task_family" in out
    assert "recommended_actions" in out
    assert "summary" in out
    assert len(out["per_task_family"]) >= len(TASK_FAMILIES) or len(out["per_task_family"]) >= 1


def test_production_safe_filtering():
    """route_for_task with require_production_safe prefers production_safe models."""
    r = route_for_task("planning", trust_posture="production", require_production_safe=True, repo_root=Path("/tmp"))
    assert "primary_model_id" in r
    assert "is_degraded" in r


def test_invalid_task_family_uses_default_class():
    """Unknown task family falls back to desktop_copilot task_class."""
    r = route_for_task("nonexistent_family_xyz", repo_root=Path("/tmp"))
    assert r.get("task_class") == "desktop_copilot"


def test_missing_runtime_degraded():
    """When repo has no backends available, route can be degraded."""
    r = route_for_task("planning", repo_root=Path("/nonexistent_repo"))
    assert "is_degraded" in r
    assert "degraded_route" in r


# ----- M42D.1 Vertical profiles, routing policies, route outcome -----
def test_vertical_profiles_and_routing_policies():
    """Vertical profiles and routing policies are listable and gettable."""
    from workflow_dataset.runtime_mesh.profiles_and_policies import (
        list_vertical_profiles,
        list_routing_policies,
        get_vertical_profile,
        get_routing_policy,
    )
    vprofiles = list_vertical_profiles()
    assert len(vprofiles) >= 1
    assert get_vertical_profile("default") is not None
    assert get_vertical_profile("council_eval") is not None
    policies = list_routing_policies()
    assert len(policies) >= 1
    assert get_routing_policy("conservative") is not None
    assert get_routing_policy("balanced") is not None
    assert get_routing_policy("production_safe") is not None


def test_route_returns_outcome_and_reason_why():
    """route_for_task returns route_outcome and reason_why (preferred/allowed/degraded/blocked)."""
    from workflow_dataset.runtime_mesh.routing import (
        ROUTE_OUTCOME_PREFERRED,
        ROUTE_OUTCOME_ALLOWED,
        ROUTE_OUTCOME_DEGRADED,
        ROUTE_OUTCOME_BLOCKED,
    )
    r = route_for_task("planning", repo_root=Path("/tmp"))
    assert "route_outcome" in r
    assert r["route_outcome"] in (ROUTE_OUTCOME_PREFERRED, ROUTE_OUTCOME_ALLOWED, ROUTE_OUTCOME_DEGRADED, ROUTE_OUTCOME_BLOCKED)
    assert "reason_why" in r
    assert isinstance(r["reason_why"], str)


def test_route_with_policy_and_vertical():
    """route_for_task accepts vertical_id and routing_policy_id."""
    r = route_for_task("council", vertical_id="council_eval", routing_policy_id="conservative", repo_root=Path("/tmp"))
    assert r.get("vertical_id") in ("council_eval", "")
    assert r.get("routing_policy_id") in ("conservative", "balanced", "")
    assert "route_outcome" in r


def test_routing_policy_report():
    """build_routing_policy_report returns vertical_profile, routing_policy, effect_summary."""
    from workflow_dataset.runtime_mesh.profiles_and_policies import build_routing_policy_report
    out = build_routing_policy_report(vertical_id="default", policy_id="conservative")
    assert "vertical_profile" in out
    assert "routing_policy" in out
    assert "effect_summary" in out
    assert "conservative" in out.get("effect_summary", "")
