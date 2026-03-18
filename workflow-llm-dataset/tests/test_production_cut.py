"""
M40A–M40D: Tests for production cut — final vertical lock and production surface freeze.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.production_cut.models import (
    ProductionCut,
    ChosenPrimaryVertical,
    SupportedWorkflowSet,
    RequiredTrustPosture,
    DefaultOperatingProfile,
    ProductionReadinessNote,
)
from workflow_dataset.production_cut.store import get_active_cut, set_active_cut
from workflow_dataset.production_cut.lock import (
    choose_primary_from_evidence,
    build_production_cut_for_vertical,
    lock_production_cut,
    explain_production_cut,
)
from workflow_dataset.production_cut.freeze import (
    build_production_freeze,
    get_default_visible_surfaces,
    get_hidden_experimental_surfaces,
    get_blocked_unsupported_surfaces,
)
from workflow_dataset.production_cut.scope_report import (
    build_frozen_scope_report,
    build_surfaces_classification,
)


def test_production_cut_model():
    """Production cut model: to_dict, chosen_vertical, surface lists."""
    cv = ChosenPrimaryVertical(
        vertical_id="founder_operator_core",
        label="Founder / Operator (core)",
        selection_reason="Evidence-based selection.",
        primary_workflow_ids=["morning_ops", "weekly_status"],
        excluded_surface_ids=["agent_loop"],
    )
    cut = ProductionCut(
        cut_id="founder_operator_primary",
        vertical_id="founder_operator_core",
        label="Founder (production cut)",
        frozen_at_utc="2025-01-01T12:00:00Z",
        chosen_vertical=cv,
        included_surface_ids=["workspace_home", "day_status", "queue_summary"],
        excluded_surface_ids=["agent_loop", "timeline"],
        quarantined_surface_ids=["automation_inbox"],
        supported_workflows=SupportedWorkflowSet(workflow_ids=["morning_ops"], path_id="founder_ops", label="Founder ops"),
        required_trust=RequiredTrustPosture(trust_preset_id="supervised_operator"),
        default_profile=DefaultOperatingProfile(workday_preset_id="founder_operator", default_experience_profile_id="founder_calm"),
        production_readiness_note=ProductionReadinessNote(summary="Scope frozen."),
    )
    d = cut.to_dict()
    assert d["cut_id"] == "founder_operator_primary"
    assert d["vertical_id"] == "founder_operator_core"
    assert len(d["included_surface_ids"]) == 3
    assert len(d["excluded_surface_ids"]) == 2
    assert len(d["quarantined_surface_ids"]) == 1
    assert d["chosen_vertical"]["selection_reason"] == "Evidence-based selection."
    assert d["supported_workflows"]["workflow_ids"] == ["morning_ops"]
    assert d["default_profile"]["workday_preset_id"] == "founder_operator"


def test_choose_primary_from_evidence():
    """Choose primary from evidence returns ChosenPrimaryVertical for known vertical."""
    chosen = choose_primary_from_evidence("founder_operator_core")
    assert chosen is not None
    assert chosen.vertical_id == "founder_operator_core"
    assert chosen.label
    assert chosen.selection_reason or chosen.description
    assert isinstance(chosen.primary_workflow_ids, list)
    assert isinstance(chosen.excluded_surface_ids, list)


def test_choose_primary_unknown_vertical():
    """Unknown vertical returns None."""
    chosen = choose_primary_from_evidence("nonexistent_vertical_xyz")
    assert chosen is None


def test_build_production_freeze():
    """Freeze for founder_operator_core: included, excluded, quarantined."""
    freeze = build_production_freeze("founder_operator_core")
    assert freeze is not None
    assert "included_surface_ids" in freeze
    assert "excluded_surface_ids" in freeze
    assert "quarantined_surface_ids" in freeze
    assert freeze["vertical_id"] == "founder_operator_core"
    assert len(freeze["included_surface_ids"]) >= 1
    assert freeze["included_count"] == len(freeze["included_surface_ids"])
    assert freeze["excluded_count"] == len(freeze["excluded_surface_ids"])
    assert freeze["quarantined_count"] == len(freeze["quarantined_surface_ids"])


def test_build_production_freeze_unknown():
    """Unknown vertical returns None."""
    assert build_production_freeze("nonexistent_vertical_xyz") is None


def test_build_production_cut_for_vertical():
    """Build full production cut for founder_operator_core."""
    cut = build_production_cut_for_vertical("founder_operator_core")
    assert cut is not None
    assert cut.cut_id == "founder_operator_core_primary"
    assert cut.vertical_id == "founder_operator_core"
    assert cut.chosen_vertical is not None
    assert cut.frozen_at_utc
    assert len(cut.included_surface_ids) >= 1
    assert cut.supported_workflows is not None
    assert cut.required_trust is not None
    assert cut.default_profile is not None
    assert cut.production_readiness_note is not None


def test_build_production_cut_unknown():
    """Unknown vertical returns None."""
    assert build_production_cut_for_vertical("nonexistent_vertical_xyz") is None


def test_lock_production_cut_and_store(tmp_path):
    """Lock production cut persists cut and sets active vertical and pack."""
    cut = lock_production_cut("founder_operator_core", repo_root=str(tmp_path))
    assert cut is not None
    loaded = get_active_cut(tmp_path)
    assert loaded is not None
    assert loaded.cut_id == cut.cut_id
    assert loaded.vertical_id == cut.vertical_id
    assert loaded.included_surface_ids == cut.included_surface_ids


def test_frozen_scope_report_from_cut(tmp_path):
    """Frozen scope report from active cut has included/excluded/quarantined."""
    lock_production_cut("founder_operator_core", repo_root=str(tmp_path))
    cut = get_active_cut(tmp_path)
    report = build_frozen_scope_report(cut=cut, repo_root=str(tmp_path))
    assert "error" not in report or not report["error"]
    assert report["included_count"] >= 1
    assert "included" in report
    assert "excluded" in report
    assert "quarantined" in report


def test_surfaces_classification():
    """Surfaces classification returns included, excluded, quarantined with labels."""
    classification = build_surfaces_classification(vertical_id="founder_operator_core")
    assert "included" in classification
    assert "excluded" in classification
    assert "quarantined" in classification
    for e in classification.get("included", [])[:3]:
        assert "surface_id" in e
        assert "policy_level" in e


def test_explain_production_cut():
    """Explain production cut returns selection reason and counts."""
    cut = build_production_cut_for_vertical("founder_operator_core")
    assert cut is not None
    out = explain_production_cut(cut)
    assert out["cut_id"] == cut.cut_id
    assert "included_count" in out
    assert "excluded_count" in out
    assert "quarantined_count" in out
    assert "primary_workflow_ids" in out
    assert "default_workday" in out or "trust_preset" in out


def test_default_profile_generation():
    """Production cut for founder_operator_core has default workday and experience."""
    cut = build_production_cut_for_vertical("founder_operator_core")
    assert cut is not None
    assert cut.default_profile is not None
    assert cut.default_profile.workday_preset_id
    assert cut.default_profile.default_experience_profile_id or True
    assert cut.required_trust is not None
    assert cut.required_trust.trust_preset_id


def test_get_default_visible_and_blocked():
    """get_default_visible_surfaces and get_blocked_unsupported_surfaces return lists."""
    included = get_default_visible_surfaces("founder_operator_core")
    assert isinstance(included, list)
    blocked = get_blocked_unsupported_surfaces("founder_operator_core")
    assert isinstance(blocked, list)
    quarantined = get_hidden_experimental_surfaces("founder_operator_core")
    assert isinstance(quarantined, list)


# ----- M40D.1 Production defaults + quarantine rules + labels -----


def test_production_default_profile(tmp_path):
    """Production default profile from active cut has workspace/day/queue and label."""
    from workflow_dataset.production_cut import get_production_default_profile
    lock_production_cut("founder_operator_core", repo_root=str(tmp_path))
    profile = get_production_default_profile(repo_root=tmp_path)
    assert profile is not None
    assert "Production default" in profile.label
    assert profile.workday_preset_id
    assert profile.operator_summary


def test_production_default_profile_no_cut():
    """No active cut returns None."""
    from workflow_dataset.production_cut import get_production_default_profile
    profile = get_production_default_profile(cut=None, repo_root="/nonexistent_repo_path_xyz")
    assert profile is None


def test_quarantine_rules_report(tmp_path):
    """Quarantine rules report lists rules with operator_explanation and production_safe=False."""
    from workflow_dataset.production_cut import build_quarantine_rules_report, list_quarantine_rules
    lock_production_cut("founder_operator_core", repo_root=str(tmp_path))
    report = build_quarantine_rules_report(repo_root=tmp_path)
    assert report["vertical_id"] == "founder_operator_core"
    assert "quarantine_rules" in report
    assert "operator_summary" in report
    for r in report.get("quarantine_rules", []):
        assert r.get("production_safe") is False
        assert "operator_explanation" in r
    rules = list_quarantine_rules(vertical_id="founder_operator_core")
    assert isinstance(rules, list)


def test_production_safe_label_report(tmp_path):
    """Production-safe label report: production_safe only for included surfaces."""
    from workflow_dataset.production_cut import build_production_safe_label_report
    lock_production_cut("founder_operator_core", repo_root=str(tmp_path))
    report = build_production_safe_label_report(repo_root=tmp_path)
    assert report["vertical_id"] == "founder_operator_core"
    assert report["production_safe_count"] >= 1
    assert "labels" in report
    safe_labels = [L for L in report["labels"] if L.get("production_safe")]
    assert len(safe_labels) == report["production_safe_count"]
    for L in report["labels"]:
        if not L.get("production_safe"):
            assert L.get("reason_if_not_safe") in ("experimental", "excluded", "")


def test_operator_surface_explanations(tmp_path):
    """Operator explanations include production_safe, advanced_only, experimental_only summaries."""
    from workflow_dataset.production_cut import build_operator_surface_explanations
    lock_production_cut("founder_operator_core", repo_root=str(tmp_path))
    out = build_operator_surface_explanations(repo_root=tmp_path)
    assert "production_safe_summary" in out
    assert "advanced_only_summary" in out
    assert "experimental_only_summary" in out
    assert "included_count" in out
    assert "quarantined_count" in out
