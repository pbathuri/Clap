"""
M23N: Tests for first-run onboarding, bootstrap profile, approval bootstrap.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.onboarding.bootstrap_profile import (
    BootstrapProfile,
    build_bootstrap_profile,
    load_bootstrap_profile,
    save_bootstrap_profile,
    get_bootstrap_profile_path,
)
from workflow_dataset.onboarding.onboarding_flow import (
    get_onboarding_status,
    run_onboarding_flow,
    format_onboarding_status,
)
from workflow_dataset.onboarding.product_summary import (
    build_first_run_summary,
    format_first_run_summary,
)
from workflow_dataset.onboarding.approval_bootstrap import (
    collect_approval_requests,
    format_approval_bootstrap_summary,
    apply_approval_choices,
)
from workflow_dataset.capability_discovery.approval_registry import (
    load_approval_registry,
    ApprovalRegistry,
)


def test_bootstrap_profile_path(tmp_path: Path) -> None:
    path = get_bootstrap_profile_path(tmp_path)
    assert path == tmp_path / "data/local/onboarding/bootstrap_profile.yaml"
    assert "onboarding" in str(path)


def test_build_bootstrap_profile(tmp_path: Path) -> None:
    profile = build_bootstrap_profile(repo_root=tmp_path)
    assert isinstance(profile, BootstrapProfile)
    assert profile.machine_id != ""
    assert profile.repo_root == str(tmp_path.resolve())
    assert profile.created_at != ""
    assert "file_ops" in profile.adapter_ids or len(profile.adapter_ids) >= 1
    assert isinstance(profile.adapters_available, list)
    assert isinstance(profile.capabilities_summary, dict)
    assert isinstance(profile.trusted_real_actions, list)
    assert isinstance(profile.simulate_only_adapters, list)
    assert isinstance(profile.recommended_job_packs, list)


def test_save_and_load_bootstrap_profile(tmp_path: Path) -> None:
    profile = build_bootstrap_profile(repo_root=tmp_path)
    path = save_bootstrap_profile(profile, tmp_path)
    assert path.exists()
    loaded = load_bootstrap_profile(tmp_path)
    assert loaded is not None
    assert loaded.machine_id == profile.machine_id
    assert loaded.repo_root == profile.repo_root
    assert len(loaded.adapter_ids) == len(profile.adapter_ids)


def test_load_bootstrap_profile_missing(tmp_path: Path) -> None:
    loaded = load_bootstrap_profile(tmp_path)
    assert loaded is None


def test_get_onboarding_status(tmp_path: Path) -> None:
    status = get_onboarding_status(repo_root=tmp_path)
    assert "profile_path" in status
    assert "profile_exists" in status
    assert "env_ready" in status or "edge_ready" in status
    assert "approval_summary" in status
    assert "recommended_next_steps" in status
    assert status.get("profile") is not None


def test_format_onboarding_status(tmp_path: Path) -> None:
    status = get_onboarding_status(repo_root=tmp_path)
    text = format_onboarding_status(status)
    assert "Onboarding status" in text
    assert "Approval summary" in text
    assert "Recommended next steps" in text or "Blocked" in text


def test_run_onboarding_flow_persist(tmp_path: Path) -> None:
    result = run_onboarding_flow(repo_root=tmp_path, persist_profile=True)
    assert result.get("profile_exists") is True
    assert get_bootstrap_profile_path(tmp_path).exists()


def test_build_first_run_summary(tmp_path: Path) -> None:
    summary = build_first_run_summary(repo_root=tmp_path)
    assert "what_can_do_safely" in summary
    assert "trusted_benchmarked" in summary
    assert "simulate_only" in summary
    assert "recommended_first_workflow" in summary
    assert isinstance(summary["what_can_do_safely"], list)
    assert summary["recommended_first_workflow"] in (
        "workflow-dataset onboard bootstrap",
        "workflow-dataset console",
    ) or "workflow-dataset" in summary["recommended_first_workflow"]


def test_format_first_run_summary(tmp_path: Path) -> None:
    summary = build_first_run_summary(repo_root=tmp_path)
    text = format_first_run_summary(summary=summary)
    assert "First-run product summary" in text
    assert "What the product can do safely" in text
    assert "Recommended first workflow" in text


def test_collect_approval_requests(tmp_path: Path) -> None:
    requests = collect_approval_requests(repo_root=tmp_path)
    assert "suggested_paths" in requests
    assert "suggested_action_scopes" in requests
    assert "consequence_if_refuse" in requests
    assert "consequence_if_approve" in requests
    assert "data/local" in str(requests.get("suggested_paths", []))


def test_format_approval_bootstrap_summary(tmp_path: Path) -> None:
    requests = collect_approval_requests(repo_root=tmp_path)
    text = format_approval_bootstrap_summary(requests)
    assert "Approval bootstrap" in text
    assert "Suggested paths" in text or "suggested paths" in text.lower()
    assert "If you refuse" in text
    assert "If you approve" in text


def test_apply_approval_choices_creates_registry(tmp_path: Path) -> None:
    path = apply_approval_choices(
        repo_root=tmp_path,
        approve_paths=["data/local", "data/local/workspaces"],
        merge_with_existing=False,
    )
    assert path.exists()
    # path = repo_root/data/local/capability_discovery/approvals.yaml -> repo_root = path.parent.parent.parent.parent
    repo_root = path.parent.parent.parent.parent
    reg = load_approval_registry(repo_root)
    assert "data/local" in reg.approved_paths
    assert "data/local/workspaces" in reg.approved_paths


def test_apply_approval_choices_refusal_omits(tmp_path: Path) -> None:
    path1 = apply_approval_choices(
        repo_root=tmp_path,
        approve_paths=["data/local", "data/local/workspaces"],
        merge_with_existing=False,
    )
    repo_root = path1.parent.parent.parent.parent
    apply_approval_choices(
        repo_root=repo_root,
        refuse_paths=["data/local/workspaces"],
        merge_with_existing=True,
    )
    reg = load_approval_registry(repo_root)
    assert "data/local" in reg.approved_paths
    assert "data/local/workspaces" not in reg.approved_paths


def test_apply_approval_choices_approve_scopes(tmp_path: Path) -> None:
    path = apply_approval_choices(
        repo_root=tmp_path,
        approve_scopes=[
            {"adapter_id": "file_ops", "action_id": "inspect_path"},
            {"adapter_id": "notes_document", "action_id": "read_text"},
        ],
        merge_with_existing=False,
    )
    repo_root = path.parent.parent.parent.parent
    reg = load_approval_registry(repo_root)
    assert len(reg.approved_action_scopes) == 2
    adapter_actions = {(s["adapter_id"], s["action_id"]) for s in reg.approved_action_scopes}
    assert ("file_ops", "inspect_path") in adapter_actions
    assert ("notes_document", "read_text") in adapter_actions
