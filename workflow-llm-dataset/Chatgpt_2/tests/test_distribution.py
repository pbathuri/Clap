"""M24R–M24U: Tests for distribution layer — bundle, install profile, update planner, checklists, readiness."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.distribution.models import InstallBundle, FieldDeploymentProfile, PackAwareInstallProfile
from workflow_dataset.distribution.bundle import build_install_bundle, write_install_bundle
from workflow_dataset.distribution.install_profile import build_pack_aware_install_profile, build_field_deployment_profile
from workflow_dataset.distribution.update_planner import build_update_plan, format_update_plan, UpdatePlan
from workflow_dataset.distribution.checklists import (
    build_field_checklist,
    format_field_checklist,
    list_checklist_packs,
)
from workflow_dataset.distribution.readiness import build_deploy_readiness, format_deploy_readiness
from workflow_dataset.distribution.handoff_pack import (
    build_handoff_pack,
    write_handoff_pack,
    format_handoff_readme,
    format_release_bundle_summary,
)


def test_build_install_bundle(tmp_path: Path) -> None:
    bundle = build_install_bundle(repo_root=tmp_path, bundle_id="test_bundle")
    assert bundle.bundle_id == "test_bundle"
    assert bundle.version == "1"
    assert "config_exists" in bundle.required_capabilities
    assert bundle.machine_assumptions.get("local_only") is True


def test_write_install_bundle(tmp_path: Path) -> None:
    bundle = build_install_bundle(repo_root=tmp_path, bundle_id="write_test")
    path = write_install_bundle(bundle, repo_root=tmp_path)
    assert path.exists()
    assert path.suffix == ".json"
    data = __import__("json").loads(path.read_text(encoding="utf-8"))
    assert data["bundle_id"] == "write_test"


def test_build_pack_aware_install_profile(tmp_path: Path) -> None:
    profile = build_pack_aware_install_profile("founder_ops_starter", tmp_path)
    assert profile.pack_id == "founder_ops_starter"
    assert len(profile.runtime_prerequisites) >= 1
    assert len(profile.required_capabilities) >= 1


def test_build_field_deployment_profile(tmp_path: Path) -> None:
    profile = build_field_deployment_profile("analyst_starter", tmp_path)
    assert profile.pack_id == "analyst_starter"
    assert profile.profile_id == "field_analyst_starter"
    assert isinstance(profile.first_value_run_command, str)


def test_build_update_plan(tmp_path: Path) -> None:
    plan = build_update_plan(repo_root=tmp_path)
    assert plan.plan_id == "update_plan"
    assert isinstance(plan.steps, list)
    assert isinstance(plan.risks, list)
    text = format_update_plan(plan)
    assert "Update plan" in text
    assert "Steps" in text


def test_update_plan_with_desired(tmp_path: Path) -> None:
    desired = {"readiness": {"ready_for_first_real_user_install": True}}
    plan = build_update_plan(repo_root=tmp_path, desired_state=desired)
    assert len(plan.steps) >= 0
    assert "Reversible" in format_update_plan(plan) or "reversible" in format_update_plan(plan).lower()


def test_build_field_checklist(tmp_path: Path) -> None:
    checklist = build_field_checklist("developer_starter", tmp_path)
    assert checklist["pack_id"] == "developer_starter"
    assert "runtime_prerequisites" in checklist
    assert "commands" in checklist
    assert "workflow-dataset" in str(checklist["commands"])


def test_format_field_checklist() -> None:
    checklist = {"pack_id": "x", "pack_name": "X", "runtime_prerequisites": ["a"], "first_value_run_command": "cmd", "commands": ["c1"]}
    text = format_field_checklist(checklist)
    assert "Field deployment checklist" in text
    assert "a" in text
    assert "cmd" in text


def test_list_checklist_packs() -> None:
    packs = list_checklist_packs()
    assert "founder_ops_starter" in packs
    assert "analyst_starter" in packs
    assert "developer_starter" in packs
    assert "document_worker_starter" in packs


def test_build_deploy_readiness(tmp_path: Path) -> None:
    r = build_deploy_readiness(tmp_path)
    assert "install_check_passed" in r
    assert "package_ready_for_first_user" in r
    assert "rollout_demo_ready" in r
    assert "summary" in r


def test_format_deploy_readiness(tmp_path: Path) -> None:
    text = format_deploy_readiness(tmp_path)
    assert "Deploy readiness" in text
    assert "Install check" in text
    assert "Summary" in text


def test_partial_blocked_deployment_behavior(tmp_path: Path) -> None:
    """With no profile/readiness, bundle and update plan still produce valid structures."""
    bundle = build_install_bundle(repo_root=tmp_path)
    assert bundle.bundle_id
    plan = build_update_plan(repo_root=tmp_path)
    assert plan.reversible_overall in (True, False)
    checklist = build_field_checklist("founder_ops_starter", tmp_path)
    assert checklist["pack_id"] == "founder_ops_starter"


def test_build_handoff_pack(tmp_path: Path) -> None:
    """Handoff pack contains install_profile, readiness_summary, support_bundle_pointers, runbooks, first_value_launch_instructions, known_limitations."""
    pack = build_handoff_pack("founder_ops_starter", tmp_path)
    assert pack["pack_id"] == "founder_ops_starter"
    assert "install_profile" in pack
    assert "readiness_summary" in pack
    assert "support_bundle_pointers" in pack
    assert "runbooks" in pack
    assert "first_value_launch_instructions" in pack
    assert "known_limitations" in pack
    assert len(pack["known_limitations"]) >= 1
    assert len(pack["support_bundle_pointers"]) >= 1


def test_write_handoff_pack(tmp_path: Path) -> None:
    """write_handoff_pack creates directory with HANDOFF_README.md and handoff_summary.json."""
    out_dir = tmp_path / "handoff_out"
    path = write_handoff_pack("analyst_starter", repo_root=tmp_path, output_dir=out_dir)
    assert path == out_dir
    assert (path / "HANDOFF_README.md").exists()
    assert (path / "handoff_summary.json").exists()
    content = (path / "HANDOFF_README.md").read_text(encoding="utf-8")
    assert "Handoff pack" in content
    assert "analyst" in content.lower() or "Analyst" in content
    assert "Known limitations" in content


def test_format_release_bundle_summary(tmp_path: Path) -> None:
    """Release bundle summary includes pack, readiness, support bundle, first-value, runbooks, limitations."""
    summary = format_release_bundle_summary(pack_id="developer_starter", repo_root=tmp_path)
    assert "Release bundle summary" in summary
    assert "developer_starter" in summary
    assert "Readiness" in summary
    assert "Support bundle" in summary
    assert "First-value" in summary
    assert "Runbooks" in summary
    assert "Known limitations" in summary
