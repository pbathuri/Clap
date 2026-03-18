"""
M34E–M34H: Tests for bounded background runner — models, queue, gating, run, recovery, summary.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.background_run.models import (
    BackgroundRun,
    QueuedRecurringJob,
    RunSourceTrigger,
    ExecutionMode,
    ApprovalState,
    FailureRetryState,
    BackgroundArtifact,
    RunSummary,
    RetryPolicy,
    BackoffStrategy,
)
from workflow_dataset.background_run.store import (
    load_queue,
    save_queue,
    save_run,
    load_run,
    load_history,
    append_history_entry,
    load_retry_policies,
    save_retry_policies,
)
from workflow_dataset.background_run.gating import evaluate_background_policy
from workflow_dataset.background_run.recovery import classify_failure, retry_run, suppress_run
from workflow_dataset.background_run.runner import build_run_summary
from workflow_dataset.background_run.retry_policies import (
    get_policy_for_automation,
    compute_defer_until,
    DEFAULT_RETRY_POLICY,
)
from workflow_dataset.background_run.degraded_fallback import (
    build_degraded_fallback_report,
    get_fallback_for_failure,
    ASYNC_DEGRADED_FALLBACK_PROFILES,
)
from workflow_dataset.background_run.explain import build_failure_explanation, build_fallback_explanation


def test_queued_recurring_job_roundtrip():
    job = QueuedRecurringJob(
        automation_id="auto_weekly",
        plan_source="job",
        plan_ref="weekly_report",
        trigger_type="schedule",
        allowed_modes=["simulate"],
        require_approval_before_real=True,
        label="Weekly report",
    )
    d = job.to_dict()
    job2 = QueuedRecurringJob.from_dict(d)
    assert job2.automation_id == job.automation_id
    assert job2.plan_ref == job.plan_ref


def test_background_run_roundtrip(tmp_path):
    run = BackgroundRun(
        run_id="bg_abc123",
        automation_id="auto_1",
        source_trigger=RunSourceTrigger.RECURRING_MATCH.value,
        plan_source="job",
        plan_ref="job_1",
        execution_mode=ExecutionMode.SIMULATE.value,
        approval_state=ApprovalState.APPROVED.value,
        status="completed",
        timestamp_start="2025-03-16T12:00:00Z",
        timestamp_end="2025-03-16T12:01:00Z",
        failure_retry=FailureRetryState(failed=False),
        artifacts=[BackgroundArtifact(path="/out/report.txt", kind="file", run_id="bg_abc123", step_index=0)],
    )
    save_run(run, tmp_path)
    loaded = load_run(run.run_id, tmp_path)
    assert loaded is not None
    assert loaded.run_id == run.run_id
    assert loaded.status == "completed"
    assert len(loaded.artifacts) == 1
    assert loaded.artifacts[0].path == "/out/report.txt"


def test_queue_save_load(tmp_path):
    jobs = [
        QueuedRecurringJob(automation_id="a1", plan_source="job", plan_ref="j1", allowed_modes=["simulate"]),
    ]
    save_queue(jobs, tmp_path)
    out = load_queue(tmp_path)
    assert len(out) == 1
    assert out[0].automation_id == "a1"


def test_gating_simulate_only_when_real_not_allowed():
    job = QueuedRecurringJob(
        automation_id="auto_1",
        plan_ref="j1",
        plan_source="job",
        allowed_modes=["simulate"],
        require_approval_before_real=True,
    )
    result = evaluate_background_policy(job, work_state=None, repo_root=None)
    assert result.allowed is True
    assert result.simulate_only is True


def test_gating_blocked_when_approval_blocked():
    class MockWorkState:
        approval_blocked_jobs = ["j1"]
        simulate_only_jobs = []

    job = QueuedRecurringJob(automation_id="auto_1", plan_ref="j1", plan_source="job", allowed_modes=["simulate"])
    result = evaluate_background_policy(job, work_state=MockWorkState(), repo_root=None)
    assert result.allowed is False
    assert "approval_blocked" in " ".join(result.notes).lower() or "blocked" in " ".join(result.notes).lower()


def test_classify_failure():
    run = BackgroundRun(
        run_id="bg_1",
        status="blocked",
        failure_retry=FailureRetryState(failed=True, failure_code="blocked", failure_reason="approval missing"),
    )
    assert classify_failure(run) == "blocked"
    run.failure_retry.failure_code = "transient"
    assert classify_failure(run) == "transient"


def test_retry_run(tmp_path):
    run = BackgroundRun(
        run_id="bg_retry_1",
        automation_id="auto_1",
        status="failed",
        failure_retry=FailureRetryState(failed=True, retry_count=0, max_retries=3),
    )
    save_run(run, tmp_path)
    result = retry_run("bg_retry_1", repo_root=tmp_path)
    assert "error" not in result
    assert result.get("retry_count") == 1
    loaded = load_run("bg_retry_1", tmp_path)
    assert loaded.status == "queued"


def test_suppress_run(tmp_path):
    run = BackgroundRun(run_id="bg_sup_1", automation_id="auto_1", status="failed")
    save_run(run, tmp_path)
    result = suppress_run("bg_sup_1", repo_root=tmp_path)
    assert result.get("status") == "suppressed"
    loaded = load_run("bg_sup_1", tmp_path)
    assert loaded.status == "suppressed"


def test_build_run_summary(tmp_path):
    append_history_entry({"run_id": "h1", "status": "completed", "timestamp": "2025-03-16T12:00:00Z"}, tmp_path)
    summary = build_run_summary(repo_root=tmp_path)
    assert isinstance(summary.active_run_ids, list)
    assert isinstance(summary.blocked_run_ids, list)
    assert isinstance(summary.queue_length, int)
    assert summary.queue_length >= 0
    assert len(summary.recent_outcomes) >= 1


# ----- M34H.1 Retry policies + degraded fallbacks -----


def test_retry_policy_roundtrip():
    policy = RetryPolicy(
        policy_id="custom",
        max_retries=5,
        backoff_strategy=BackoffStrategy.EXPONENTIAL.value,
        backoff_base_seconds=120,
        suppress_after_failures=3,
        handoff_after_failures=2,
        label="Custom",
    )
    d = policy.to_dict()
    p2 = RetryPolicy.from_dict(d)
    assert p2.max_retries == 5
    assert p2.backoff_strategy == BackoffStrategy.EXPONENTIAL.value
    assert p2.suppress_after_failures == 3


def test_compute_defer_until():
    policy = RetryPolicy(backoff_base_seconds=60, backoff_strategy=BackoffStrategy.FIXED.value)
    t = compute_defer_until(0, policy, "2025-03-16T12:00:00Z")
    assert "2025" in t and "12" in t
    policy_exp = RetryPolicy(backoff_base_seconds=60, backoff_strategy=BackoffStrategy.EXPONENTIAL.value)
    t1 = compute_defer_until(1, policy_exp, "2025-03-16T12:00:00Z")
    t2 = compute_defer_until(2, policy_exp, "2025-03-16T12:00:00Z")
    assert t1 != t2


def test_get_policy_for_automation_default(tmp_path):
    policy = get_policy_for_automation("", tmp_path)
    assert policy.max_retries >= 1
    assert policy.backoff_strategy in ("fixed", "linear", "exponential")


def test_retry_run_with_backoff(tmp_path):
    run = BackgroundRun(
        run_id="bg_backoff_1",
        automation_id="auto_1",
        status="failed",
        timestamp_end="2025-03-16T12:00:00Z",
        failure_retry=FailureRetryState(failed=True, retry_count=0, max_retries=3),
    )
    save_run(run, tmp_path)
    result = retry_run("bg_backoff_1", repo_root=tmp_path, with_backoff=True)
    assert "error" not in result
    assert result.get("retry_count") == 1
    loaded = load_run("bg_backoff_1", tmp_path)
    assert loaded.status == "queued"
    # with_backoff=True uses policy; defer_until may be set
    assert "defer_until" in result or hasattr(loaded.failure_retry, "defer_until")


def test_build_degraded_fallback_report(tmp_path):
    report = build_degraded_fallback_report(limit=5, repo_root=tmp_path)
    assert report.get("report_type") == "degraded_fallback"
    assert "entries" in report
    assert "profiles_available" in report
    assert len(report["profiles_available"]) >= 1


def test_get_fallback_for_failure():
    profile = get_fallback_for_failure("transient")
    assert profile is not None
    assert profile.when_to_use == "transient"
    assert profile.operator_explanation


def test_build_failure_explanation():
    run = BackgroundRun(
        run_id="bg_ex",
        automation_id="auto_1",
        status="failed",
        failure_retry=FailureRetryState(failed=True, failure_code="blocked", failure_reason="approval missing"),
    )
    expl = build_failure_explanation(run)
    assert "failure_code" in expl
    assert expl["failure_code"] == "blocked"
    assert expl["summary"]


def test_build_fallback_explanation():
    run = BackgroundRun(
        run_id="bg_fb",
        status="blocked",
        failure_retry=FailureRetryState(failed=True, failure_code="blocked"),
    )
    expl = build_fallback_explanation(run)
    assert expl.get("fallback_profile_id") or expl.get("operator_explanation")
    assert "recommended_action" in expl
