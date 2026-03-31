"""Summary reflects last execution after supervised run."""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.capability_discovery.approval_registry import ApprovalRegistry, save_approval_registry
from workflow_dataset.local_operator.action_proposals import propose_local_actions
from workflow_dataset.local_operator.execution_controller import run_supervised_execution
from workflow_dataset.local_operator.setup import build_setup_status
from workflow_dataset.local_operator.summary import build_operator_state_summary


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


def test_summary_last_execution_after_inspect(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    (root / "README.md").write_text("# x")
    reg = ApprovalRegistry(
        approved_paths=[_approved_path(str(root))],
        approved_action_scopes=[
            {"adapter_id": "file_ops", "action_id": "inspect_path", "executable": True},
        ],
    )
    save_approval_registry(reg, tmp_path)
    build_setup_status(tmp_path)
    propose_local_actions(repo_root=tmp_path)
    state = __import__(
        "workflow_dataset.local_operator.state_store", fromlist=["load_operator_state"]
    ).load_operator_state(tmp_path)
    prop = next(p for p in state["action_proposals"] if p.get("action_type") == "inspect_path")
    run_supervised_execution(prop["action_id"], approved=True, repo_root=tmp_path)
    s = build_operator_state_summary(tmp_path)
    assert s.get("last_execution")
    assert s["last_execution"].get("success") is True
    assert s["last_execution"].get("action_id") == prop["action_id"]
