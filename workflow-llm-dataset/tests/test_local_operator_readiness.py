"""Readiness surfaces always populated (Phase 1.5)."""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.local_operator.readiness import (
    build_machine_readiness,
    build_operator_readiness,
    count_active_approved_folders,
)


def test_machine_readiness_has_platform_and_summary(tmp_path: Path) -> None:
    m = build_machine_readiness(tmp_path)
    assert m.get("platform")
    assert m.get("summary")
    assert "active_approved_folder_count" in m
    assert m["active_approved_folder_count"] == count_active_approved_folders(tmp_path)


def test_clean_repo_no_active_folders_without_registry(tmp_path: Path) -> None:
    """No approvals.yaml → zero active folders (no placeholder inheritance)."""
    assert count_active_approved_folders(tmp_path) == 0
    o = build_operator_readiness(tmp_path)
    assert o["active_approved_folder_count"] == 0
    assert o["workflow_node_count"] == 0


def test_operator_readiness_next_steps_when_empty(tmp_path: Path) -> None:
    o = build_operator_readiness(tmp_path)
    assert o.get("next_steps")
    assert any("approved-folders add" in s for s in o["next_steps"])
