"""Tests for local operator action proposals."""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.capability_discovery.approval_registry import ApprovalRegistry, save_approval_registry
from workflow_dataset.local_operator.action_proposals import propose_local_actions


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


def test_action_proposals_include_required_fields(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "a.txt").write_text("x")

    reg = ApprovalRegistry(approved_paths=[_approved_path(str(root))])
    save_approval_registry(reg, tmp_path)

    state = propose_local_actions(repo_root=tmp_path)
    proposals = state.get("action_proposals") or []
    assert proposals, "expected at least one proposal"
    p = proposals[0]
    assert "risk_tier" in p
    assert "destructive" in p
    assert "reversible" in p
    assert "approval_requirement" in p
    assert "execution_scope" in p
    assert "required_adapter" in p
    assert "required_permissions" in p
    assert "scope_origin" in p
    assert p.get("rollback_feasible") is True
    assert "rollback_method" in p
