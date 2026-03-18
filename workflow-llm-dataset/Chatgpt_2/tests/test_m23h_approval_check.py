"""M23H: Approval check module — execution gating by registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.capability_discovery.approval_check import check_execution_allowed
from workflow_dataset.capability_discovery.approval_registry import (
    ApprovalRegistry,
    get_registry_path,
    save_approval_registry,
)


def test_check_allowed_when_registry_file_missing(tmp_path):
    """When approvals.yaml does not exist, check_execution_allowed returns (True, '')."""
    allowed, msg = check_execution_allowed(
        "file_ops", "inspect_path", {"path": "/tmp"}, repo_root=tmp_path
    )
    assert allowed is True
    assert msg == ""


def test_check_refused_when_scope_not_listed(tmp_path):
    """When registry exists and approved_action_scopes is non-empty, unlisted action is refused."""
    reg = ApprovalRegistry(
        approved_paths=[],
        approved_apps=[],
        approved_action_scopes=[
            {"adapter_id": "notes_document", "action_id": "read_text", "executable": True},
        ],
    )
    save_approval_registry(reg, tmp_path)
    allowed, msg = check_execution_allowed(
        "file_ops", "inspect_path", {"path": str(tmp_path)}, repo_root=tmp_path
    )
    assert allowed is False
    assert "approved_action_scopes" in msg
    assert "file_ops" in msg or "inspect_path" in msg


def test_check_allowed_when_scope_listed(tmp_path):
    """When action is in approved_action_scopes with executable=true, allowed."""
    reg = ApprovalRegistry(
        approved_paths=[],
        approved_action_scopes=[
            {"adapter_id": "file_ops", "action_id": "list_directory", "executable": True},
        ],
    )
    save_approval_registry(reg, tmp_path)
    allowed, msg = check_execution_allowed(
        "file_ops", "list_directory", {"path": str(tmp_path)}, repo_root=tmp_path
    )
    assert allowed is True
    assert msg == ""


def test_check_refused_when_scope_executable_false(tmp_path):
    """When action is in approved_action_scopes with executable=false, refused."""
    reg = ApprovalRegistry(
        approved_paths=[],
        approved_action_scopes=[
            {"adapter_id": "file_ops", "action_id": "inspect_path", "executable": False},
        ],
    )
    save_approval_registry(reg, tmp_path)
    allowed, msg = check_execution_allowed(
        "file_ops", "inspect_path", {"path": str(tmp_path)}, repo_root=tmp_path
    )
    assert allowed is False
    assert "approved_action_scopes" in msg or "executable" in msg


def test_check_path_refused_when_not_under_approved(tmp_path):
    """When approved_paths is non-empty and path is not under any, refused."""
    allowed_dir = tmp_path / "allowed"
    allowed_dir.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    reg = ApprovalRegistry(
        approved_paths=[str(allowed_dir)],
        approved_action_scopes=[
            {"adapter_id": "file_ops", "action_id": "inspect_path", "executable": True},
        ],
    )
    save_approval_registry(reg, tmp_path)
    allowed, msg = check_execution_allowed(
        "file_ops", "inspect_path", {"path": str(other)}, repo_root=tmp_path
    )
    assert allowed is False
    assert "approved_paths" in msg or "Path not in" in msg


def test_check_path_allowed_when_under_approved(tmp_path):
    """When path is under an approved_paths entry, allowed."""
    allowed_dir = tmp_path / "allowed"
    allowed_dir.mkdir()
    f = allowed_dir / "f.txt"
    f.write_text("x")
    reg = ApprovalRegistry(
        approved_paths=[str(allowed_dir)],
        approved_action_scopes=[
            {"adapter_id": "file_ops", "action_id": "inspect_path", "executable": True},
        ],
    )
    save_approval_registry(reg, tmp_path)
    allowed, msg = check_execution_allowed(
        "file_ops", "inspect_path", {"path": str(f)}, repo_root=tmp_path
    )
    assert allowed is True
    assert msg == ""
