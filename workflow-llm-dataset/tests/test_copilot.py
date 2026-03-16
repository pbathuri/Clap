"""
M23K: Copilot — recommendations, routines, plan preview, run, reminders, report.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.job_packs.seed_jobs import seed_example_job_pack, seed_task_demo_job_pack
from workflow_dataset.desktop_bench.seed_cases import seed_default_cases
from workflow_dataset.copilot.recommendations import recommend_jobs
from workflow_dataset.copilot.routines import Routine, list_routines, get_routine, save_routine, get_ordered_job_ids
from workflow_dataset.copilot.plan import build_plan_for_job, build_plan_for_routine, PlanPreview
from workflow_dataset.copilot.run import run_plan, list_plan_runs
from workflow_dataset.copilot.reminders import list_reminders, add_reminder, reminders_due
from workflow_dataset.copilot.report import copilot_report, format_copilot_report
from workflow_dataset.copilot.seed_copilot import seed_morning_routine


@pytest.fixture
def seeded_jobs(tmp_path):
    seed_default_cases(tmp_path)
    seed_example_job_pack(tmp_path)
    seed_task_demo_job_pack(tmp_path)


def test_recommend_jobs(seeded_jobs, tmp_path):
    recs = recommend_jobs(tmp_path, limit=10)
    assert isinstance(recs, list)
    for r in recs:
        assert "job_pack_id" in r
        assert "reason" in r
        assert "mode_allowed" in r
        assert "blocking_issues" in r


def test_routine_crud(tmp_path):
    r = Routine(
        routine_id="test_routine",
        title="Test",
        job_pack_ids=["j1", "j2"],
        simulate_only=True,
    )
    save_routine(r, tmp_path)
    assert "test_routine" in list_routines(tmp_path)
    loaded = get_routine("test_routine", tmp_path)
    assert loaded is not None
    assert loaded.title == "Test"
    assert get_ordered_job_ids(loaded) == ["j1", "j2"]


def test_build_plan_for_job(seeded_jobs, tmp_path):
    plan = build_plan_for_job("weekly_status_from_notes", "simulate", {}, tmp_path)
    assert plan is not None
    assert plan.plan_id
    assert plan.job_pack_ids == ["weekly_status_from_notes"]
    assert plan.mode == "simulate"


def test_build_plan_for_routine(seeded_jobs, tmp_path):
    seed_morning_routine(tmp_path)
    plan = build_plan_for_routine("morning_reporting", "simulate", tmp_path)
    assert plan is not None
    assert "weekly_status_from_notes" in plan.job_pack_ids


def test_run_plan_simulate(seeded_jobs, tmp_path):
    plan = build_plan_for_job("weekly_status_from_notes", "simulate", {}, tmp_path)
    assert plan is not None
    result = run_plan(plan, tmp_path, stop_on_first_blocked=True)
    assert "plan_run_id" in result
    assert result.get("executed_count") >= 0
    assert "run_path" in result


def test_reminders(tmp_path):
    add_reminder(job_pack_id="weekly_status", due_at="morning", title="Morning job", repo_root=tmp_path)
    rems = list_reminders(tmp_path)
    assert len(rems) >= 1
    due = reminders_due(tmp_path)
    assert len(due) >= 1


def test_copilot_report(seeded_jobs, tmp_path):
    report = copilot_report(tmp_path)
    assert "recommendations_count" in report
    assert "routines_count" in report
    assert "plan_runs_count" in report
    assert "reminders_count" in report
    text = format_copilot_report(report)
    assert "Copilot report" in text
