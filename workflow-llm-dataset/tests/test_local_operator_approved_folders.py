"""Approved-folder registry behavior (local_operator.approved_folders)."""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.local_operator.approved_folders import (
    add_approved_folder,
    list_approved_folders,
    revoke_approved_folder,
)


def test_add_list_revoke_path(tmp_path: Path) -> None:
    add_approved_folder(
        "data/local/ws",
        ops=["read", "open"],
        repo_root=tmp_path,
    )
    entries = list_approved_folders(tmp_path)
    paths = [e["path"] for e in entries]
    assert "data/local/ws" in paths
    active = [e for e in entries if e["path"] == "data/local/ws"]
    assert active[0]["revocation_state"] == "active"

    revoke_approved_folder("data/local/ws", repo_root=tmp_path)
    entries2 = list_approved_folders(tmp_path)
    revoked = next(e for e in entries2 if e["path"] == "data/local/ws")
    assert revoked["revocation_state"] == "revoked"
