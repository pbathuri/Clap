"""Tests for local operator approved-folder ingestion."""

from __future__ import annotations

from pathlib import Path
from shutil import copytree

from workflow_dataset.capability_discovery.approval_registry import ApprovalRegistry, save_approval_registry
from workflow_dataset.local_operator.ingest import ingest_approved_folders
from workflow_dataset.local_operator.state_store import load_operator_state


def _fixture_root() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "local_operator"


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


def test_ingest_approved_folders_builds_workflow_tree(tmp_path: Path) -> None:
    src = _fixture_root() / "project_alpha"
    dst = tmp_path / "project_alpha"
    copytree(src, dst)

    reg = ApprovalRegistry(approved_paths=[_approved_path(str(dst))])
    save_approval_registry(reg, tmp_path)

    result = ingest_approved_folders(repo_root=tmp_path)
    assert "workflow_tree" in result
    nodes = result["workflow_tree"]
    assert len(nodes) >= 1
    assert any(n.get("node_type") == "root" for n in nodes)
    for n in nodes:
        assert "evidence_refs" in n
        assert "evidence_summary" in n
        assert "confidence_reason" in n

    state = load_operator_state(tmp_path)
    assert len(state.get("workflow_tree") or []) == len(nodes)
