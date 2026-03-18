"""
M34E–M34H: Failure classification, retry, defer, handoff to human review.
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

from workflow_dataset.background_run.models import BackgroundRun, FailureRetryState
from workflow_dataset.background_run.store import load_run, save_run, append_history_entry


def classify_failure(run: BackgroundRun) -> str:
    """
    Classify failure: blocked | policy_suppressed | transient | degraded.
    """
    if not run.failure_retry.failed:
        return ""
    code = run.failure_retry.failure_code
    if code in ("blocked", "policy_suppressed", "transient", "degraded"):
        return code
    if "approval" in (run.failure_retry.failure_reason or "").lower() or "blocked" in (run.status or "").lower():
        return "blocked"
    if "policy" in (run.failure_retry.failure_reason or "").lower() or "suppress" in (run.failure_retry.failure_reason or "").lower():
        return "policy_suppressed"
    if "degraded" in (run.failure_retry.failure_reason or "").lower():
        return "degraded"
    return "transient"


def retry_run(
    run_id: str,
    repo_root: Path | str | None = None,
    with_backoff: bool = True,
) -> dict[str, Any]:
    """
    Mark run for retry: increment retry_count, set status so runner can pick it again or re-execute.
    If with_backoff is True, uses RetryPolicy for this automation to set defer_until (backoff).
    Returns updated run summary or error.
    """
    root = Path(repo_root).resolve() if repo_root else None
    run = load_run(run_id, root)
    if not run:
        return {"error": f"Run not found: {run_id}"}
    from workflow_dataset.background_run.retry_policies import (
        get_policy_for_automation,
        compute_defer_until,
    )
    policy = get_policy_for_automation(run.automation_id, root)
    if run.failure_retry.retry_count >= policy.max_retries:
        return {"error": f"Max retries ({policy.max_retries}) exceeded", "run_id": run_id}
    run.failure_retry.retry_count += 1
    run.failure_retry.failed = False
    run.failure_retry.failure_reason = ""
    run.failure_retry.failure_code = ""
    run.failure_retry.max_retries = policy.max_retries
    if with_backoff:
        run.failure_retry.defer_until = compute_defer_until(
            run.failure_retry.retry_count - 1,
            policy,
            run.timestamp_end or utc_now_iso(),
        )
    else:
        run.failure_retry.defer_until = ""
    run.status = "queued"
    save_run(run, root)
    append_history_entry({
        "run_id": run_id,
        "action": "retry",
        "retry_count": run.failure_retry.retry_count,
        "defer_until": run.failure_retry.defer_until,
        "timestamp": utc_now_iso(),
    }, root)
    return {
        "run_id": run_id,
        "status": "queued",
        "retry_count": run.failure_retry.retry_count,
        "defer_until": run.failure_retry.defer_until or None,
    }


def defer_run(
    run_id: str,
    defer_until: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Defer run until after defer_until (ISO timestamp)."""
    root = Path(repo_root).resolve() if repo_root else None
    run = load_run(run_id, root)
    if not run:
        return {"error": f"Run not found: {run_id}"}
    run.failure_retry.defer_until = defer_until or utc_now_iso()
    run.status = "deferred"
    save_run(run, root)
    append_history_entry({
        "run_id": run_id,
        "action": "defer",
        "defer_until": run.failure_retry.defer_until,
        "timestamp": utc_now_iso(),
    }, root)
    return {"run_id": run_id, "status": "deferred", "defer_until": run.failure_retry.defer_until}


def handoff_to_review(run_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Mark run as needing human review (e.g. add to intervention inbox)."""
    root = Path(repo_root).resolve() if repo_root else None
    run = load_run(run_id, root)
    if not run:
        return {"error": f"Run not found: {run_id}"}
    run.failure_retry.handoff_to_review = True
    run.status = "needs_review"
    save_run(run, root)
    append_history_entry({
        "run_id": run_id,
        "action": "handoff_to_review",
        "timestamp": utc_now_iso(),
    }, root)
    return {"run_id": run_id, "status": "needs_review", "handoff_to_review": True}


def suppress_run(
    run_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Suppress run (policy or operator choice); do not retry."""
    root = Path(repo_root).resolve() if repo_root else None
    run = load_run(run_id, root)
    if not run:
        return {"error": f"Run not found: {run_id}"}
    run.status = "suppressed"
    run.failure_retry.failure_code = "policy_suppressed"
    save_run(run, root)
    append_history_entry({
        "run_id": run_id,
        "action": "suppress",
        "timestamp": utc_now_iso(),
    }, root)
    return {"run_id": run_id, "status": "suppressed"}
