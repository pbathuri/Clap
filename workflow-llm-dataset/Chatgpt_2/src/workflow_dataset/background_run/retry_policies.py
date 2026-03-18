"""
M34H.1: Retry policies, backoff, and suppression strategies.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from workflow_dataset.background_run.models import BackoffStrategy, RetryPolicy
from workflow_dataset.background_run.store import load_retry_policies, save_retry_policies
from workflow_dataset.background_run.models import BackgroundRun


DEFAULT_RETRY_POLICY = RetryPolicy(
    policy_id="default",
    max_retries=3,
    backoff_strategy=BackoffStrategy.EXPONENTIAL.value,
    backoff_base_seconds=60,
    suppress_after_failures=0,
    handoff_after_failures=0,
    label="Default retry with exponential backoff",
)


def get_policy_for_automation(
    automation_id: str = "",
    repo_root: Path | str | None = None,
) -> RetryPolicy:
    """Return effective retry policy for an automation (per-automation override or default)."""
    policies = load_retry_policies(repo_root)
    if automation_id and automation_id in policies.get("by_automation", {}):
        return policies["by_automation"][automation_id]
    default = policies.get("default")
    return default if default else DEFAULT_RETRY_POLICY


def compute_defer_until(
    retry_count: int,
    policy: RetryPolicy,
    now_iso: str | None = None,
) -> str:
    """
    Compute next run time (ISO) from retry count and policy backoff.
    Backoff: fixed = base each time; linear = base * (1 + retry_count); exponential = base * 2^retry_count.
    """
    if now_iso is None:
        try:
            from workflow_dataset.utils.dates import utc_now_iso
            now_iso = utc_now_iso()
        except Exception:
            now_iso = datetime.now(timezone.utc).isoformat()
    try:
        dt = datetime.fromisoformat(now_iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except Exception:
        dt = datetime.now(timezone.utc)
    base = max(1, policy.backoff_base_seconds)
    if policy.backoff_strategy == BackoffStrategy.FIXED.value:
        seconds = base
    elif policy.backoff_strategy == BackoffStrategy.LINEAR.value:
        seconds = base * (1 + retry_count)
    else:
        seconds = base * (2 ** retry_count)
    next_dt = dt + timedelta(seconds=min(seconds, 86400))  # cap 24h
    return next_dt.isoformat()


def should_suppress_after_failure(run: BackgroundRun, policy: RetryPolicy) -> bool:
    """True if policy says to auto-suppress after this many failures."""
    if policy.suppress_after_failures <= 0:
        return False
    return run.failure_retry.retry_count >= policy.suppress_after_failures


def should_handoff_after_failure(run: BackgroundRun, policy: RetryPolicy) -> bool:
    """True if policy says to auto-handoff to human review after this many failures."""
    if policy.handoff_after_failures <= 0:
        return False
    return run.failure_retry.retry_count >= policy.handoff_after_failures
