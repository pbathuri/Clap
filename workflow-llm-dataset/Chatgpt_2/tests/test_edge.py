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
    generate_degraded_report,
    generate_smoke_check_report,
)
from workflow_dataset.edge.tiers import (
    EDGE_TIERS,
    get_tier_definition,
    get_workflow_status_for_tier,
    get_required_dependencies_for_tier,
    list_tiers,
)
from workflow_dataset.edge.package_report import (
    build_workflow_matrix_by_tier,
    build_workflow_matrix_all_tiers,
    build_packaging_metadata,
)
from workflow_dataset.edge.smoke import run_smoke_check


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
    assert "Workflow status diff" in text or "workflow" in text.lower()
    assert "Path" in text or "path" in text or "dependencies" in text.lower()


def test_get_required_dependencies_for_tier():
    req, opt = get_required_dependencies_for_tier("local_standard")
    assert isinstance(req, list)
    assert isinstance(opt, list)
    assert any(d.get("name") == "config" or d.get("name") == "sandbox" for d in req)
    req2, opt2 = get_required_dependencies_for_tier("unknown")
    assert req2 == []
    assert opt2 == []


def test_generate_degraded_report(tmp_path):
    out = tmp_path / "degraded.md"
    path = generate_degraded_report(output_path=out, repo_root=tmp_path, tier="constrained_edge", format="markdown")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "degraded" in text.lower()
    assert "constrained_edge" in text
    assert "workflow" in text.lower() or "Fallback" in text
    out_json = tmp_path / "degraded.json"
    path_json = generate_degraded_report(output_path=out_json, repo_root=tmp_path, tier=None, format="json")
    assert path_json.exists()
    data = json.loads(path_json.read_text(encoding="utf-8"))
    assert "tiers" in data
    assert "constrained_edge" in data["tiers"]
    assert len(data["tiers"]["constrained_edge"]) >= 1
    for row in data["tiers"]["constrained_edge"]:
        assert "workflow" in row
        assert "reason" in row
        assert "fallback" in row or "missing_functionality" in row


def test_tier_matrix_report_includes_deps_and_degraded(tmp_path):
    out = tmp_path / "matrix_deps.md"
    path = generate_tier_matrix_report(
        output_path=out, repo_root=tmp_path, tier="constrained_edge", format="markdown"
    )
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Required" in text or "Optional" in text or "dependencies" in text.lower()
    assert "Degraded" in text or "degraded" in text
    assert "constrained_edge" in text


# ----- M23B-F3: Packaging metadata, smoke check -----
def test_build_packaging_metadata(tmp_path):
    (tmp_path / "configs").mkdir(parents=True)
    (tmp_path / "configs/settings.yaml").write_text("project: {}", encoding="utf-8")
    meta = build_packaging_metadata("local_standard", repo_root=tmp_path)
    assert meta.get("tier") == "local_standard"
    assert "required_runtime_components" in meta
    assert "optional_runtime_components" in meta
    assert "supported_workflows" in meta
    assert "degraded_workflows" in meta or "unavailable_workflows" in meta
    assert "local_path_assumptions" in meta
    assert "config_assumptions" in meta
    assert "notes_for_packaging" in meta
    err = build_packaging_metadata("unknown_tier", repo_root=tmp_path)
    assert err.get("error") is not None


def test_generate_package_report_with_tier(tmp_path):
    (tmp_path / "configs").mkdir(parents=True)
    (tmp_path / "configs/settings.yaml").write_text("project: {}", encoding="utf-8")
    out = tmp_path / "pkg_tier.md"
    path = generate_package_report(output_path=out, repo_root=tmp_path, tier="local_standard", format="markdown")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "local_standard" in text
    assert "Required" in text or "Supported" in text
    assert "workflow" in text.lower()
    out_json = tmp_path / "pkg_tier.json"
    path_json = generate_package_report(output_path=out_json, repo_root=tmp_path, tier="constrained_edge", format="json")
    assert path_json.exists()
    data = json.loads(path_json.read_text(encoding="utf-8"))
    assert data.get("tier") == "constrained_edge"
    assert "degraded_workflows" in data


def test_run_smoke_check_readiness_only(tmp_path):
    (tmp_path / "configs").mkdir(parents=True)
    (tmp_path / "configs/settings.yaml").write_text("project: {}", encoding="utf-8")
    # Provide LLM config so skip reason is "Demo run disabled" not "LLM missing"
    (tmp_path / "configs/llm_training_full.yaml").write_text("base_model: test/model\nbackend: mlx", encoding="utf-8")
    result = run_smoke_check("local_standard", repo_root=tmp_path, run_demo=False)
    assert result.get("tier") == "local_standard"
    assert "readiness_ok" in result
    assert "workflow_results" in result
    assert "overall_pass" in result
    for r in result["workflow_results"]:
        assert r.get("status") == "skipped"
        assert "Demo run disabled" in (r.get("message") or "") or "readiness only" in (r.get("message") or "").lower()


