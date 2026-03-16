"""M23D-F1: Capability discovery and approval registry. Local-only; lightweight."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.capability_discovery import (
    run_scan,
    format_profile_report,
    load_approval_registry,
    save_approval_registry,
    get_registry_path,
    ApprovalRegistry,
    CapabilityProfile,
)


def test_run_scan_returns_profile(tmp_path):
    profile = run_scan(repo_root=tmp_path)
    assert isinstance(profile, CapabilityProfile)
    assert len(profile.adapters_available) >= 4
    adapter_ids = {a.adapter_id for a in profile.adapters_available}
    assert "file_ops" in adapter_ids
    assert "browser_open" in adapter_ids
    assert len(profile.action_scopes) >= 4
    assert "approved_apps" in dir(profile)
    assert "approved_paths" in dir(profile)


def test_run_scan_file_ops_executable_actions():
    profile = run_scan()
    file_ops = next((a for a in profile.adapters_available if a.adapter_id == "file_ops"), None)
    assert file_ops is not None
    assert file_ops.supports_real_execution is True
    assert "inspect_path" in file_ops.executable_action_ids
    assert "list_directory" in file_ops.executable_action_ids


def test_run_scan_browser_open_simulate_only():
    profile = run_scan()
    browser = next((a for a in profile.adapters_available if a.adapter_id == "browser_open"), None)
    assert browser is not None
    assert browser.supports_real_execution is False
    assert browser.supports_simulate is True


def test_format_profile_report_contains_adapters():
    profile = run_scan()
    report = format_profile_report(profile)
    assert "file_ops" in report
    assert "Approved paths" in report or "approved paths" in report.lower()
    assert "Approved apps" in report or "approved apps" in report.lower()
    assert "Action scopes" in report or "action scopes" in report.lower()


def test_approval_registry_load_empty_when_missing(tmp_path):
    reg = load_approval_registry(tmp_path)
    assert reg.approved_paths == []
    assert reg.approved_apps == []
    assert reg.approved_action_scopes == []


def test_approval_registry_save_and_load(tmp_path):
    reg = ApprovalRegistry(
        approved_paths=["/tmp/foo", "data/docs"],
        approved_apps=["Notes", "Safari"],
        approved_action_scopes=[{"adapter_id": "file_ops", "action_id": "inspect_path", "executable": True}],
    )
    path = save_approval_registry(reg, tmp_path)
    assert path.exists()
    loaded = load_approval_registry(tmp_path)
    assert loaded.approved_paths == reg.approved_paths
    assert loaded.approved_apps == reg.approved_apps
    assert len(loaded.approved_action_scopes) == 1
    assert loaded.approved_action_scopes[0]["adapter_id"] == "file_ops"


def test_get_registry_path(tmp_path):
    p = get_registry_path(tmp_path)
    assert "capability_discovery" in str(p)
    assert p.name == "approvals.yaml"


def test_run_scan_uses_approval_registry(tmp_path):
    reg = ApprovalRegistry(approved_paths=["/allowed"], approved_apps=["CustomApp"])
    save_approval_registry(reg, tmp_path)
    profile = run_scan(repo_root=tmp_path, approval_registry=load_approval_registry(tmp_path))
    assert "/allowed" in profile.approved_paths
    assert "CustomApp" in profile.approved_apps
