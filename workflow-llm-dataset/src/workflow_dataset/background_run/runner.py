"""
M34E–M34H: Bounded background runner — pick eligible job, run simulate-first, optional approved real, persist.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:20]

from workflow_dataset.background_run.models import (
    BackgroundRun,
    BackgroundArtifact,
    FailureRetryState,
    QueuedRecurringJob,
    RunSourceTrigger,
    ExecutionMode,
    ApprovalState,
)
from workflow_dataset.background_run.store import (
    load_queue,
    save_run,
    load_run as load_bg_run,
    list_runs as list_bg_runs,
    load_history,
    append_history_entry,
)
from workflow_dataset.background_run.gating import evaluate_background_policy, GatingResult
from workflow_dataset.background_run.models import RunSummary


def pick_eligible_job(
    work_state: Any | None = None,
    repo_root: Path | str | None = None,
) -> tuple[QueuedRecurringJob | None, GatingResult | None]:
    """
    Pick the first queued recurring job that is allowed to run (policy + trust).
    Returns (job, gating_result) or (None, None) if none eligible.
    """
    root = Path(repo_root).resolve() if repo_root else None
    jobs = load_queue(root)
    for job in jobs:
        gating = evaluate_background_policy(job, work_state=work_state, repo_root=root)
        if gating.allowed:
            return job, gating
    return None, None


def run_one_background(
    job: QueuedRecurringJob | None = None,
    run_id: str | None = None,
    work_state: Any | None = None,
    simulate_first: bool = True,
    allow_real_after_simulate: bool = False,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Run one background workflow. If job is None, picks first eligible from queue.
    simulate_first: run in simulate mode first.
    allow_real_after_simulate: if True and policy allows, run real after simulate (still respects approval_required).
    Persists BackgroundRun, artifacts, and history entry.
    """
    root = Path(repo_root).resolve() if repo_root else None

    if job is None:
        job, gating = pick_eligible_job(work_state=work_state, repo_root=root)
        if job is None:
            return {
                "error": "No eligible queued recurring job",
                "run_id": "",
                "status": "skipped",
            }
    else:
        gating = evaluate_background_policy(job, work_state=work_state, repo_root=root)
        if not gating.allowed:
            return {
                "error": "Workflow not allowed for background run",
                "notes": gating.notes,
                "run_id": "",
                "status": "blocked",
            }

    mode = "simulate" if gating.simulate_only or not allow_real_after_simulate else "simulate"
    # We always run simulate first; real only in a second phase if allow_real_after_simulate and approved
    bid = run_id or stable_id("bg", job.automation_id, job.plan_ref, utc_now_iso(), prefix="bg_")[:24]
    approval_state = ApprovalState.APPROVED.value if not gating.approval_required else ApprovalState.PENDING.value
    exec_mode = ExecutionMode.SIMULATE.value
    if gating.degraded_fallback:
        exec_mode = ExecutionMode.DEGRADED_SIMULATE.value

    run = BackgroundRun(
        run_id=bid,
        automation_id=job.automation_id,
        source_trigger=RunSourceTrigger.RECURRING_MATCH.value,
        plan_source=job.plan_source,
        plan_ref=job.plan_ref,
        execution_mode=exec_mode,
        approval_state=approval_state,
        status="running",
        executor_run_id="",
        timestamp_start=utc_now_iso(),
        timestamp_end="",
        artifacts=[],
        failure_retry=FailureRetryState(),
        policy_notes=gating.notes,
        run_path="",
        outcome_summary="",
    )
    save_run(run, root)

    # Execute via executor (same path as supervised_loop handoff)
    try:
        from workflow_dataset.executor.runner import run_with_checkpoints
    except Exception as e:
        run.status = "failed"
        run.timestamp_end = utc_now_iso()
        run.failure_retry.failed = True
        run.failure_retry.failure_reason = str(e)
        run.failure_retry.failure_code = "blocked"
        save_run(run, root)
        append_history_entry({
            "run_id": bid,
            "automation_id": job.automation_id,
            "status": "failed",
            "error": str(e),
            "timestamp": run.timestamp_end,
        }, root)
        return {
            "run_id": bid,
            "status": "failed",
            "error": str(e),
            "outcome_summary": run.outcome_summary,
        }

    result = run_with_checkpoints(
        plan_source=job.plan_source,
        plan_ref=job.plan_ref,
        mode=mode,
        repo_root=root,
        stop_at_checkpoints=True,
        stop_on_first_blocked=True,
    )

    executor_run_id = result.get("run_id", "")
    run.executor_run_id = executor_run_id
    run.status = result.get("status", "completed")
    run.timestamp_end = utc_now_iso()
    run.outcome_summary = result.get("message", "") or f"executed={result.get('executed_count', 0)} blocked={result.get('blocked_count', 0)}"

    if executor_run_id:
        try:
            from workflow_dataset.executor.hub import load_run as load_exec_run
            exec_run = load_exec_run(executor_run_id, root)
            if exec_run and getattr(exec_run, "artifacts", None):
                for p in exec_run.artifacts:
                    run.artifacts.append(BackgroundArtifact(path=p, kind="file", run_id=bid, step_index=0))
        except Exception:
            pass

    if run.status == "blocked":
        run.failure_retry.failed = True
        run.failure_retry.failure_code = "blocked"
        run.failure_retry.failure_reason = result.get("message", "blocked")
    elif result.get("error"):
        run.failure_retry.failed = True
        run.failure_retry.failure_reason = result.get("error", "")
        run.failure_retry.failure_code = "transient"
        run.status = "failed"

    save_run(run, root)
    append_history_entry({
        "run_id": bid,
        "automation_id": job.automation_id,
        "plan_ref": job.plan_ref,
        "status": run.status,
        "executor_run_id": executor_run_id,
        "outcome_summary": run.outcome_summary,
        "timestamp": run.timestamp_end,
    }, root)

    return {
        "run_id": bid,
        "status": run.status,
        "executor_run_id": executor_run_id,
        "outcome_summary": run.outcome_summary,
        "error": result.get("error"),
    }


def build_run_summary(
    repo_root: Path | str | None = None,
    recent_limit: int = 10,
) -> RunSummary:
    """Build RunSummary for CLI and mission control: active, blocked, retryable, next, recent outcomes, needs_review, queue_length."""
    root = Path(repo_root).resolve() if repo_root else None
    runs = list_bg_runs(limit=100, status_filter=None, repo_root=root)
    active = [r["run_id"] for r in runs if r.get("status") == "running"]
    blocked = [r["run_id"] for r in runs if r.get("status") == "blocked"]
    retryable = []
    for r in runs:
        if r.get("status") not in ("failed", "deferred"):
            continue
        br = load_bg_run(r["run_id"], root)
        if br and br.failure_retry.retry_count < br.failure_retry.max_retries:
            retryable.append(r["run_id"])
        if len(retryable) >= 20:
            break
    needs_review_ids = list({r.get("automation_id", r["run_id"]) for r in runs if r.get("status") == "needs_review"})[:20]
    recent_outcomes = load_history(limit=recent_limit, repo_root=root)
    queue = load_queue(root)
    next_automation_id = ""
    next_plan_ref = ""
    if queue:
        next_automation_id = queue[0].automation_id
        next_plan_ref = queue[0].plan_ref
    return RunSummary(
        active_run_ids=active,
        blocked_run_ids=blocked,
        retryable_run_ids=retryable[:20],
        next_automation_id=next_automation_id,
        next_plan_ref=next_plan_ref,
        recent_outcomes=recent_outcomes,
        needs_review_automation_ids=needs_review_ids,
        queue_length=len(queue),
    )
