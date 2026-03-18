"""M24A: External capability activation planner — registry, planner, policy, plans, report."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.external_capability.schema import (
    ExternalCapabilitySource,
    SOURCE_CATEGORIES,
    ACTIVATION_STATUSES,
)
from workflow_dataset.external_capability.registry import (
    load_external_sources,
    list_external_sources,
    get_external_source,
)
from workflow_dataset.external_capability.policy import (
    apply_rejection_policy,
    REJECTION_REMOTE_ONLY_LOCAL_FIRST,
    REJECTION_INCOMPATIBLE_MACHINE,
    REJECTION_UNSUPPORTED_LICENSE,
    REJECTION_RESOURCE_TOO_HIGH,
)
from workflow_dataset.external_capability.planner import (
    ActivationPlanner,
    plan_activations,
    PlannerResult,
    BlockedEntry,
)
from workflow_dataset.external_capability.plans import build_activation_plan
from workflow_dataset.external_capability.report import (
    format_external_list,
    format_recommend,
    format_blocked,
    format_plan,
    format_explain,
)


def test_schema_to_dict_roundtrip():
    """ExternalCapabilitySource to_dict/from_dict roundtrip."""
    s = ExternalCapabilitySource(
        source_id="openclaw",
        category="openclaw",
        local=True,
        supported_task_classes=["desktop_assistant"],
        activation_status="optional",
    )
    d = s.to_dict()
    assert d["source_id"] == "openclaw"
    assert d["category"] == "openclaw"
    s2 = ExternalCapabilitySource.from_dict(d)
    assert s2.source_id == s.source_id
    assert s2.activation_status == s.activation_status


def test_registry_load(tmp_path):
    """load_external_sources returns list of ExternalCapabilitySource from built-in data."""
    sources = load_external_sources(tmp_path)
    assert isinstance(sources, list)
    assert len(sources) >= 1
    ids = [x.source_id for x in sources]
    assert "openclaw" in ids or "coding_agent" in ids or "backend_ollama" in ids
    for s in sources:
        assert isinstance(s, ExternalCapabilitySource)
        assert s.source_id
        assert s.category in SOURCE_CATEGORIES or s.category in ("openclaw", "coding_agent", "ide_editor", "automation")


def test_registry_get(tmp_path):
    """get_external_source returns source for known id, None for unknown."""
    s = get_external_source("openclaw", tmp_path)
    assert s is not None
    assert s.source_id == "openclaw"
    assert get_external_source("nonexistent_xyz", tmp_path) is None


def test_policy_rejection_remote_only():
    """apply_rejection_policy rejects remote-only when local-first required."""
    source = ExternalCapabilitySource(
        source_id="cloud_only",
        category="automation",
        local=False,
        optional_remote=False,
    )
    allowed, reason = apply_rejection_policy(source, {}, {})
    assert allowed is False
    assert reason == REJECTION_REMOTE_ONLY_LOCAL_FIRST


def test_policy_rejection_incompatible_machine():
    """apply_rejection_policy rejects when tier not in supported_tiers."""
    source = ExternalCapabilitySource(
        source_id="dev_only",
        category="ollama_model",
        local=True,
        supported_tiers=["dev_full"],
    )
    machine = {"tier": "minimal_eval"}
    allowed, reason = apply_rejection_policy(source, machine, {})
    assert allowed is False
    assert reason == REJECTION_INCOMPATIBLE_MACHINE


def test_policy_rejection_license():
    """apply_rejection_policy rejects unsupported license."""
    source = ExternalCapabilitySource(
        source_id="proprietary",
        category="automation",
        local=True,
        license_policy="proprietary",
    )
    allowed, reason = apply_rejection_policy(source, {"tier": "local_standard"}, {})
    assert allowed is False
    assert reason == REJECTION_UNSUPPORTED_LICENSE


def test_policy_rejection_resource():
    """apply_rejection_policy rejects high resource on constrained tier."""
    source = ExternalCapabilitySource(
        source_id="heavy",
        category="ollama_model",
        local=True,
        supported_tiers=["dev_full", "local_standard", "constrained_edge", "minimal_eval"],
        estimated_resource="high",
    )
    machine = {"tier": "constrained_edge"}
    allowed, reason = apply_rejection_policy(source, machine, {})
    assert allowed is False
    assert reason == REJECTION_RESOURCE_TOO_HIGH


def test_planner_returns_result(tmp_path):
    """ActivationPlanner.plan returns PlannerResult with recommended, blocked, resource_estimate."""
    planner = ActivationPlanner(repo_root=tmp_path)
    result = planner.plan(machine_profile={"tier": "local_standard"}, trust_posture={})
    assert isinstance(result, PlannerResult)
    assert hasattr(result, "recommended")
    assert hasattr(result, "rejected_by_policy")
    assert hasattr(result, "not_worth_it")
    assert hasattr(result, "prerequisite_steps")
    assert isinstance(result.resource_estimate, dict)
    assert "tier" in result.resource_estimate or "low_count" in result.resource_estimate


def test_plan_activations_convenience(tmp_path):
    """plan_activations(repo_root) runs without machine/trust (builds from local_deployment/trust)."""
    result = plan_activations(repo_root=tmp_path)
    assert isinstance(result, PlannerResult)


def test_build_activation_plan(tmp_path):
    """build_activation_plan returns list of steps; unknown source returns single unknown step."""
    steps = build_activation_plan("openclaw", tmp_path)
    assert isinstance(steps, list)
    assert len(steps) >= 1
    assert all("action" in s and "detail" in s for s in steps)
    unknown = build_activation_plan("nonexistent_id_xyz", tmp_path)
    assert len(unknown) == 1
    assert unknown[0]["action"] == "unknown"


def test_report_format_external_list(tmp_path):
    """format_external_list produces string with source ids."""
    sources = list_external_sources(tmp_path)
    report = format_external_list(sources)
    assert "External capability" in report or "sources" in report
    if sources:
        assert sources[0].source_id in report


def test_report_format_recommend():
    """format_recommend produces string from PlannerResult."""
    result = PlannerResult(
        recommended=[],
        prerequisite_steps=["Step one"],
        resource_estimate={"tier": "local_standard"},
    )
    report = format_recommend(result)
    assert "Recommended" in report or "Prerequisite" in report
    assert "Step one" in report


def test_report_format_blocked():
    """format_blocked produces string from PlannerResult."""
    result = PlannerResult(
        rejected_by_policy=[BlockedEntry("x", "policy", "unsupported_license")],
        not_worth_it=[],
    )
    report = format_blocked(result)
    assert "Blocked" in report or "Rejected" in report


def test_report_format_plan():
    """format_plan produces string from steps and source_id."""
    steps = [{"action": "pull_model", "detail": "Pull model X.", "safe_local": True}]
    report = format_plan(steps, "ollama_qwen2.5-coder")
    assert "ollama_qwen2.5-coder" in report
    assert "pull_model" in report


def test_report_format_explain(tmp_path):
    """format_explain produces string for source or unknown."""
    s = get_external_source("openclaw", tmp_path)
    report = format_explain(s, "openclaw")
    assert "openclaw" in report
    assert "category" in report or "openclaw" in report
    unknown_report = format_explain(None, "nonexistent")
    assert "not found" in unknown_report
