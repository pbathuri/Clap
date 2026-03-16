"""M23B: Edge / Hardware Readiness — profile, checks, reports. Local-only; no cloud.
M23B-F2: Tiers, workflow matrix by tier, tier comparison."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.edge.profile import build_edge_profile, SUPPORTED_WORKFLOWS, SANDBOX_PATHS
from workflow_dataset.edge.checks import run_readiness_checks, checks_summary
from workflow_dataset.edge.report import (
    generate_edge_readiness_report,
    generate_missing_dependency_report,
    generate_workflow_matrix_report,
    generate_package_report,
    generate_tier_matrix_report,
    compare_tiers,
    generate_compare_report,
)
from workflow_dataset.edge.tiers import EDGE_TIERS, get_tier_definition, get_workflow_status_for_tier, list_tiers
from workflow_dataset.edge.package_report import build_workflow_matrix_by_tier, build_workflow_matrix_all_tiers


def test_build_edge_profile_structure(tmp_path):
    (tmp_path / "configs").mkdir(parents=True)
    (tmp_path / "configs/settings.yaml").write_text("release: {}", encoding="utf-8")
    profile = build_edge_profile(repo_root=tmp_path)
    assert "repo_root" in profile
    assert profile["repo_root"] == str(tmp_path.resolve())
    assert "runtime_requirements" in profile
    assert "python_version_min" in profile["runtime_requirements"]
    assert "supported_workflows" in profile
    assert "sandbox_path_assumptions" in profile
    assert set(profile["supported_workflows"]) == set(SUPPORTED_WORKFLOWS)


def test_run_readiness_checks_returns_list(tmp_path):
    (tmp_path / "configs").mkdir(parents=True)
    checks = run_readiness_checks(repo_root=tmp_path)
    assert isinstance(checks, list)
    assert len(checks) >= 1
    for c in checks:
        assert "check_id" in c
        assert "passed" in c
        assert "message" in c
        assert "optional" in c


def test_checks_summary(tmp_path):
    (tmp_path / "configs").mkdir(parents=True)
    checks = run_readiness_checks(repo_root=tmp_path)
    summary = checks_summary(checks)
    assert "passed" in summary
    assert "failed" in summary
    assert "ready" in summary


def test_generate_edge_readiness_report(tmp_path):
    (tmp_path / "configs").mkdir(parents=True)
    out = tmp_path / "readiness.md"
    path = generate_edge_readiness_report(output_path=out, repo_root=tmp_path)
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Edge Readiness" in text
    assert "Runtime" in text or "runtime" in text
    assert "Sandbox" in text or "sandbox" in text


def test_generate_missing_dependency_report(tmp_path):
    out = tmp_path / "missing.md"
    path = generate_missing_dependency_report(output_path=out, repo_root=tmp_path)
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Missing" in text or "dependency" in text.lower()


def test_generate_workflow_matrix_report_markdown(tmp_path):
    out = tmp_path / "matrix.md"
    path = generate_workflow_matrix_report(output_path=out, repo_root=tmp_path, format="markdown")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Workflow" in text or "workflow" in text
    assert "ops_reporting_workspace" in text or "weekly_status" in text


def test_generate_workflow_matrix_report_json(tmp_path):
    out = tmp_path / "matrix.json"
    path = generate_workflow_matrix_report(output_path=out, repo_root=tmp_path, format="json")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "workflows" in data
    assert len(data["workflows"]) >= 1


def test_generate_package_report(tmp_path):
    (tmp_path / "configs").mkdir(parents=True)
    out = tmp_path / "pkg.md"
    path = generate_package_report(output_path=out, repo_root=tmp_path)
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Package" in text or "package" in text
    assert "workflow" in text.lower()


# ----- M23B-F2: Tiers, matrix by tier, compare -----
def test_tiers_list():
    tiers = list_tiers()
    assert len(tiers) == len(EDGE_TIERS)
    for t in tiers:
        assert "tier" in t
        assert "supported_count" in t or "degraded_count" in t or "unavailable_count" in t


def test_get_tier_definition():
    d = get_tier_definition("local_standard")
    assert d is not None
    assert d["tier"] == "local_standard"
    assert "required_paths" in d
    assert "llm_requirement" in d
    assert "workflow_status" in d
    assert get_tier_definition("unknown_tier") is None


def test_build_edge_profile_with_tier(tmp_path):
    profile = build_edge_profile(repo_root=tmp_path, tier="local_standard")
    assert profile.get("tier") == "local_standard"
    assert "tier_description" in profile
    assert "tier_llm_requirement" in profile
    assert "workflow_availability" in profile
    assert len(profile["workflow_availability"]) >= 1
    for wa in profile["workflow_availability"]:
        assert wa.get("status") in ("supported", "degraded", "unavailable")
        assert "reason" in wa or "workflow" in wa


def test_build_workflow_matrix_by_tier(tmp_path):
    matrix = build_workflow_matrix_by_tier("constrained_edge", repo_root=tmp_path)
    assert len(matrix) >= 1
    for row in matrix:
        assert "workflow" in row
        assert "status" in row
        assert row["status"] in ("supported", "degraded", "unavailable")
        assert "reason" in row
        assert "fallback" in row or "missing_functionality" in row


def test_build_workflow_matrix_all_tiers(tmp_path):
    all_ = build_workflow_matrix_all_tiers(repo_root=tmp_path)
    assert set(all_.keys()) == set(EDGE_TIERS)
    for tier in EDGE_TIERS:
        assert len(all_[tier]) >= 1


def test_generate_tier_matrix_report_single(tmp_path):
    out = tmp_path / "local_standard_matrix.md"
    path = generate_tier_matrix_report(output_path=out, repo_root=tmp_path, tier="local_standard", format="markdown")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "local_standard" in text
    assert "supported" in text or "degraded" in text or "workflow" in text.lower()


def test_generate_tier_matrix_report_all(tmp_path):
    out = tmp_path / "all_tiers.md"
    path = generate_tier_matrix_report(output_path=out, repo_root=tmp_path, tier=None, format="markdown")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    for t in EDGE_TIERS:
        assert t in text


def test_compare_tiers(tmp_path):
    diff = compare_tiers("local_standard", "constrained_edge", repo_root=tmp_path)
    assert not diff.get("error"), diff.get("error")
    assert diff.get("tier_a") == "local_standard"
    assert diff.get("tier_b") == "constrained_edge"
    assert "workflow_status_diff" in diff
    assert "llm_requirement_a" in diff
    assert "paths_only_in_a" in diff or "paths_only_in_b" in diff


def test_generate_compare_report(tmp_path):
    out = tmp_path / "compare.md"
    path = generate_compare_report(output_path=out, repo_root=tmp_path, tier_a="local_standard", tier_b="minimal_eval")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Comparison" in text or "Tier" in text
    assert "local_standard" in text
    assert "minimal_eval" in text
