"""workflow_discovery module emits formal workflow-tree nodes."""

from __future__ import annotations

from pathlib import Path
from shutil import copytree

from workflow_dataset.local_operator.workflow_discovery import build_workflow_tree


def _fixture_root() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "local_operator"


def test_workflow_discovery_formal_tree(tmp_path: Path) -> None:
    src = _fixture_root() / "project_alpha"
    dst = tmp_path / "project_alpha"
    copytree(src, dst)
    nodes = build_workflow_tree(dst)
    assert isinstance(nodes, list)
    assert len(nodes) >= 1
    ids = {n["node_id"] for n in nodes}
    assert len(ids) == len(nodes)
    for n in nodes:
        assert n.get("node_type") in ("root", "task_cluster")
