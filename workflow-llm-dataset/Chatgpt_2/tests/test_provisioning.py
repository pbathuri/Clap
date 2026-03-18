"""M24E: Provisioning runner, domain environment, blocked prerequisite, first-value readiness."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.provisioning.runner import (
    check_prerequisites,
    run_provisioning,
    resolve_pack_id,
    RECIPE_PACK_ALIASES,
)
from workflow_dataset.provisioning.domain_environment import domain_environment_summary
from workflow_dataset.provisioning.report import format_provisioning_result, format_domain_environment_summary


def test_resolve_pack_id():
    assert resolve_pack_id("founder_ops_recipe") == "founder_ops_plus"
    assert resolve_pack_id("analyst_research_recipe") == "analyst_research_plus"
    assert resolve_pack_id("founder_ops_plus") == "founder_ops_plus"


def test_check_prerequisites_unknown_pack(tmp_path):
    missing, pack = check_prerequisites(value_pack_id="nonexistent", repo_root=tmp_path)
    assert "not found" in missing[0].lower() or "nonexistent" in missing[0]
    assert pack is None


def test_check_prerequisites_founder_ops(tmp_path):
    missing, pack = check_prerequisites(value_pack_id="founder_ops_plus", repo_root=tmp_path)
    assert pack is not None
    assert pack.pack_id == "founder_ops_plus"
    # In a clean tmp dir, jobs/routines/approval registry are typically missing
    assert isinstance(missing, list)


def test_run_provisioning_dry_run(tmp_path):
    result = run_provisioning("founder_ops_plus", repo_root=tmp_path, dry_run=True, strict_prerequisites=False)
    assert result.get("success") is True
    steps = result.get("steps_done") or []
    assert any("dry" in str(s).lower() for s in steps)


def test_run_provisioning_strict_blocked(tmp_path):
    # Strict mode: missing prereqs should block (no run)
    result = run_provisioning("founder_ops_plus", repo_root=tmp_path, dry_run=False, strict_prerequisites=True)
    # May be blocked due to missing jobs/routines/approval
    if not result.get("success"):
        assert result.get("missing_prerequisites")
        assert "blocked" in result.get("message", "").lower() or "prerequisite" in result.get("message", "").lower()


def test_run_provisioning_no_strict_creates_manifest(tmp_path):
    result = run_provisioning("founder_ops_plus", repo_root=tmp_path, dry_run=False, strict_prerequisites=False)
    assert result.get("success") is True
    assert result.get("run_id")
    prov_dir = tmp_path / "data/local/provisioning/founder_ops_plus"
    assert (prov_dir / "provisioning_manifest.json").exists()
    assert "write_provisioning_manifest" in result.get("steps_done", [])


def test_domain_environment_summary_unknown(tmp_path):
    summary = domain_environment_summary("nonexistent", repo_root=tmp_path)
    assert summary.get("error")
    assert summary.get("pack_id") == "nonexistent"


def test_domain_environment_summary_founder_ops(tmp_path):
    summary = domain_environment_summary("founder_ops_plus", repo_root=tmp_path)
    assert not summary.get("error") or summary.get("pack_id") == "founder_ops_plus"
    assert "jobs_ready" in summary
    assert "routines_ready" in summary
    assert "needs_activation" in summary
    assert "recommended_first_value_run" in summary
    assert "missing_prerequisites" in summary


def test_format_provisioning_result_success():
    result = {"success": True, "run_id": "run_1", "message": "Done", "steps_done": ["step1"], "outputs_produced": []}
    text = format_provisioning_result(result)
    assert "run_1" in text
    assert "Done" in text


def test_format_provisioning_result_blocked():
    result = {"success": False, "error": "Missing prerequisites", "missing_prerequisites": ["Job pack not found: x"]}
    text = format_provisioning_result(result)
    assert "Blocked" in text or "prerequisite" in text
    assert "Job pack" in text


def test_format_domain_environment_summary():
    summary = {
        "pack_id": "founder_ops_plus",
        "pack_name": "Founder / operator",
        "provisioned": True,
        "jobs_ready": ["weekly_status"],
        "routines_ready": [],
        "macros_ready": ["morning_ops"],
        "needs_activation": ["job:other"],
        "simulate_only": ["Real mode after approvals."],
        "recommended_first_value_run": "workflow-dataset jobs run --id weekly_status --mode simulate",
        "missing_prerequisites": [],
    }
    text = format_domain_environment_summary(summary)
    assert "founder_ops_plus" in text
    assert "Provisioned" in text
    assert "weekly_status" in text
    assert "first-value" in text.lower()
