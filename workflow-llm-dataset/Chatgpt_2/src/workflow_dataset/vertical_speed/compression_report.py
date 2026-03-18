"""
M47H.1: Operator-facing report — which repeated flows are compressed vs still need work.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.vertical_speed.identification import list_frequent_workflows
from workflow_dataset.vertical_speed.fast_paths import get_fast_path_by_workflow_id
from workflow_dataset.vertical_speed.common_loop_bundles import get_bundles_for_workflow


def build_compression_report(
    repo_root: Path | str | None = None,
    vertical_pack_id: str | None = None,
) -> dict[str, Any]:
    """
    Build report of frequent workflows with compression status:
    - compressed: has a fast path
    - still_needs_work: no fast path yet
    - workflow_entries: per-workflow details (workflow_id, label, compressed, fast_path_id, bundle_ids, recommendation)
    """
    workflows = list_frequent_workflows(repo_root=repo_root, vertical_pack_id=vertical_pack_id)
    compressed_ids: list[str] = []
    still_needs_work_ids: list[str] = []
    entries: list[dict[str, Any]] = []

    for w in workflows:
        fast = get_fast_path_by_workflow_id(w.workflow_id)
        bundles = get_bundles_for_workflow(w.workflow_id)
        bundle_ids = [b.bundle_id for b in bundles]
        compressed = fast is not None
        if compressed:
            compressed_ids.append(w.workflow_id)
        else:
            still_needs_work_ids.append(w.workflow_id)

        if compressed and fast:
            recommendation = f"Use fast path: {fast.single_command or (fast.compressed_steps[0] if fast.compressed_steps else fast.path_id)}"
        else:
            recommendation = "Add fast path or use friction-report / action-route for incremental improvement."

        entries.append({
            "workflow_id": w.workflow_id,
            "label": w.label,
            "compressed": compressed,
            "fast_path_id": fast.path_id if fast else None,
            "bundle_ids": bundle_ids,
            "current_step_count": w.current_step_count,
            "suggested_step_count": w.suggested_step_count,
            "recommendation": recommendation,
        })

    return {
        "compressed_workflow_ids": compressed_ids,
        "still_needs_work_workflow_ids": still_needs_work_ids,
        "compressed_count": len(compressed_ids),
        "still_needs_work_count": len(still_needs_work_ids),
        "workflow_entries": entries,
    }
