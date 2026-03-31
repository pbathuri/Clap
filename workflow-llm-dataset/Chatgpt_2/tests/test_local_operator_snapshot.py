"""Operator summary / snapshot shape for shell and edge surfaces."""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.local_operator.snapshot import export_operator_summary_for_surfaces


def test_export_operator_summary_required_keys(tmp_path: Path) -> None:
    s = export_operator_summary_for_surfaces(tmp_path)
    assert "machine_readiness" in s
    assert "operator_readiness" in s
    assert "approved_folders" in s
    assert "count" in s["approved_folders"]
    assert "workflow_tree" in s
    assert "node_count" in s["workflow_tree"]
    assert "tool_registry" in s
    assert "action_proposals" in s
    assert "session_trust" in s
    assert "capability_trust" in s
    assert "last_execution" in s
    assert "updated_at" in s
