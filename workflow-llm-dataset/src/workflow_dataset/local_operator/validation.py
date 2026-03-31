"""
Surface coherence validation across CLI, console, and shell snapshot.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.local_operator.summary import build_operator_state_summary
from workflow_dataset.live_desktop_adapter.models import RefreshPolicy
from workflow_dataset.live_desktop_adapter.pipeline import build_live_adapter_snapshot


REQUIRED_SUMMARY_KEYS = (
    "machine_readiness",
    "operator_readiness",
    "approved_folders",
    "workflow_tree",
    "tool_registry",
    "action_proposals",
    "last_execution",
)


def validate_surface_coherence(repo_root=None) -> dict[str, Any]:
    errors: list[str] = []
    summary = build_operator_state_summary(repo_root)
    for key in REQUIRED_SUMMARY_KEYS:
        if key not in summary:
            errors.append(f"summary_missing:{key}")
    mr = summary.get("machine_readiness") or {}
    if not mr.get("platform"):
        errors.append("machine_readiness_not_populated")
    op = summary.get("operator_readiness") or {}
    if op.get("workflow_node_count") is None:
        errors.append("operator_readiness_not_populated")

    pol = RefreshPolicy(
        timeout_seconds=6.0,
        merge_last_good_cache=False,
        skip_slow_text_fetchers=True,
        presenter_fast_path=False,
        max_parallel_wait_seconds=8.0,
    )
    snap = build_live_adapter_snapshot(repo_root, pol)
    snap_summary = snap.get("local_operator_summary") or {}
    for key in REQUIRED_SUMMARY_KEYS:
        if key not in snap_summary:
            errors.append(f"snapshot_missing:{key}")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "summary_keys": sorted(list(summary.keys())),
        "snapshot_keys": sorted(list(snap_summary.keys())),
    }
