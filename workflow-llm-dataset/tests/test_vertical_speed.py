"""
M47E–M47H: Tests for vertical workflow speed and friction reduction.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from workflow_dataset.vertical_speed.models import (
    FrequentWorkflow,
    FrictionCluster,
    FastPath,
    CommonLoopBundle,
    WorkflowKind,
    FrictionKind,
    SpeedUpCandidate,
)
from workflow_dataset.vertical_speed.identification import (
    list_frequent_workflows,
    get_top_workflows,
)
from workflow_dataset.vertical_speed.friction import (
    build_friction_clusters,
    get_speed_up_candidates,
    get_repeat_value_bottlenecks,
)
from workflow_dataset.vertical_speed.action_route import (
    route_item_to_action,
    get_grouped_review_recommendation,
)
from workflow_dataset.vertical_speed.repeat_value import (
    get_morning_first_action_prefill,
    get_blocked_recovery_suggestion,
    repeat_value_report,
)
from workflow_dataset.vertical_speed.mission_control import vertical_speed_slice
from workflow_dataset.vertical_speed.fast_paths import (
    list_fast_paths,
    get_fast_path_by_workflow_id,
    get_fast_path_by_path_id,
)
from workflow_dataset.vertical_speed.common_loop_bundles import (
    list_common_loop_bundles,
    get_common_loop_bundle,
    get_bundles_for_workflow,
)
from workflow_dataset.vertical_speed.compression_report import build_compression_report


def test_frequent_workflow_model() -> None:
    w = FrequentWorkflow(
        workflow_id="morning_entry_first_action",
        kind=WorkflowKind.morning_entry_first_action,
        label="Morning entry → first action",
        estimated_frequency="daily",
        current_step_count=4,
        suggested_step_count=2,
    )
    assert w.workflow_id == "morning_entry_first_action"
    assert w.kind == WorkflowKind.morning_entry_first_action
    d = w.to_dict()
    assert d["workflow_id"] == w.workflow_id
    assert d["estimated_frequency"] == "daily"


def test_list_frequent_workflows() -> None:
    workflows = list_frequent_workflows()
    assert len(workflows) >= 5
    ids = [w.workflow_id for w in workflows]
    assert "morning_entry_first_action" in ids
    assert "queue_item_to_action" in ids
    assert "review_item_to_decision" in ids


def test_get_top_workflows() -> None:
    data = get_top_workflows(limit=3)
    assert len(data) <= 3
    assert all("workflow_id" in d and "label" in d for d in data)


def test_build_friction_clusters() -> None:
    clusters = build_friction_clusters()
    assert len(clusters) >= 4
    kinds = [c.kind for c in clusters]
    assert FrictionKind.handoff_overhead in kinds or any(c.cluster_id == "queue_to_action_handoff" for c in clusters)


def test_get_speed_up_candidates() -> None:
    candidates = get_speed_up_candidates(limit=5)
    assert len(candidates) >= 1
    assert all(isinstance(c, SpeedUpCandidate) for c in candidates)
    assert any("route" in c.route_to_action.lower() or "continuity" in c.route_to_action.lower() for c in candidates)


def test_route_item_to_action_no_history() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        result = route_item_to_action(item_id=None, repo_root=root, use_first_if_no_id=True)
    assert "command" in result
    assert result["command"]
    assert "workflow-dataset" in result["command"]


def test_get_grouped_review_recommendation() -> None:
    result = get_grouped_review_recommendation()
    assert "recommended" in result
    assert "command" in result
    assert "count" in result


def test_get_morning_first_action_prefill() -> None:
    result = get_morning_first_action_prefill()
    assert "prefilled_command" in result
    assert result["prefilled_command"]


def test_get_blocked_recovery_suggestion() -> None:
    result = get_blocked_recovery_suggestion()
    assert "suggestion" in result
    assert "workflow-dataset" in result["suggestion"]


def test_repeat_value_report() -> None:
    data = repeat_value_report()
    assert "morning_prefill" in data
    assert "grouped_review" in data
    assert "blocked_recovery" in data
    assert "bottlenecks" in data
    assert "next_recommended" in data


def test_vertical_speed_slice() -> None:
    slice_data = vertical_speed_slice()
    assert "vertical_pack_id" in slice_data
    assert "highest_frequency_workflow_id" in slice_data
    assert "biggest_friction_cluster_id" in slice_data
    assert "strongest_speed_up_candidate_id" in slice_data
    assert "next_recommended_friction_reduction_action" in slice_data


def test_get_repeat_value_bottlenecks() -> None:
    bottlenecks = get_repeat_value_bottlenecks()
    assert isinstance(bottlenecks, list)
    assert any(b.bottleneck_id == "resume_no_prefill" for b in bottlenecks)


# ----- M47H.1 Fast paths + common-loop bundles -----


def test_list_fast_paths() -> None:
    paths = list_fast_paths()
    assert len(paths) >= 4
    assert all(isinstance(p, FastPath) for p in paths)
    ids = [p.path_id for p in paths]
    assert "morning_entry_fast" in ids
    assert "queue_item_to_action_fast" in ids


def test_get_fast_path_by_workflow_id() -> None:
    p = get_fast_path_by_workflow_id("morning_entry_first_action")
    assert p is not None
    assert p.workflow_id == "morning_entry_first_action"
    assert p.step_count_before >= p.step_count_after
    p_missing = get_fast_path_by_workflow_id("nonexistent_workflow")
    assert p_missing is None


def test_get_fast_path_by_path_id() -> None:
    p = get_fast_path_by_path_id("queue_item_to_action_fast")
    assert p is not None
    assert p.path_id == "queue_item_to_action_fast"
    assert "action-route" in (p.single_command or "")


def test_list_common_loop_bundles() -> None:
    bundles = list_common_loop_bundles()
    assert len(bundles) >= 3
    assert all(isinstance(b, CommonLoopBundle) for b in bundles)
    assert any(b.bundle_id == "morning_loop" for b in bundles)
    assert any(b.bundle_id == "queue_to_action_loop" for b in bundles)


def test_get_common_loop_bundle() -> None:
    b = get_common_loop_bundle("morning_loop")
    assert b is not None
    assert "morning_entry_first_action" in b.workflow_ids
    assert get_common_loop_bundle("nonexistent") is None


def test_get_bundles_for_workflow() -> None:
    bundles = get_bundles_for_workflow("queue_item_to_action")
    assert len(bundles) >= 1
    assert any(b.bundle_id == "queue_to_action_loop" for b in bundles)


def test_build_compression_report() -> None:
    report = build_compression_report()
    assert "compressed_workflow_ids" in report
    assert "still_needs_work_workflow_ids" in report
    assert "workflow_entries" in report
    assert report["compressed_count"] + report["still_needs_work_count"] == len(report["workflow_entries"])
    assert "morning_entry_first_action" in report["compressed_workflow_ids"]
    assert "operator_routine_to_execution" in report["still_needs_work_workflow_ids"] or "vertical_draft_to_completion" in report["still_needs_work_workflow_ids"]


def test_vertical_speed_slice_includes_compression() -> None:
    slice_data = vertical_speed_slice()
    assert "compressed_workflow_count" in slice_data
    assert "still_needs_work_workflow_ids" in slice_data
