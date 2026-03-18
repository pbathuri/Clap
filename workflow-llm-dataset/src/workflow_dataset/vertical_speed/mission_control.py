"""
M47E–M47H: Mission control slice — top workflow, friction cluster, speed-up candidate, repeat-value bottleneck, next action.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.vertical_speed.identification import list_frequent_workflows, _active_vertical_pack_id
from workflow_dataset.vertical_speed.friction import build_friction_clusters, get_speed_up_candidates, get_repeat_value_bottlenecks
from workflow_dataset.vertical_speed.repeat_value import get_morning_first_action_prefill
from workflow_dataset.vertical_speed.compression_report import build_compression_report


def vertical_speed_slice(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Build mission-control slice for vertical speed: highest-frequency workflow, biggest friction, speed-up candidate, bottleneck, next action."""
    root = Path(repo_root).resolve() if repo_root else None
    if not root:
        try:
            from workflow_dataset.path_utils import get_repo_root
            root = Path(get_repo_root()).resolve()
        except Exception:
            root = Path.cwd().resolve()

    workflows = list_frequent_workflows(repo_root=root)
    clusters = build_friction_clusters(repo_root=root)
    candidates = get_speed_up_candidates(repo_root=root, limit=5)
    bottlenecks = get_repeat_value_bottlenecks(repo_root=root)
    morning = get_morning_first_action_prefill(repo_root=root)
    pack_id = _active_vertical_pack_id(root)

    highest_frequency_workflow_id = ""
    highest_frequency_workflow_label = ""
    if workflows:
        w = workflows[0]
        highest_frequency_workflow_id = w.workflow_id
        highest_frequency_workflow_label = w.label

    biggest_friction_cluster_id = ""
    biggest_friction_cluster_label = ""
    if clusters:
        c = clusters[0]
        biggest_friction_cluster_id = c.cluster_id
        biggest_friction_cluster_label = c.label

    strongest_speed_up_candidate_id = ""
    strongest_speed_up_candidate_label = ""
    if candidates:
        s = candidates[0]
        strongest_speed_up_candidate_id = s.candidate_id
        strongest_speed_up_candidate_label = s.label

    recent_repeat_value_bottleneck_id = ""
    if bottlenecks:
        recent_repeat_value_bottleneck_id = bottlenecks[0].bottleneck_id

    next_recommended_friction_reduction = morning.get("prefilled_command", "workflow-dataset vertical-speed top-workflows")
    if candidates:
        next_recommended_friction_reduction = candidates[0].route_to_action or next_recommended_friction_reduction

    # M47H.1: compressed vs still need work
    try:
        compression = build_compression_report(repo_root=root)
        compressed_count = compression.get("compressed_count", 0)
        still_needs_work_workflow_ids = compression.get("still_needs_work_workflow_ids", [])
    except Exception:
        compressed_count = 0
        still_needs_work_workflow_ids = []

    return {
        "vertical_pack_id": pack_id,
        "highest_frequency_workflow_id": highest_frequency_workflow_id,
        "highest_frequency_workflow_label": highest_frequency_workflow_label,
        "biggest_friction_cluster_id": biggest_friction_cluster_id,
        "biggest_friction_cluster_label": biggest_friction_cluster_label,
        "strongest_speed_up_candidate_id": strongest_speed_up_candidate_id,
        "strongest_speed_up_candidate_label": strongest_speed_up_candidate_label,
        "recent_repeat_value_bottleneck_id": recent_repeat_value_bottleneck_id,
        "next_recommended_friction_reduction_action": next_recommended_friction_reduction,
        "workflow_count": len(workflows),
        "friction_cluster_count": len(clusters),
        "speed_up_candidate_count": len(candidates),
        "compressed_workflow_count": compressed_count,
        "still_needs_work_workflow_ids": still_needs_work_workflow_ids,
    }
