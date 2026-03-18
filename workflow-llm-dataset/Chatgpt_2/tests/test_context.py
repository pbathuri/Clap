"""
M23L: Work state engine, context snapshot, triggers, drift, recommendation explain.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.context.work_state import (
    build_work_state,
    WorkState,
    work_state_to_dict,
    work_state_summary_md,
)
from workflow_dataset.context.config import get_context_root, get_snapshots_dir
from workflow_dataset.context.snapshot import save_snapshot, load_snapshot, list_snapshots
from workflow_dataset.context.triggers import (
    evaluate_trigger_for_job,
    evaluate_trigger_for_routine,
    TriggerResult,
)
from workflow_dataset.context.drift import compare_snapshots, load_latest_and_previous
from workflow_dataset.context.recommendation_explain import (
    explain_recommendation_by_job,
)
from workflow_dataset.job_packs.seed_jobs import seed_example_job_pack
from workflow_dataset.desktop_bench.seed_cases import seed_default_cases
from workflow_dataset.copilot.routines import save_routine, Routine


@pytest.fixture
def tmp_repo(tmp_path):
    """Minimal repo with job packs and optional routine."""
    seed_default_cases(tmp_path)
    seed_example_job_pack(tmp_path)
    save_routine(
        Routine(routine_id="ctx_test_routine", title="Ctx test", job_pack_ids=["weekly_status_from_notes"], simulate_only=True),
        tmp_path,
    )
    return tmp_path


def test_build_work_state(tmp_path):
    state = build_work_state(tmp_path)
    assert isinstance(state, WorkState)
    assert hasattr(state, "recent_successful_jobs")
    assert hasattr(state, "trusted_for_real_jobs")
    assert hasattr(state, "reminders_count")
    assert hasattr(state, "routines_count")


def test_build_work_state_with_jobs(tmp_repo):
    state = build_work_state(tmp_repo)
    assert isinstance(state, WorkState)
    # May have jobs from seed
    assert state.routine_ids == ["ctx_test_routine"] or "ctx_test_routine" in state.routine_ids


def test_work_state_to_dict(tmp_path):
    state = build_work_state(tmp_path)
    d = work_state_to_dict(state)
    assert "created_at" in d
    assert "recent_successful_jobs" in d
    assert "reminders_count" in d


def test_work_state_summary_md(tmp_path):
    state = build_work_state(tmp_path)
    md = work_state_summary_md(state)
    assert "Work state summary" in md
    assert "Jobs" in md
    assert "Copilot" in md


def test_save_and_load_snapshot(tmp_path):
    state = build_work_state(tmp_path)
    state.snapshot_id = "test123"
    path = save_snapshot(state, tmp_path, snapshot_id="test123")
    assert path.exists()
    loaded = load_snapshot("test123", tmp_path)
    assert loaded is not None
    assert loaded.snapshot_id == "test123"
    latest = load_snapshot("latest", tmp_path)
    assert latest is not None


def test_list_snapshots(tmp_path):
    state = build_work_state(tmp_path)
    save_snapshot(state, tmp_path)
    snaps = list_snapshots(limit=5, repo_root=tmp_path)
    assert isinstance(snaps, list)


def test_evaluate_trigger_for_job(tmp_repo):
    state = build_work_state(tmp_repo)
    results = evaluate_trigger_for_job("weekly_status_from_notes", state, tmp_repo)
    assert isinstance(results, list)
    for r in results:
        assert isinstance(r, TriggerResult)
        assert r.job_or_routine_id == "weekly_status_from_notes"
        assert r.trigger_type
        assert r.reason


def test_evaluate_trigger_for_routine(tmp_repo):
    state = build_work_state(tmp_repo)
    results = evaluate_trigger_for_routine("ctx_test_routine", state, tmp_repo)
    assert isinstance(results, list)
    for r in results:
        assert r.kind == "routine"
        assert r.job_or_routine_id == "ctx_test_routine"


def test_recommend_jobs_with_context(tmp_repo):
    from workflow_dataset.copilot.recommendations import recommend_jobs
    state = build_work_state(tmp_repo)
    recs = recommend_jobs(tmp_repo, limit=10, context_snapshot=state)
    assert isinstance(recs, list)
    for r in recs:
        assert "job_pack_id" in r
        # With context we may get why_now_evidence
        assert "reason" in r


def test_explain_recommendation_by_job(tmp_repo):
    out = explain_recommendation_by_job("weekly_status_from_notes", tmp_repo, context_snapshot="")
    assert "job_pack_id" in out
    assert out["job_pack_id"] == "weekly_status_from_notes"
    assert "trigger_results" in out
    assert "explanation_md" in out


def test_compare_snapshots(tmp_path):
    a = build_work_state(tmp_path)
    a.recent_successful_jobs = [{"job_pack_id": "j1", "run_id": "r1", "timestamp": "t1"}]
    a.trusted_for_real_jobs = ["j2"]
    a.approval_blocked_jobs = []
    b = build_work_state(tmp_path)
    b.recent_successful_jobs = [{"job_pack_id": "j1"}, {"job_pack_id": "j3"}]
    b.trusted_for_real_jobs = ["j2", "j3"]
    b.approval_blocked_jobs = []
    drift = compare_snapshots(a, b)
    assert hasattr(drift, "newly_recommendable_jobs")
    assert hasattr(drift, "summary")
    assert isinstance(drift.summary, list)


def test_load_latest_and_previous(tmp_path):
    state = build_work_state(tmp_path)
    save_snapshot(state, tmp_path)
    latest, prev = load_latest_and_previous(tmp_path)
    assert latest is not None
    # previous may be None if first run
    assert prev is None or isinstance(prev, WorkState)


def test_mission_control_includes_work_context(tmp_repo):
    from workflow_dataset.mission_control.state import get_mission_control_state
    state = get_mission_control_state(tmp_repo)
    assert "work_context" in state
    wc = state["work_context"]
    if not wc.get("error"):
        assert "context_recommendations_count" in wc or "next_recommended_action" in wc
