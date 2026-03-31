"""Documentation placeholder paths must not drive ingest/proposals."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.capability_discovery.approval_registry import (
    ApprovalRegistry,
    is_documentation_placeholder_path,
    normalize_approved_paths,
    save_approval_registry,
)
from workflow_dataset.local_operator.action_proposals import propose_local_actions
from workflow_dataset.local_operator.ingest import ingest_approved_folders


@pytest.mark.parametrize(
    "p",
    ["/path/to/folder", "path/to/folder", "/path/to/project"],
)
def test_is_placeholder(p: str) -> None:
    assert is_documentation_placeholder_path(p) is True


def test_real_path_not_placeholder(tmp_path: Path) -> None:
    assert is_documentation_placeholder_path(str(tmp_path / "proj")) is False


def test_ingest_ignores_placeholder_registry(tmp_path: Path) -> None:
    reg = ApprovalRegistry(
        approved_paths=[
            {
                "path": "/path/to/folder",
                "allowed_operations": ["read"],
                "recursive": True,
                "inherit_mode": "inherit",
                "sensitivity_tag": "unspecified",
                "approval_source": "explicit_user",
                "revocation_state": "active",
                "approved_at": "",
                "reviewed_at": "",
                "expires_at": "",
            },
        ],
    )
    save_approval_registry(reg, tmp_path)
    state = ingest_approved_folders(repo_root=tmp_path)
    assert state.get("workflow_tree") == []
    assert state.get("approved_folders") == []


def test_ingest_keeps_real_path_alongside_placeholder(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    (real / "README.md").write_text("# x")
    reg = ApprovalRegistry(
        approved_paths=[
            {"path": "/path/to/folder", "allowed_operations": ["read"]},
            {"path": str(real), "allowed_operations": ["read"]},
        ],
    )
    save_approval_registry(reg, tmp_path)
    state = ingest_approved_folders(repo_root=tmp_path)
    assert len(state.get("workflow_tree") or []) >= 1


def test_normalize_exclude_template() -> None:
    raw = [{"path": "/path/to/folder"}, {"path": "/real"}]
    out = normalize_approved_paths(raw, exclude_template_paths=True)
    assert len(out) == 1
    assert out[0]["path"] == "/real"
