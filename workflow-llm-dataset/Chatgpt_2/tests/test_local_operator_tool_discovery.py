"""Tests for tool discovery classification."""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.capability_discovery.approval_registry import ApprovalRegistry, save_approval_registry
from workflow_dataset.local_operator.tool_discovery import discover_tools


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


def test_tool_discovery_classification(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "project.code-workspace").write_text("{}", encoding="utf-8")
    (workspace / "design.fig").write_text("fig", encoding="utf-8")

    reg = ApprovalRegistry(approved_paths=[_approved_path(str(workspace))])
    save_approval_registry(reg, tmp_path)

    apps_dir = tmp_path / "Applications"
    (apps_dir / "Visual Studio Code.app").mkdir(parents=True)

    tools = discover_tools(repo_root=tmp_path, apps_dir=apps_dir)
    by_id = {t["tool_id"]: t for t in tools}
    assert by_id["vscode"]["installed"] is True
    assert by_id["vscode"]["inferred"] is True
    assert by_id["vscode"]["adapter_supported"] is True
    assert by_id["vscode"]["permission_ready"] is True
    assert by_id["vscode"]["adapter_mode"] in {"simulated", "supervised_live", "session_trusted_live"}

    assert by_id["figma"]["inferred"] is True
    assert by_id["figma"]["installed"] is False
