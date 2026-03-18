"""
M41I–M41L: Tests for ops jobs — model, cadence, run, history, blocked, report.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from workflow_dataset.ops_jobs.models import OpsJob, JobOutput, JobCadence
from workflow_dataset.ops_jobs.registry import get_ops_job, list_ops_job_ids, BUILTIN_OPS_JOBS
from workflow_dataset.ops_jobs.store import get_last_run, list_run_history, append_run, get_ops_jobs_dir
from workflow_dataset.ops_jobs.cadence import next_due_utc, list_due, list_overdue
from workflow_dataset.ops_jobs.runner import run_ops_job
from workflow_dataset.ops_jobs.report import build_ops_maintenance_report


def test_ops_job_model() -> None:
    j = get_ops_job("reliability_refresh")
    assert j is not None
    assert j.job_id == "reliability_refresh"
    assert j.job_class == "maintenance"
    assert j.cadence.interval_days == 1
    assert len(j.prerequisites) >= 1
    assert j.run_command == "reliability_run"
    assert "reliability" in j.output_surfaces
    d = j.to_dict()
    assert d["job_id"] == "reliability_refresh"
    assert "cadence" in d and "escalation_targets" in d


def test_cadence_and_due() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nd = next_due_utc("reliability_refresh", repo_root=root)
        assert nd
        due = list_due(repo_root=root)
        assert isinstance(due, list)
        assert any(d.get("job_id") == "reliability_refresh" for d in due)
        overdue = list_overdue(repo_root=root)
        assert isinstance(overdue, list)


def test_run_ops_job() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        out = run_ops_job("queue_calmness_review", repo_root=root)
        assert out.job_id == "queue_calmness_review"
        assert out.outcome in ("pass", "fail", "blocked")
        assert out.run_id
        assert out.started_utc
        last = get_last_run("queue_calmness_review", repo_root=root)
        assert last.get("job_id") == "queue_calmness_review" or last.get("outcome")


def test_history() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        append_run("issue_cluster_review", {"job_id": "issue_cluster_review", "outcome": "pass", "started_utc": "2025-01-01T00:00:00Z", "summary": "ok"}, repo_root=root)
        history = list_run_history("issue_cluster_review", limit=5, repo_root=root)
        assert len(history) >= 1
        assert history[0].get("outcome") == "pass"


def test_blocked_behavior() -> None:
    j = get_ops_job("reliability_refresh")
    assert j is not None
    assert j.retryable
    assert any(b.reason_id for b in j.blocked_reasons)


def test_report() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        r = build_ops_maintenance_report(repo_root=root)
        assert "next_due_job_id" in r
        assert "due_jobs" in r
        assert "recommended_action" in r
        assert "workflow-dataset ops-jobs" in r.get("recommended_action", "")


def test_unknown_job() -> None:
    j = get_ops_job("nonexistent_ops_job_xyz")
    assert j is None
    ids = list_ops_job_ids()
    assert "reliability_refresh" in ids
    assert len(ids) == len(BUILTIN_OPS_JOBS)
    with tempfile.TemporaryDirectory() as tmp:
        out = run_ops_job("nonexistent", repo_root=Path(tmp))
        assert out.outcome == "blocked"
        assert "not found" in out.summary.lower() or "Unknown" in out.summary


# --- M41L.1 Maintenance calendars + production rhythm packs ---


def test_maintenance_calendar() -> None:
    from workflow_dataset.ops_jobs import get_maintenance_calendar
    cal = get_maintenance_calendar()
    assert isinstance(cal, list)
    assert len(cal) >= 2
    rhythms = [e.rhythm for e in cal]
    assert "daily" in rhythms
    assert "weekly" in rhythms
    assert any("queue_calmness_review" in e.job_ids for e in cal if e.rhythm == "twice_daily")
    assert any("supportability_refresh" in e.job_ids or "adaptation_audit" in e.job_ids for e in cal if e.rhythm == "weekly")


def test_rhythm_packs() -> None:
    from workflow_dataset.ops_jobs import get_rhythm_pack, list_rhythm_pack_ids
    ids = list_rhythm_pack_ids()
    assert "weekly_production" in ids
    assert "monthly_production" in ids
    p = get_rhythm_pack("weekly_production")
    assert p is not None
    assert p.rhythm == "weekly"
    assert "supportability_refresh" in p.job_ids
    assert len(p.review_checklist) >= 1
    assert get_rhythm_pack("nonexistent") is None


def test_operator_maintenance_summary() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        from workflow_dataset.ops_jobs import build_operator_maintenance_summary
        s = build_operator_maintenance_summary(repo_root=root)
        assert "summary_text" in s
        assert "weekly" in s and "monthly" in s
        assert "job_ids" in s["weekly"] and "review_checklist" in s["weekly"]
        assert "calendar_rhythms" in s
        assert "workflow-dataset ops-jobs" in s.get("recommended_action", "") or "recommended_action" in s
