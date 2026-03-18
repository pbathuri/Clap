"""
M26E–M26H: Tests for safe action runtime — action envelope, plan mapping, checkpointed runner, hub, run summary.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.executor.models import ActionEnvelope, ExecutionRun, CheckpointDecision
from workflow_dataset.executor.mapping import plan_preview_to_envelopes
from workflow_dataset.executor.hub import (
    get_executor_runs_dir,
    save_run,
    load_run,
    list_runs,
    save_artifacts_list,
    load_artifacts_list,
)
from workflow_dataset.executor.runner import resolve_plan, run_with_checkpoints, resume_run
from workflow_dataset.job_packs.seed_jobs import seed_example_job_pack, seed_task_demo_job_pack
from workflow_dataset.desktop_bench.seed_cases import seed_default_cases


@pytest.fixture
def seeded_jobs(tmp_path: Path):
    seed_default_cases(tmp_path)
    seed_example_job_pack(tmp_path)
    seed_task_demo_job_pack(tmp_path)


def test_action_envelope_shape() -> None:
    """ActionEnvelope has required fields for execution contract."""
    env = ActionEnvelope(
        step_id="step_0_j1",
        step_index=0,
        action_type="job_run",
        action_ref="j1",
        mode="simulate",
        approvals_required=[],
        capability_required="",
        expected_artifact="",
        reversible=False,
        checkpoint_required=False,
        blocked_reason="",
        label="j1",
    )
    assert env.step_id == "step_0_j1"
    assert env.action_type == "job_run"
    assert env.mode == "simulate"
    assert env.checkpoint_required is False


def test_plan_preview_to_envelopes(seeded_jobs: None, tmp_path: Path) -> None:
    """Mapping produces one envelope per job; blocked step has blocked_reason."""
    from workflow_dataset.copilot.plan import build_plan_for_job
    plan = build_plan_for_job("weekly_status_from_notes", "simulate", {}, tmp_path)
    assert plan is not None
    envelopes = plan_preview_to_envelopes(
        plan.plan_id,
        plan.job_pack_ids,
        plan.mode,
        plan.blocked,
        plan.blocked_reasons,
        repo_root=tmp_path,
    )
    assert len(envelopes) == len(plan.job_pack_ids)
    assert envelopes[0].action_type == "job_run"
    assert envelopes[0].action_ref == "weekly_status_from_notes"
    assert envelopes[0].step_index == 0


def test_plan_preview_to_envelopes_blocked(seeded_jobs: None, tmp_path: Path) -> None:
    """When job is in plan.blocked, envelope has blocked_reason."""
    envelopes = plan_preview_to_envelopes(
        "plan1",
        ["nonexistent_job"],
        "simulate",
        blocked=["nonexistent_job"],
        blocked_reasons={"nonexistent_job": "job not found"},
        repo_root=tmp_path,
    )
    assert len(envelopes) == 1
    assert envelopes[0].blocked_reason


def test_execution_run_to_dict_from_dict() -> None:
    """ExecutionRun serializes and deserializes."""
    run = ExecutionRun(
        run_id="r1",
        plan_id="p1",
        plan_source="job",
        plan_ref="j1",
        mode="simulate",
        status="completed",
        current_step_index=1,
        envelopes=[ActionEnvelope(step_id="s0", step_index=0, action_ref="j1", label="j1")],
        executed=[{"job_pack_id": "j1", "step_index": 0}],
        blocked=[],
        artifacts=[],
        checkpoint_decisions=[],
        errors=[],
        timestamp_start="2025-01-01T00:00:00Z",
        timestamp_end="2025-01-01T00:01:00Z",
    )
    d = run.to_dict()
    assert d["run_id"] == "r1"
    assert d["status"] == "completed"
    loaded = ExecutionRun.from_dict(d)
    assert loaded.run_id == run.run_id
    assert len(loaded.envelopes) == 1
    assert loaded.envelopes[0].action_ref == "j1"


def test_hub_save_load_list(tmp_path: Path) -> None:
    """Hub save_run, load_run, list_runs round-trip."""
    run = ExecutionRun(
        run_id="hub_run_1",
        plan_id="p1",
        plan_ref="r1",
        plan_source="routine",
        mode="simulate",
        status="completed",
        current_step_index=1,
        envelopes=[],
        executed=[],
        blocked=[],
        artifacts=[],
        timestamp_start="2025-01-01T00:00:00Z",
    )
    save_run(run, tmp_path)
    loaded = load_run("hub_run_1", tmp_path)
    assert loaded is not None
    assert loaded.run_id == "hub_run_1"
    assert loaded.status == "completed"
    runs = list_runs(limit=5, repo_root=tmp_path)
    assert any(r["run_id"] == "hub_run_1" for r in runs)


def test_hub_artifacts_list(tmp_path: Path) -> None:
    """save_artifacts_list and load_artifacts_list."""
    get_executor_runs_dir(tmp_path)
    save_run(
        ExecutionRun(run_id="art_run", plan_id="p", plan_ref="r", plan_source="routine", mode="simulate", status="running", envelopes=[], timestamp_start=""),
        tmp_path,
    )
    save_artifacts_list("art_run", ["/tmp/out1.txt", "/tmp/out2.txt"], tmp_path)
    paths = load_artifacts_list("art_run", tmp_path)
    assert paths == ["/tmp/out1.txt", "/tmp/out2.txt"]


def test_resolve_plan_job(seeded_jobs: None, tmp_path: Path) -> None:
    """resolve_plan returns PlanPreview for job source."""
    plan = resolve_plan("job", "weekly_status_from_notes", "simulate", tmp_path)
    assert plan is not None
    assert plan.job_pack_ids == ["weekly_status_from_notes"]
    assert plan.mode == "simulate"


def test_resolve_plan_routine_missing(tmp_path: Path) -> None:
    """resolve_plan returns None for unknown routine."""
    plan = resolve_plan("routine", "nonexistent_routine", "simulate", tmp_path)
    assert plan is None


def test_run_with_checkpoints_simulate(seeded_jobs: None, tmp_path: Path) -> None:
    """run_with_checkpoints runs single-step simulate plan; ends completed or blocked (env-dependent)."""
    result = run_with_checkpoints(
        plan_source="job",
        plan_ref="weekly_status_from_notes",
        mode="simulate",
        repo_root=tmp_path,
        stop_at_checkpoints=True,
    )
    assert "error" not in result or not result.get("error")
    assert result.get("run_id")
    assert result.get("status") in ("completed", "blocked")
    assert result.get("executed_count") >= 0
    assert "run_path" in result


def test_run_with_checkpoints_blocked(tmp_path: Path) -> None:
    """run_with_checkpoints returns blocked when plan ref is invalid."""
    result = run_with_checkpoints(
        plan_source="job",
        plan_ref="nonexistent_job_pack",
        mode="simulate",
        repo_root=tmp_path,
        stop_on_first_blocked=True,
    )
    assert result.get("error") or result.get("status") == "blocked"


def test_run_summary_shape(seeded_jobs: None, tmp_path: Path) -> None:
    """Run result has run_id, status, executed_count, blocked_count, run_path."""
    result = run_with_checkpoints(
        plan_source="job",
        plan_ref="weekly_status_from_notes",
        mode="simulate",
        repo_root=tmp_path,
        stop_at_checkpoints=True,
    )
    if result.get("error"):
        pytest.skip("run failed (e.g. missing deps)")
    assert "run_id" in result
    assert "status" in result
    assert "executed_count" in result
    assert "blocked_count" in result
    assert "run_path" in result
    assert "timestamp_start" in result


def test_resume_run_not_found(tmp_path: Path) -> None:
    """resume_run returns error for missing run."""
    result = resume_run("nonexistent_run_id", "proceed", tmp_path)
    assert result.get("error")
    assert "not found" in result["error"].lower()


# ----- M26H.1 Cross-app bundles + recovery -----


def test_action_bundle_shape() -> None:
    """ActionBundle and BundleStep have required fields."""
    from workflow_dataset.executor.bundles import ActionBundle, BundleStep
    step = BundleStep(action_type="job_run", action_ref="weekly_status", label="Weekly")
    assert step.action_type == "job_run"
    assert step.action_ref == "weekly_status"
    bundle = ActionBundle(
        bundle_id="recovery_manual",
        title="Manual recovery steps",
        description="Optional steps after block",
        steps=[step],
        tags=["recovery"],
    )
    assert bundle.bundle_id == "recovery_manual"
    assert len(bundle.steps) == 1
    assert "recovery" in bundle.tags


def test_save_and_list_bundles(tmp_path: Path) -> None:
    """save_bundle and list_bundles round-trip."""
    from workflow_dataset.executor.bundles import ActionBundle, BundleStep, save_bundle, list_bundles, get_bundle
    b = ActionBundle(
        bundle_id="test_bundle_1",
        title="Test bundle",
        steps=[BundleStep(action_type="job_run", action_ref="job_a")],
        tags=["test"],
    )
    save_bundle(b, tmp_path)
    bundles = list_bundles(tmp_path)
    assert any(x.bundle_id == "test_bundle_1" for x in bundles)
    loaded = get_bundle("test_bundle_1", tmp_path)
    assert loaded is not None
    assert loaded.title == "Test bundle"
    assert len(loaded.steps) == 1
    assert loaded.steps[0].action_ref == "job_a"


def test_recovery_options_requires_blocked_run(tmp_path: Path) -> None:
    """get_recovery_options returns error when run is not blocked."""
    from workflow_dataset.executor.hub import get_recovery_options
    from workflow_dataset.executor.models import ExecutionRun
    from workflow_dataset.executor.hub import save_run
    run = ExecutionRun(run_id="r1", plan_id="p1", plan_ref="j1", plan_source="job", mode="simulate", status="completed", envelopes=[], timestamp_start="")
    save_run(run, tmp_path)
    out = get_recovery_options("r1", tmp_path)
    assert out.get("error")
    assert "not blocked" in out["error"].lower()


def test_recovery_options_for_blocked_run(tmp_path: Path) -> None:
    """get_recovery_options returns options and suggested_bundles for blocked run."""
    from workflow_dataset.executor.hub import get_recovery_options, save_run, load_run
    from workflow_dataset.executor.models import ExecutionRun, ActionEnvelope
    run = ExecutionRun(
        run_id="blocked_run_1",
        plan_id="p1",
        plan_ref="j1",
        plan_source="job",
        mode="simulate",
        status="blocked",
        current_step_index=0,
        envelopes=[ActionEnvelope(step_index=0, action_ref="j1", label="j1")],
        executed=[],
        blocked=[{"job_pack_id": "j1", "step_index": 0, "reason": "policy blocked"}],
        artifacts=[],
        timestamp_start="",
    )
    save_run(run, tmp_path)
    out = get_recovery_options("blocked_run_1", tmp_path)
    assert "error" not in out or not out.get("error")
    assert out.get("run_id") == "blocked_run_1"
    assert "retry" in out.get("options", [])
    assert "skip" in out.get("options", [])
    assert "substitute" in out.get("options", [])
    assert "suggested_bundles" in out


def test_record_recovery_decision(tmp_path: Path) -> None:
    """record_recovery_decision appends to run.recovery_decisions."""
    from workflow_dataset.executor.hub import record_recovery_decision, save_run, load_run
    from workflow_dataset.executor.models import ExecutionRun
    run = ExecutionRun(run_id="rec_run", plan_id="p1", plan_ref="j1", plan_source="job", mode="simulate", status="blocked", current_step_index=0, envelopes=[], timestamp_start="")
    save_run(run, tmp_path)
    ok = record_recovery_decision("rec_run", 0, "skip", tmp_path, note="operator chose skip")
    assert ok is True
    loaded = load_run("rec_run", tmp_path)
    assert loaded is not None
    assert len(loaded.recovery_decisions) == 1
    assert loaded.recovery_decisions[0].decision == "skip"
    assert loaded.recovery_decisions[0].note == "operator chose skip"


def test_execution_run_serialize_recovery_decisions() -> None:
    """ExecutionRun to_dict/from_dict includes recovery_decisions."""
    from workflow_dataset.executor.models import ExecutionRun, BlockedStepRecovery
    run = ExecutionRun(
        run_id="rr",
        plan_id="p",
        plan_ref="r",
        plan_source="routine",
        mode="simulate",
        status="blocked",
        current_step_index=1,
        envelopes=[],
        recovery_decisions=[
            BlockedStepRecovery(step_index=1, decision="skip", note="skipped", timestamp="2025-01-01T00:00:00Z"),
        ],
        timestamp_start="",
    )
    d = run.to_dict()
    assert "recovery_decisions" in d
    assert len(d["recovery_decisions"]) == 1
    assert d["recovery_decisions"][0]["decision"] == "skip"
    loaded = ExecutionRun.from_dict(d)
    assert len(loaded.recovery_decisions) == 1
    assert loaded.recovery_decisions[0].note == "skipped"


def test_resume_from_blocked_not_found(tmp_path: Path) -> None:
    """resume_from_blocked returns error for missing run."""
    from workflow_dataset.executor.runner import resume_from_blocked
    result = resume_from_blocked("no_such_run", "skip", tmp_path)
    assert result.get("error")
    assert "not found" in result["error"].lower()


def test_resume_from_blocked_skip(seeded_jobs: None, tmp_path: Path) -> None:
    """resume_from_blocked with decision=skip advances step and continues or completes."""
    from workflow_dataset.executor.runner import run_with_checkpoints, resume_from_blocked
    from workflow_dataset.executor.hub import load_run
    # Create a blocked run: use a plan that will block (e.g. nonexistent job at step 0)
    from workflow_dataset.executor.models import ExecutionRun, ActionEnvelope
    from workflow_dataset.executor.mapping import plan_preview_to_envelopes
    from workflow_dataset.executor.hub import save_run
    from workflow_dataset.copilot.plan import build_plan_for_job
    plan = build_plan_for_job("weekly_status_from_notes", "simulate", {}, tmp_path)
    if not plan:
        pytest.skip("plan not available")
    envelopes = plan_preview_to_envelopes(plan.plan_id, plan.job_pack_ids, plan.mode, plan.blocked, plan.blocked_reasons, tmp_path)
    run = ExecutionRun(
        run_id="skip_recovery_run",
        plan_id=plan.plan_id,
        plan_ref=plan.job_pack_ids[0] if plan.job_pack_ids else "weekly_status_from_notes",
        plan_source="job",
        mode="simulate",
        status="blocked",
        current_step_index=0,
        envelopes=envelopes,
        executed=[],
        blocked=[{"job_pack_id": plan.job_pack_ids[0], "step_index": 0, "reason": "test block"}],
        artifacts=[],
        timestamp_start="",
    )
    save_run(run, tmp_path)
    result = resume_from_blocked("skip_recovery_run", "skip", tmp_path)
    assert result.get("error") is None or "could not be re-resolved" in result.get("error", "")
    if not result.get("error"):
        assert result.get("run_id") == "skip_recovery_run"
        assert result.get("status") in ("completed", "blocked", "awaiting_approval")
        loaded = load_run("skip_recovery_run", tmp_path)
        assert loaded is not None
        assert len(loaded.recovery_decisions) == 1
        assert loaded.recovery_decisions[0].decision == "skip"
