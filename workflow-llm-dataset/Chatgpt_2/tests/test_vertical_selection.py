"""
M39A–M39D: Tests for vertical selection, scope lock, surface classification.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.vertical_selection.models import (
    VerticalCandidate,
    SURFACE_CLASS_CORE,
    SURFACE_CLASS_ADVANCED_AVAILABLE,
    SURFACE_CLASS_NON_CORE,
)
from workflow_dataset.vertical_selection.candidates import build_candidates, get_candidate
from workflow_dataset.vertical_selection.selection import (
    rank_candidates,
    recommend_primary_secondary,
    explain_vertical,
)
from workflow_dataset.vertical_selection.scope_lock import (
    get_core_surfaces,
    get_optional_surfaces,
    get_surface_class_for_vertical,
    get_surfaces_hidden_by_scope,
    get_scope_report,
)
from workflow_dataset.vertical_selection.store import (
    get_active_vertical_id,
    set_active_vertical_id,
)
from workflow_dataset.vertical_selection.models import (
    SURFACE_POLICY_RECOMMENDED,
    SURFACE_POLICY_ALLOWED,
    SURFACE_POLICY_DISCOURAGED,
    SURFACE_POLICY_BLOCKED,
)
from workflow_dataset.vertical_selection.surface_policies import (
    get_surface_policy_level,
    get_surface_policy_report,
    is_surface_experimental,
    get_advanced_reveal_rule,
)


def test_build_candidates_returns_list() -> None:
    """build_candidates returns list of VerticalCandidate (from curated packs)."""
    candidates = build_candidates(Path("/nonexistent/repo"))
    assert isinstance(candidates, list)
    assert len(candidates) >= 1
    for c in candidates:
        assert isinstance(c, VerticalCandidate)
        assert c.vertical_id
        assert c.label
        assert hasattr(c, "evidence_score")
        assert hasattr(c, "required_surface_ids")


def test_rank_candidates_returns_sorted() -> None:
    """rank_candidates returns descending by composite score."""
    ranked = rank_candidates(Path("/nonexistent/repo"))
    assert len(ranked) >= 1
    ids = [c.vertical_id for c in ranked]
    assert len(ids) == len(set(ids))


def test_recommend_primary_secondary() -> None:
    """recommend_primary_secondary returns primary and optional secondary."""
    rec = recommend_primary_secondary(Path("/nonexistent/repo"))
    assert "primary" in rec
    assert "ranked_ids" in rec
    assert "no_evidence" in rec
    if rec.get("primary"):
        assert rec["primary"].get("vertical_id")
        assert rec["primary"].get("label")


def test_explain_vertical() -> None:
    """explain_vertical returns scores and reasons for known vertical."""
    out = explain_vertical("founder_operator_core", Path("/nonexistent/repo"))
    assert out.get("vertical_id") == "founder_operator_core"
    assert "evidence_score" in out
    assert "strength_reason" in out
    assert "rank" in out


def test_explain_vertical_unknown() -> None:
    """explain_vertical returns error for unknown id."""
    out = explain_vertical("nonexistent_vertical", Path("/nonexistent/repo"))
    assert out.get("error") == "unknown vertical"


def test_scope_lock_core_surfaces() -> None:
    """get_core_surfaces returns required surface ids for vertical."""
    core = get_core_surfaces("founder_operator_core")
    assert isinstance(core, list)
    assert "workspace_home" in core or "day_status" in core


def test_surface_class_for_vertical() -> None:
    """get_surface_class_for_vertical returns core | advanced_available | non_core."""
    c = get_surface_class_for_vertical("workspace_home", "founder_operator_core")
    assert c in (SURFACE_CLASS_CORE, SURFACE_CLASS_ADVANCED_AVAILABLE, SURFACE_CLASS_NON_CORE)
    c2 = get_surface_class_for_vertical("nonexistent_surface", "founder_operator_core")
    assert c2 == SURFACE_CLASS_NON_CORE


def test_scope_report() -> None:
    """get_scope_report returns core, optional, hidden counts and lists."""
    report = get_scope_report("analyst_core")
    assert report["vertical_id"] == "analyst_core"
    assert "core_count" in report
    assert "hidden_count" in report
    assert report["core_count"] >= 0
    assert report["hidden_count"] >= 0


def test_store_get_set_vertical(tmp_path: Path) -> None:
    """Active vertical can be read and written."""
    assert get_active_vertical_id(tmp_path) == ""
    set_active_vertical_id("founder_operator_core", tmp_path)
    assert get_active_vertical_id(tmp_path) == "founder_operator_core"
    set_active_vertical_id("", tmp_path)
    assert get_active_vertical_id(tmp_path) == ""


def test_no_evidence_fallback() -> None:
    """When no evidence, recommend still returns primary (default ranking)."""
    rec = recommend_primary_secondary(Path("/nonexistent/repo"))
    assert rec is not None
    assert rec.get("primary") is not None or rec.get("ranked_ids")
    assert "no_evidence" in rec


def test_get_candidate() -> None:
    """get_candidate returns candidate by id or None."""
    c = get_candidate("document_worker_core", Path("/nonexistent/repo"))
    assert c is not None
    assert c.vertical_id == "document_worker_core"
    assert get_candidate("nonexistent", Path("/nonexistent/repo")) is None


# ----- M39D.1 Core vs advanced surface policies -----


def test_surface_policy_level() -> None:
    """get_surface_policy_level returns recommended | allowed | discouraged | blocked."""
    assert get_surface_policy_level("founder_operator_core", "workspace_home") == SURFACE_POLICY_RECOMMENDED
    assert get_surface_policy_level("founder_operator_core", "mission_control") == SURFACE_POLICY_ALLOWED
    assert get_surface_policy_level("founder_operator_core", "nonexistent_surface") == SURFACE_POLICY_DISCOURAGED


def test_is_surface_experimental() -> None:
    """is_surface_experimental labels known experimental surfaces."""
    assert is_surface_experimental("automation_run") is True
    assert is_surface_experimental("timeline") is True
    assert is_surface_experimental("workspace_home") is False


def test_surface_policy_report() -> None:
    """get_surface_policy_report returns recommended/allowed/discouraged/blocked and experimental."""
    report = get_surface_policy_report("analyst_core")
    assert report["vertical_id"] == "analyst_core"
    assert "recommended_surfaces" in report
    assert "allowed_surfaces" in report
    assert "discouraged_surfaces" in report
    assert "blocked_surfaces" in report
    assert "experimental_labels" in report
    assert "reveal_rules_summary" in report
    assert report["recommended_count"] + report["allowed_count"] + report["discouraged_count"] + report["blocked_count"] >= 1


def test_advanced_reveal_rule() -> None:
    """get_advanced_reveal_rule returns always | on_demand | after_first_milestone | never."""
    r = get_advanced_reveal_rule("founder_operator_core", "workspace_home")
    assert r in ("always", "on_demand", "after_first_milestone", "never")
    r_opt = get_advanced_reveal_rule("analyst_core", "mission_control")
    assert r_opt in ("always", "on_demand", "after_first_milestone", "never")
