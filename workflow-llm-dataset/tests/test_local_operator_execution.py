"""Tests for local operator execution and audit log rollback fields."""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.capability_discovery.approval_registry import ApprovalRegistry, save_approval_registry
from workflow_dataset.local_operator.execution import execute_action_proposal


def _approved_path(path: str) -> dict:
    return {
        "path": path,
        "allowed_operations": ["read"],
        "recursive": True,
        "inherit_mode": "inherit",
        "sensitivity_tag": "unspecified",
        "approval_source": "explicit_user",
        "revocation_state": "active",
        "approved_at": "",
        "reviewed_at": "",
        "expires_at": "",
    }


def test_execute_action_logs_rollback_fields(tmp_path: Path) -> None:
    target = tmp_path / "f.txt"
    target.write_text("x")
    reg = ApprovalRegistry(
        approved_paths=[_approved_path(str(tmp_path))],
        approved_action_scopes=[
            {"adapter_id": "file_ops", "action_id": "inspect_path", "executable": True},
        ],
    )
    save_approval_registry(reg, tmp_path)

    action = {
        "action_id": "inspect_tmp",
        "label": "Inspect file",
        "adapter_id": "file_ops",
        "action_type": "inspect_path",
        "params": {"path": str(target)},
        "risk_tier": "low",
        "destructive": False,
        "reversible": True,
        "approval_requirement": "explicit",
        "execution_scope": {"paths": [str(target)]},
        "required_adapter": "file_ops",
        "scope_origin": "approved_folder",
    }
    result = execute_action_proposal(action, repo_root=tmp_path, approved=True)
    assert result.get("success") is True
    log = result.get("log_record") or {}
    assert "rollback_feasible" in log
    assert "rollback_method" in log
