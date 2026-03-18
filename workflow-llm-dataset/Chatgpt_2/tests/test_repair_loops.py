"""
M46E–M46H: Tests for repair loops — models, patterns, signal-to-repair, flow, store, no-known-repair, failed rollback.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from workflow_dataset.repair_loops.models import (
    RepairLoop,
    RepairLoopStatus,
    BoundedRepairPlan,
    MaintenanceAction,
    RepairTargetSubsystem,
    RequiredReviewGate,
    ReviewGateKind,
    Precondition,
)
from workflow_dataset.repair_loops.patterns import (
    get_known_pattern,
    list_known_pattern_ids,
    pattern_queue_calmness_retune,
)
from workflow_dataset.repair_loops.signal_to_repair import (
    propose_plan_from_signal,
    propose_plan_from_reliability_run,
    propose_plan_from_drift,
    list_signal_mappings,
)
from workflow_dataset.repair_loops.flow import (
    propose_repair_plan,
    review_repair_plan,
    approve_bounded_repair,
    execute_bounded_repair,
    verify_repair,
    escalate_if_failed,
    rollback_if_needed,
)
from workflow_dataset.repair_loops.store import (
    save_repair_loop,
    load_repair_loop,
    list_repair_loops,
    get_repair_loops_dir,
    get_loops_dir,
)
from workflow_dataset.repair_loops.mission_control import repair_loops_mission_control_slice


def test_repair_loop_model() -> None:
    plan = pattern_queue_calmness_retune("test_plan")
    loop = RepairLoop(
        repair_loop_id="rl_test",
        plan=plan,
        status=RepairLoopStatus.proposed,
        source_signal_id="drift_123",
        source_signal_type="drift",
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )
    assert loop.repair_loop_id == "rl_test"
    assert loop.status == RepairLoopStatus.proposed
    assert loop.plan.plan_id == "test_plan"
    assert len(loop.plan.actions) >= 1
    d = loop.to_dict()
    assert d["repair_loop_id"] == "rl_test"
    assert d["status"] == "proposed"
    assert "plan" in d and "actions" in d["plan"]


def test_known_patterns() -> None:
    ids = list_known_pattern_ids()
    assert "queue_calmness_retune" in ids
    assert "memory_curation_refresh" in ids
    assert "runtime_route_fallback_reset" in ids
    p = get_known_pattern("queue_calmness_retune")
    assert p is not None
    assert p.plan_id == "queue_calmness_retune"
    assert p.required_review_gate is not None
    assert p.required_review_gate.kind == ReviewGateKind.operator_approval
    assert get_known_pattern("nonexistent") is None


def test_propose_plan_from_reliability_run() -> None:
    plan = propose_plan_from_reliability_run("run_abc", "degraded", "packs")
    assert plan is not None
    assert plan.plan_id
    plan_none = propose_plan_from_reliability_run("run_xyz", "pass", "install")
    assert plan_none is None
    plan_blocked = propose_plan_from_reliability_run("run_123", "blocked", "trust")
    assert plan_blocked is not None


def test_propose_plan_from_drift() -> None:
    plan = propose_plan_from_drift("drift_1", "queue")
    assert plan is not None
    plan_mem = propose_plan_from_drift("drift_2", "memory_curation")
    assert plan_mem is not None


def test_propose_plan_from_signal_no_match() -> None:
    plan = propose_plan_from_signal("unknown_type", "sig_1", subsystem="unknown_subsystem")
    assert plan is None


def test_propose_plan_from_signal_with_override() -> None:
    plan = propose_plan_from_signal(
        "reliability_run",
        "run_1",
        subsystem="",
        pattern_id_override="queue_calmness_retune",
    )
    assert plan is not None
    assert "queue" in plan.name.lower() or "calmness" in plan.name.lower()


def test_list_signal_mappings() -> None:
    mappings = list_signal_mappings()
    assert isinstance(mappings, list)
    assert any(m.get("pattern_id") == "queue_calmness_retune" for m in mappings)


def test_repair_loop_creation_and_store() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan = pattern_queue_calmness_retune("store_test")
        loop = propose_repair_plan(
            plan,
            source_signal_id="drift_99",
            source_signal_type="drift",
            repo_root=root,
        )
        assert loop.status == RepairLoopStatus.proposed
        assert loop.repair_loop_id.startswith("rl_")
        loops_dir = get_loops_dir(root)
        assert loops_dir.exists()
        saved = load_repair_loop(loop.repair_loop_id, repo_root=root)
        assert saved is not None
        assert saved.plan.plan_id == "store_test"
        listed = list_repair_loops(limit=10, repo_root=root)
        assert len(listed) >= 1
        assert listed[0]["repair_loop_id"] == loop.repair_loop_id


def test_review_and_approve_flow() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan = pattern_queue_calmness_retune("approve_test")
        loop = propose_repair_plan(plan, source_signal_id="sig_1", source_signal_type="drift", repo_root=root)
        reviewed = review_repair_plan(loop.repair_loop_id, repo_root=root)
        assert reviewed is not None
        assert reviewed.status == RepairLoopStatus.under_review
        approved = approve_bounded_repair(loop.repair_loop_id, approved_by="operator", repo_root=root)
        assert approved is not None
        assert approved.status == RepairLoopStatus.approved
        assert approved.approved_by == "operator"
        assert approved.plan.required_review_gate is not None
        assert approved.plan.required_review_gate.passed is True


def test_execute_requires_approved() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan = pattern_queue_calmness_retune("wrong_state")
        loop = propose_repair_plan(plan, source_signal_id="sig_1", source_signal_type="drift", repo_root=root)
        # Execute without approve must be rejected
        executed = execute_bounded_repair(loop.repair_loop_id, repo_root=root)
        assert executed is None
        approve_bounded_repair(loop.repair_loop_id, repo_root=root)
        executed = execute_bounded_repair(loop.repair_loop_id, repo_root=root)
        assert executed is not None
        assert executed.status in (RepairLoopStatus.verifying, RepairLoopStatus.failed)


def test_verify_requires_verifying_or_executing() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan = pattern_queue_calmness_retune("verify_test")
        loop = propose_repair_plan(plan, source_signal_id="sig_1", source_signal_type="drift", repo_root=root)
        # Verify on proposed loop returns None (not in verifying/executing state)
        verified = verify_repair(loop.repair_loop_id, repo_root=root)
        assert verified is None


def test_escalate_requires_failed_or_rolled_back() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan = pattern_queue_calmness_retune("escalate_test")
        loop = propose_repair_plan(plan, source_signal_id="sig_1", source_signal_type="drift", repo_root=root)
        # Escalate on proposed loop returns None (not in failed/rolled_back state)
        escalated = escalate_if_failed(loop.repair_loop_id, reason="Manual", repo_root=root)
        assert escalated is None


def test_rollback_if_needed_requires_failed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan = pattern_queue_calmness_retune("rollback_test")
        loop = propose_repair_plan(plan, source_signal_id="sig_1", source_signal_type="drift", repo_root=root)
        # Rollback on proposed loop returns None (not in failed state)
        rolled = rollback_if_needed(loop.repair_loop_id, repo_root=root)
        assert rolled is None


def test_mission_control_slice() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        slice_data = repair_loops_mission_control_slice(repo_root=root)
        assert "top_repair_needed_subsystem" in slice_data
        assert "active_repair_loop_id" in slice_data
        assert "failed_repair_requiring_escalation_id" in slice_data
        assert "verified_successful_repair_id" in slice_data
        assert "next_recommended_maintenance_action" in slice_data
        assert "active_repair_loop_count" in slice_data


def test_no_known_repair_case() -> None:
    plan = propose_plan_from_signal("reliability_run", "run_x", subsystem="nonexistent_subsystem_xyz")
    assert plan is None


def test_unsafe_repair_execute_without_approve() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan = pattern_queue_calmness_retune("no_approve")
        loop = propose_repair_plan(plan, source_signal_id="sig_1", source_signal_type="drift", repo_root=root)
        # Do not approve; try execute
        executed = execute_bounded_repair(loop.repair_loop_id, repo_root=root)
        assert executed is None


# ----- M46H.1 Maintenance profiles + safe repair bundles -----
def test_maintenance_profiles() -> None:
    from workflow_dataset.repair_loops.profiles import (
        get_maintenance_profile,
        list_maintenance_profile_ids,
    )
    ids = list_maintenance_profile_ids()
    assert "light_touch" in ids
    assert "balanced" in ids
    assert "production_strict" in ids
    p = get_maintenance_profile("balanced")
    assert p is not None
    assert p.profile_id == "balanced"
    assert p.is_pattern_allowed("queue_calmness_retune")
    assert "benchmark_refresh_rollback" in p.require_council_for_pattern_ids
    g = p.guidance_for_pattern("queue_calmness_retune")
    assert g.kind.value == "do_now"
    g2 = p.guidance_for_pattern("benchmark_refresh_rollback")
    assert g2.kind.value == "schedule_later"


def test_safe_repair_bundles() -> None:
    from workflow_dataset.repair_loops.bundles import (
        get_safe_repair_bundle,
        list_safe_repair_bundle_ids,
        bundle_first_plan,
    )
    ids = list_safe_repair_bundle_ids()
    assert "queue_memory_baseline" in ids
    assert "degraded_runtime_recovery" in ids
    b = get_safe_repair_bundle("queue_memory_baseline")
    assert b is not None
    assert "queue_calmness_retune" in b.pattern_ids
    assert b.do_now_guidance
    assert b.operator_summary
    plan = bundle_first_plan("queue_memory_baseline")
    assert plan is not None
    assert plan.plan_id


def test_propose_with_profile_and_guidance() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan = pattern_queue_calmness_retune("guidance_test")
        loop = propose_repair_plan(
            plan,
            source_signal_id="sig_1",
            source_signal_type="drift",
            maintenance_profile_id="balanced",
            pattern_id="queue_calmness_retune",
            repo_root=root,
        )
        assert loop.maintenance_profile_id == "balanced"
        assert loop.operator_guidance is not None
        assert loop.operator_guidance.kind.value == "do_now"
        loaded = load_repair_loop(loop.repair_loop_id, repo_root=root)
        assert loaded is not None
        assert loaded.operator_guidance is not None
        assert loaded.operator_guidance.reason


def test_propose_with_bundle() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan = pattern_queue_calmness_retune("bundle_test")
        loop = propose_repair_plan(
            plan,
            source_signal_id="drift_1",
            source_signal_type="drift",
            repair_bundle_id="queue_memory_baseline",
            pattern_id="queue_calmness_retune",
            repo_root=root,
        )
        assert loop.repair_bundle_id == "queue_memory_baseline"
        assert loop.operator_guidance is not None
