"""
M28E–M28H: Bounded worker lanes — model, store, subplan, execution, handoff, mission control visibility.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.lanes.models import (
    WorkerLane,
    DelegatedSubplan,
    DelegatedSubplanStep,
    LaneScope,
    LanePermissions,
    LaneArtifact,
    LaneFailure,
    LaneHandoff,
    LANE_STATUS_OPEN,
    LANE_STATUS_BLOCKED,
    LANE_STATUS_COMPLETED,
    LANE_PERMISSION_SIMULATE_ONLY,
)
from workflow_dataset.lanes.store import get_lanes_dir, save_lane, load_lane, list_lanes
from workflow_dataset.lanes.subplan import create_delegated_subplan, gather_subplan_context
from workflow_dataset.lanes.execution import (
    run_lane_simulate,
    set_lane_blocked,
    collect_lane_results,
    build_lane_summary,
    deliver_lane_handoff,
)


def test_lane_scope_roundtrip():
    s = LaneScope(scope_id="extract_only", label="Extract", description="Narrow scope", allowed_step_classes=["local_inspect"])
    d = s.to_dict()
    assert d["scope_id"] == "extract_only"
    loaded = LaneScope.from_dict(d)
    assert loaded.label == s.label


def test_delegated_subplan_roundtrip():
    scope = LaneScope(scope_id="default")
    step = DelegatedSubplanStep(step_index=0, label="Step A", expected_outputs=["out1"])
    sub = DelegatedSubplan(subplan_id="sub_1", scope=scope, steps=[step], expected_outputs=["out1"], trust_mode="simulate")
    d = sub.to_dict()
    assert d["subplan_id"] == "sub_1"
    loaded = DelegatedSubplan.from_dict(d)
    assert len(loaded.steps) == 1
    assert loaded.steps[0].label == "Step A"


def test_worker_lane_roundtrip():
    scope = LaneScope(scope_id="default")
    perms = LanePermissions(permission=LANE_PERMISSION_SIMULATE_ONLY)
    lane = WorkerLane(lane_id="lane_1", project_id="p1", goal_id="g_1", scope=scope, permissions=perms, status=LANE_STATUS_OPEN)
    d = lane.to_dict()
    assert d["lane_id"] == "lane_1"
    loaded = WorkerLane.from_dict(d)
    assert loaded.project_id == "p1"
    assert loaded.status == LANE_STATUS_OPEN


def test_lane_store_save_load_list(tmp_path):
    scope = LaneScope(scope_id="default")
    lane = WorkerLane(lane_id="lane_abc", project_id="founder_case_alpha", goal_id="g_123", scope=scope, status=LANE_STATUS_OPEN)
    save_lane(lane, tmp_path)
    assert get_lanes_dir(tmp_path).exists()
    loaded = load_lane("lane_abc", tmp_path)
    assert loaded is not None
    assert loaded.goal_id == "g_123"
    lanes = list_lanes(project_id="founder_case_alpha", repo_root=tmp_path)
    assert len(lanes) >= 1
    assert any(L["lane_id"] == "lane_abc" for L in lanes)


def test_create_delegated_subplan_no_plan():
    sub = create_delegated_subplan(project_id="p1", goal_id="g1", goal_text="Summarize the report", scope_id="default")
    assert sub.subplan_id
    assert len(sub.steps) == 1
    assert "summary" in sub.expected_outputs
    assert "max_steps:" in " ".join(sub.stop_conditions)
    assert "on_blocked" in sub.stop_conditions


def test_create_delegated_subplan_from_plan():
    from workflow_dataset.planner.schema import Plan, PlanStep
    steps = [PlanStep(step_index=0, label="Fetch", step_class="local_inspect", expected_outputs=["data"])]
    plan = Plan(plan_id="plan_1", goal_text="Fetch and summarize", steps=steps)
    sub = create_delegated_subplan(project_id="p1", goal_id="g1", plan=plan, step_indices=[0])
    assert len(sub.steps) == 1
    assert sub.steps[0].label == "Fetch"
    assert sub.parent_plan_id == "plan_1"


def test_run_lane_simulate(tmp_path):
    scope = LaneScope(scope_id="default")
    step = DelegatedSubplanStep(step_index=0, label="Sim step")
    sub = DelegatedSubplan(subplan_id="sub1", scope=scope, steps=[step])
    lane = WorkerLane(lane_id="lane_sim", project_id="p1", goal_id="g1", scope=scope, status=LANE_STATUS_OPEN, subplan=sub)
    save_lane(lane, tmp_path)
    out = run_lane_simulate("lane_sim", tmp_path)
    assert out.get("ok") is True
    assert out.get("status") == LANE_STATUS_COMPLETED
    assert out.get("artifacts_count") >= 1
    loaded = load_lane("lane_sim", tmp_path)
    assert loaded.status == LANE_STATUS_COMPLETED
    assert len(loaded.artifacts) >= 1


def test_set_lane_blocked(tmp_path):
    lane = WorkerLane(lane_id="lane_blk", project_id="p1", goal_id="g1", scope=LaneScope(scope_id="default"), status=LANE_STATUS_OPEN)
    save_lane(lane, tmp_path)
    out = set_lane_blocked("lane_blk", reason="approval_required", step_index=1, repo_root=tmp_path)
    assert out.get("ok") is True
    loaded = load_lane("lane_blk", tmp_path)
    assert loaded.status == LANE_STATUS_BLOCKED
    assert loaded.failure is not None
    assert loaded.failure.reason == "approval_required"


def test_collect_lane_results_and_summary(tmp_path):
    lane = WorkerLane(
        lane_id="lane_res",
        project_id="p1",
        goal_id="g1",
        scope=LaneScope(scope_id="default"),
        status=LANE_STATUS_COMPLETED,
        artifacts=[LaneArtifact(label="report", path_or_type="report.md", step_index=0)],
    )
    save_lane(lane, tmp_path)
    results = collect_lane_results("lane_res", tmp_path)
    assert len(results) == 1
    assert results[0]["label"] == "report"
    summary = build_lane_summary("lane_res", tmp_path)
    assert summary["lane_id"] == "lane_res"
    assert summary["artifacts_count"] == 1


def test_deliver_lane_handoff(tmp_path):
    lane = WorkerLane(
        lane_id="lane_hand",
        project_id="p1",
        goal_id="g1",
        scope=LaneScope(scope_id="default"),
        status=LANE_STATUS_COMPLETED,
        artifacts=[LaneArtifact(label="out", path_or_type="/tmp/out.txt")],
    )
    save_lane(lane, tmp_path)
    out = deliver_lane_handoff("lane_hand", tmp_path)
    assert out.get("ok") is True
    assert out.get("handoff_id")
    loaded = load_lane("lane_hand", tmp_path)
    assert loaded.handoff is not None
    assert loaded.handoff.status == "delivered"


def test_mission_control_worker_lanes_section(tmp_path):
    """Mission control state includes worker_lanes when lanes exist."""
    lane = WorkerLane(lane_id="lane_mc", project_id="proj_1", goal_id="g1", scope=LaneScope(scope_id="default"), status=LANE_STATUS_OPEN)
    save_lane(lane, tmp_path)
    from workflow_dataset.mission_control.state import get_mission_control_state
    state = get_mission_control_state(tmp_path)
    wl = state.get("worker_lanes", {})
    assert "error" not in wl or wl.get("error") is None
    if "error" not in wl:
        assert "active_lanes" in wl
        assert "blocked_lanes" in wl
        assert "results_awaiting_review" in wl
        assert "parent_project_to_lanes" in wl
        assert "next_handoff_needed" in wl


# ----- M28H.1 Lane bundles -----
def test_lane_bundle_roundtrip(tmp_path):
    from workflow_dataset.lanes.bundles import LaneBundle, save_bundle, load_bundle
    scope = LaneScope(scope_id="extract_only", label="Extract")
    bundle = LaneBundle(bundle_id="extract_only", label="Extract only", scope=scope, default_stop_conditions=["max_steps:5"])
    save_bundle(bundle, tmp_path)
    loaded = load_bundle("extract_only", tmp_path)
    assert loaded is not None
    assert loaded.bundle_id == "extract_only"
    assert "max_steps:5" in loaded.default_stop_conditions


def test_ensure_default_bundles_and_list(tmp_path):
    from workflow_dataset.lanes.bundles import ensure_default_bundles, list_bundles
    ensure_default_bundles(tmp_path)
    bundles = list_bundles(repo_root=tmp_path)
    assert len(bundles) >= 2
    ids = [b["bundle_id"] for b in bundles]
    assert "extract_only" in ids
    assert "summarize_only" in ids


# ----- M28H.1 Parent/child review -----
def test_build_parent_child_review(tmp_path):
    from workflow_dataset.lanes.review import build_parent_child_review, format_parent_child_review
    lane = WorkerLane(
        lane_id="lane_rev",
        project_id="proj_r",
        goal_id="g_r",
        scope=LaneScope(scope_id="default"),
        status=LANE_STATUS_COMPLETED,
        artifacts=[LaneArtifact(label="a1", path_or_type="p1")],
        handoff=LaneHandoff(handoff_id="h1", lane_id="lane_rev", project_id="proj_r", goal_id="g_r", status="delivered", summary="done"),
    )
    save_lane(lane, tmp_path)
    r = build_parent_child_review("lane_rev", tmp_path)
    assert r.get("parent_project_id") == "proj_r"
    assert r.get("child_lane_id") == "lane_rev"
    assert r.get("handoff_status") == "delivered"
    assert r.get("recommendation") == "approve"
    text = format_parent_child_review("lane_rev", tmp_path)
    assert "Parent/Child review" in text
    assert "delivered" in text


def test_approve_and_reject_lane_handoff(tmp_path):
    from workflow_dataset.lanes.review import approve_lane_handoff, reject_lane_handoff
    lane = WorkerLane(
        lane_id="lane_apr",
        project_id="p",
        goal_id="g",
        scope=LaneScope(scope_id="default"),
        status=LANE_STATUS_COMPLETED,
        handoff=LaneHandoff(handoff_id="h1", lane_id="lane_apr", project_id="p", goal_id="g", status="delivered"),
    )
    save_lane(lane, tmp_path)
    out = approve_lane_handoff("lane_apr", approved_by="operator", repo_root=tmp_path)
    assert out.get("ok") is True
    assert out.get("status") == "approved"
    loaded = load_lane("lane_apr", tmp_path)
    assert loaded.handoff.status == "approved"
    assert loaded.handoff.approved_by == "operator"

    # reset to delivered for reject test
    loaded.handoff.status = "delivered"
    loaded.handoff.approved_at = ""
    loaded.handoff.approved_by = ""
    save_lane(loaded, tmp_path)
    out2 = reject_lane_handoff("lane_apr", reason="bad quality", rejected_by="operator", repo_root=tmp_path)
    assert out2.get("ok") is True
    loaded2 = load_lane("lane_apr", tmp_path)
    assert loaded2.handoff.status == "rejected"
    assert "bad quality" in loaded2.handoff.rejection_reason


def test_accept_lane_results_into_project(tmp_path):
    from workflow_dataset.lanes.review import approve_lane_handoff, accept_lane_results_into_project
    from workflow_dataset.project_case.store import create_project, get_linked_artifacts
    create_project("proj_accept", repo_root=tmp_path)
    lane = WorkerLane(
        lane_id="lane_acc",
        project_id="proj_accept",
        goal_id="g",
        scope=LaneScope(scope_id="default"),
        status=LANE_STATUS_COMPLETED,
        artifacts=[LaneArtifact(label="report", path_or_type="report.md")],
        handoff=LaneHandoff(handoff_id="h1", lane_id="lane_acc", project_id="proj_accept", goal_id="g", status="delivered"),
    )
    save_lane(lane, tmp_path)
    approve_lane_handoff("lane_acc", approved_by="op", repo_root=tmp_path)
    out = accept_lane_results_into_project("lane_acc", repo_root=tmp_path)
    assert out.get("ok") is True
    assert out.get("status") == "accepted"
    linked = get_linked_artifacts("proj_accept", tmp_path)
    assert any("lane:lane_acc:" in (a.path_or_label) or "report" in (a.path_or_label) for a in linked)


def test_format_lane_trust_readiness(tmp_path):
    from workflow_dataset.lanes.execution import format_lane_trust_readiness, update_lane_trust_readiness
    lane = WorkerLane(lane_id="lane_tr", project_id="p", goal_id="g", scope=LaneScope(scope_id="default"), status=LANE_STATUS_OPEN)
    update_lane_trust_readiness(lane)
    assert lane.trust_summary in ("simulate_only", "")
    assert lane.readiness_status in ("ready", "not_ready", "")
    text = format_lane_trust_readiness(lane)
    assert "trust=" in text
    assert "readiness=" in text
