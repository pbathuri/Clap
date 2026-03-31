"""Execution controller gating: no execute without approval + registered proposal."""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.capability_discovery.approval_registry import ApprovalRegistry, save_approval_registry
from workflow_dataset.local_operator.action_proposals import propose_local_actions
from workflow_dataset.local_operator.execution_controller import (
    ExecutionController,
    gate_execution,
    run_supervised_execution,
)


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


def test_gate_rejects_without_approval(tmp_path: Path) -> None:
    g = gate_execution("any-id", approved=False, repo_root=tmp_path)
    assert g.allowed is False
    assert g.reason == "approval_required"


def test_run_supervised_without_approval(tmp_path: Path) -> None:
    r = run_supervised_execution("x", approved=False, repo_root=tmp_path)
    assert r["success"] is False
    assert r.get("gate_reason") == "approval_required"


def test_run_supervised_unknown_proposal(tmp_path: Path) -> None:
    r = run_supervised_execution("nonexistent-act", approved=True, repo_root=tmp_path)
    assert r["success"] is False
    assert r.get("gate_reason") == "proposal_not_found"


def test_controller_execute_after_proposals(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    (root / "f.txt").write_text("ok")
    reg = ApprovalRegistry(
        approved_paths=[_approved_path(str(root))],
        approved_action_scopes=[
            {"adapter_id": "file_ops", "action_id": "inspect_path", "executable": True},
        ],
    )
    save_approval_registry(reg, tmp_path)
    state = propose_local_actions(repo_root=tmp_path)
    inspect_prop = next(
        p for p in (state.get("action_proposals") or []) if p.get("action_type") == "inspect_path"
    )
    ctrl = ExecutionController()
    r = ctrl.execute(inspect_prop["action_id"], approved=True, repo_root=tmp_path)
    assert r["success"] is True
    log = r.get("log_record") or {}
    assert log.get("rollback_feasible") is True
