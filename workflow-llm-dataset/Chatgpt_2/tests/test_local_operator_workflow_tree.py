"""Tests for workflow-tree construction from local files."""

from __future__ import annotations

from pathlib import Path
from shutil import copytree

from workflow_dataset.local_operator.workflow_tree import build_workflow_tree


def _fixture_root() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "local_operator"


def test_build_workflow_tree_includes_evidence_fields(tmp_path: Path) -> None:
    src = _fixture_root() / "project_beta"
    dst = tmp_path / "project_beta"
    copytree(src, dst)

    nodes = build_workflow_tree(dst)
    assert any(n.get("node_type") == "root" for n in nodes)
    for n in nodes:
        assert "evidence_refs" in n
        assert "evidence_summary" in n
        assert "confidence_reason" in n
        assert "parent_id" in n
        assert "inferred_tools" in n
        assert "inferred_data_dependencies" in n
        assert "confidence" in n
        assert "missing_evidence" in n
        assert "suggested_next_actions" in n
        assert "execution_eligibility" in n
