"""
Approved-folder ingestion for local operator draft.
Scans approved folders and emits workflow/task tree nodes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.capability_discovery.approval_registry import load_approval_registry, normalize_approved_paths
from workflow_dataset.local_operator.state_store import load_operator_state, save_operator_state
from workflow_dataset.local_operator.workflow_tree import build_workflow_tree
from workflow_dataset.personal.project_interpreter import infer_project_roots_from_paths
from workflow_dataset.utils.dates import utc_now_iso


def ingest_approved_folders(repo_root: Path | str | None = None) -> dict[str, Any]:
    registry = load_approval_registry(repo_root)
    approved_entries = normalize_approved_paths(
        registry.approved_paths, exclude_template_paths=True
    )
    active_entries = [e for e in approved_entries if e.get("revocation_state") == "active"]

    read_paths: list[str] = []
    for entry in active_entries:
        ops = list(entry.get("allowed_operations") or [])
        if ops and "read" not in ops:
            continue
        read_paths.append(str(entry.get("path") or ""))
    read_paths = [p for p in read_paths if p]

    roots = infer_project_roots_from_paths(read_paths, repo_root=repo_root)
    nodes: list[dict[str, Any]] = []
    for root in roots:
        nodes.extend(build_workflow_tree(root))

    state = load_operator_state(repo_root)
    state["approved_folders"] = active_entries
    state["workflow_tree"] = nodes
    state["updated_at"] = utc_now_iso()
    save_operator_state(state, repo_root)
    return state