def test_run_smoke_check_unknown_tier(tmp_path):
    result = run_smoke_check("unknown_tier", repo_root=tmp_path)
    assert result.get("error") is not None
    assert result.get("overall_pass") is False


def test_generate_smoke_check_report(tmp_path):
    (tmp_path / "configs").mkdir(parents=True)
    (tmp_path / "configs/settings.yaml").write_text("project: {}", encoding="utf-8")
    result = run_smoke_check("local_standard", repo_root=tmp_path, run_demo=False)
    out = tmp_path / "smoke.md"
    path = generate_smoke_check_report(result, output_path=out, repo_root=tmp_path)
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Smoke" in text
    assert "local_standard" in text
    assert "Workflows tested" in text or "workflow" in text.lower()
    out_json = tmp_path / "smoke.json"
    path_json = generate_smoke_check_report(result, output_path=out_json, repo_root=tmp_path, format="json")
    assert path_json.exists()
    data = json.loads(path_json.read_text(encoding="utf-8"))
    assert "workflow_results" in data
    assert data.get("tier") == "local_standard"


# ----- M23B-F4: Docs, sample profiles, readability -----
def test_readiness_report_contains_outcome(tmp_path):
    (tmp_path / "configs").mkdir(parents=True)
    (tmp_path / "configs/settings.yaml").write_text("project: {}", encoding="utf-8")
    out = tmp_path / "readiness_outcome.md"
    path = generate_edge_readiness_report(output_path=out, repo_root=tmp_path)
    text = path.read_text(encoding="utf-8")
    assert "Outcome:" in text
    assert "Ready" in text or "Not ready" in text


def test_missing_dep_report_contains_what_this_means(tmp_path):
    out = tmp_path / "missing_meaning.md"
    path = generate_missing_dependency_report(output_path=out, repo_root=tmp_path)
    text = path.read_text(encoding="utf-8")
    if "Required (must fix)" in text or "Optional" in text:
        assert "What this means" in text or "Required" in text
    assert "Missing" in text or "dependency" in text.lower()


def test_sample_profiles_exist():
    """Sample profile docs for each tier exist under docs/edge/sample_profiles."""
    repo_root = Path(__file__).resolve().parent.parent
    samples_dir = repo_root / "docs" / "edge" / "sample_profiles"
    if not samples_dir.exists():
        pytest.skip("docs/edge/sample_profiles not present (optional doc tree)")
    for tier in ("dev_full", "local_standard", "constrained_edge", "minimal_eval"):
        sample = samples_dir / f"{tier}.md"
        assert sample.exists(), f"Sample profile {tier}.md should exist"
        content = sample.read_text(encoding="utf-8")
        assert tier in content
        assert "Required" in content or "paths" in content.lower() or "LLM" in content


# ----- M23B-F5: Readiness history, drift detection -----
from workflow_dataset.edge.history import (
    record_readiness_snapshot,
    list_readiness_snapshots,
    load_latest_snapshot,
    load_previous_snapshot,
    snapshot_from_checks,
)
from workflow_dataset.edge.drift import compute_drift, generate_drift_report


def test_record_readiness_snapshot(tmp_path):
    (tmp_path / "configs").mkdir(parents=True)
    (tmp_path / "configs/settings.yaml").write_text("release: {}", encoding="utf-8")
    snapshot = record_readiness_snapshot(repo_root=tmp_path)
    assert "timestamp_utc" in snapshot
    assert "ready" in snapshot
    assert "summary" in snapshot
    assert "checks" in snapshot
    assert "supported_workflows" in snapshot
    assert "_path" in snapshot
    assert "_latest_path" in snapshot
    assert Path(snapshot["_path"]).exists()
    assert Path(snapshot["_latest_path"]).exists()
    hist = json.loads(Path(snapshot["_path"]).read_text(encoding="utf-8"))
    assert hist["timestamp_utc"] == snapshot["timestamp_utc"]
    assert hist["ready"] == snapshot["ready"]


def test_list_readiness_snapshots(tmp_path):
    (tmp_path / "configs").mkdir(parents=True)
    (tmp_path / "configs/settings.yaml").write_text("release: {}", encoding="utf-8")
    record_readiness_snapshot(repo_root=tmp_path)
    record_readiness_snapshot(repo_root=tmp_path)
    listed = list_readiness_snapshots(repo_root=tmp_path, limit=5)
    assert len(listed) >= 1
    for item in listed:
        assert "path" in item
        assert "timestamp_utc" in item
        assert "ready" in item


