"""
Workflow-tree / task-tree construction from local files.
Produces a formal node list with evidence fields.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from workflow_dataset.utils.hashes import stable_id


_MAX_FILES = 2000


def _scan_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        files.append(p)
        if len(files) >= _MAX_FILES:
            break
    return files


def build_workflow_tree(root: Path | str) -> list[dict[str, Any]]:
    root_path = Path(root).expanduser().resolve()
    files = _scan_files(root_path) if root_path.exists() else []
    nodes: list[dict[str, Any]] = []

    root_id = stable_id("workflow_root", str(root_path), prefix="wf")
    nodes.append({
        "node_id": root_id,
        "node_type": "root",
        "parent_id": "",
        "title": root_path.name,
        "children": [],
        "inferred_tools": [],
        "inferred_data_dependencies": [],
        "evidence_refs": [str(root_path)],
        "evidence_summary": f"Scanned {len(files)} file(s) under {root_path.name}.",
        "confidence": 0.6,
        "confidence_reason": "root_scan",
        "missing_evidence": [],
        "suggested_next_actions": [],
        "execution_eligibility": "approved_scope",
        "metadata": {"path": str(root_path)},
    })

    grouped: dict[str, list[Path]] = defaultdict(list)
    for f in files:
        ext = f.suffix.lower().lstrip(".") or "no_ext"
        grouped[ext].append(f)

    for ext, paths in sorted(grouped.items(), key=lambda x: (-len(x[1]), x[0]))[:50]:
        node_id = stable_id("workflow_cluster", str(root_path), ext, prefix="wf")
        nodes.append({
            "node_id": node_id,
            "node_type": "task_cluster",
            "parent_id": root_id,
            "title": f"{ext} artifacts",
            "children": [],
            "inferred_tools": [],
            "inferred_data_dependencies": [],
            "evidence_refs": [str(p) for p in paths[:25]],
            "evidence_summary": f"Found {len(paths)} file(s) with .{ext} extension.",
            "confidence": 0.5,
            "confidence_reason": "extension_cluster",
            "missing_evidence": [],
            "suggested_next_actions": [],
            "execution_eligibility": "approved_scope",
            "metadata": {"extension": ext, "count": len(paths)},
        })
        nodes[0]["children"].append(node_id)

    return nodes
