"""Snapshot summary after real approved-folder registration (no placeholders)."""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.local_operator.approved_folders import add_approved_folder
from workflow_dataset.local_operator.ingest import ingest_approved_folders
from workflow_dataset.local_operator.summary import build_operator_state_summary


def test_summary_workflow_after_add_and_ingest(tmp_path: Path) -> None:
    proj = tmp_path / "real_project"
    proj.mkdir()
    (proj / "README.md").write_text("# app")
    add_approved_folder(str(proj), ops=["read"], repo_root=tmp_path)
    ingest_approved_folders(repo_root=tmp_path)
    s = build_operator_state_summary(tmp_path)
    assert s["machine_readiness"].get("active_approved_folder_count") >= 1
    assert s["workflow_tree"]["node_count"] >= 1
    assert s["approved_folders"]["count"] >= 1