def test_load_latest_and_previous_snapshot(tmp_path):
    import time
    (tmp_path / "configs").mkdir(parents=True)
    (tmp_path / "configs/settings.yaml").write_text("release: {}", encoding="utf-8")
    latest = load_latest_snapshot(repo_root=tmp_path)
    assert latest is None
    record_readiness_snapshot(repo_root=tmp_path)
    latest = load_latest_snapshot(repo_root=tmp_path)
    assert latest is not None
    assert "checks" in latest
    assert "timestamp_utc" in latest
    prev = load_previous_snapshot(repo_root=tmp_path)
    assert prev is None  # only one snapshot
    time.sleep(1.1)  # ensure distinct timestamped filename (history uses second precision)
    record_readiness_snapshot(repo_root=tmp_path)
    prev = load_previous_snapshot(repo_root=tmp_path)
    assert prev is not None
    assert "checks" in prev


def test_snapshot_from_checks():
    checks = [{"check_id": "a", "passed": True, "message": "ok", "optional": False}]
    summary = {"ready": True, "passed": 1, "failed": 0, "failed_required": 0, "optional_disabled": 0}
    profile = {"supported_workflows": ["w1"]}
    snap = snapshot_from_checks(checks, summary, profile, "2025-01-01T00:00:00Z")
    assert snap["timestamp_utc"] == "2025-01-01T00:00:00Z"
    assert snap["ready"] is True
    assert len(snap["checks"]) == 1
    assert snap["checks"][0]["check_id"] == "a"
    assert snap["supported_workflows"] == ["w1"]


def test_compute_drift_no_previous(tmp_path):
    (tmp_path / "configs").mkdir(parents=True)
    (tmp_path / "configs/settings.yaml").write_text("release: {}", encoding="utf-8")
    drift = compute_drift(repo_root=tmp_path)
    assert "current_ready" in drift
    assert drift.get("previous_snapshot") is None
    assert "next_command" in drift


def test_compute_drift_with_previous(tmp_path):
    import time
    (tmp_path / "configs").mkdir(parents=True)
    (tmp_path / "configs/settings.yaml").write_text("release: {}", encoding="utf-8")
    record_readiness_snapshot(repo_root=tmp_path)
    time.sleep(1.1)  # ensure two distinct snapshots so "previous" exists
    record_readiness_snapshot(repo_root=tmp_path)
    drift = compute_drift(repo_root=tmp_path)
    assert drift.get("previous_snapshot") is not None
    assert "worse" in drift
    assert "improved" in drift
    assert "has_drift" in drift
    assert "next_command" in drift


def test_generate_drift_report(tmp_path):
    import time
    (tmp_path / "configs").mkdir(parents=True)
    (tmp_path / "configs/settings.yaml").write_text("release: {}", encoding="utf-8")
    out = tmp_path / "drift.md"
    path = generate_drift_report(output_path=out, repo_root=tmp_path)
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Drift" in text
    assert "Next command" in text or "next command" in text or "No previous snapshot" in text or "check-now" in text
    record_readiness_snapshot(repo_root=tmp_path)
    time.sleep(1.1)
    record_readiness_snapshot(repo_root=tmp_path)
    path2 = generate_drift_report(output_path=tmp_path / "drift2.md", repo_root=tmp_path)
    assert path2.exists()
    text2 = path2.read_text(encoding="utf-8")
    assert "Outcome" in text2 or "Current" in text2


def test_edge_check_now_cli(tmp_path):
    pytest.importorskip("yaml")
    (tmp_path / "configs").mkdir(parents=True)
    (tmp_path / "configs/settings.yaml").write_text("release: {}", encoding="utf-8")
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    result = CliRunner().invoke(app, ["edge", "check-now", "--repo-root", str(tmp_path), "--config", str(tmp_path / "configs/settings.yaml")])
    assert result.exit_code == 0
    assert "Snapshot recorded" in result.output
    assert "drift-report" in result.output
    hist_dir = tmp_path / "data" / "local" / "edge" / "history"
    assert hist_dir.exists()
    assert any(hist_dir.glob("readiness_*.json"))


def test_edge_drift_report_cli(tmp_path):
    pytest.importorskip("yaml")
    (tmp_path / "configs").mkdir(parents=True)
    (tmp_path / "configs/settings.yaml").write_text("release: {}", encoding="utf-8")
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    result = CliRunner().invoke(app, ["edge", "drift-report", "--repo-root", str(tmp_path)])
    assert result.exit_code == 0
    assert "Drift report" in result.output
    default_report = tmp_path / "data" / "local" / "edge" / "readiness_drift_report.md"
    assert default_report.exists()


def test_edge_schedule_checks_cli(tmp_path):
    pytest.importorskip("yaml")
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    result = CliRunner().invoke(app, ["edge", "schedule-checks", "--repo-root", str(tmp_path), "--interval-hours", "12"])
    assert result.exit_code == 0
    assert "Schedule marker" in result.output
    schedule_path = tmp_path / "data" / "local" / "edge" / "schedule.json"
    assert schedule_path.exists()
    data = json.loads(schedule_path.read_text(encoding="utf-8"))
    assert data.get("interval_hours") == 12
    assert "check-now" in data.get("note", "")
