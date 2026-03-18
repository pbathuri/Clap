"""
M34H.1: Async degraded fallback profiles and report for background runs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.background_run.models import AsyncDegradedFallbackProfile, BackgroundRun
from workflow_dataset.background_run.store import list_runs, load_run
from workflow_dataset.background_run.recovery import classify_failure


# Built-in async degraded fallback profiles (when to use degraded/skip/handoff and what operator should know)
ASYNC_DEGRADED_FALLBACK_PROFILES: list[AsyncDegradedFallbackProfile] = [
    AsyncDegradedFallbackProfile(
        profile_id="transient_failure",
        name="Transient failure",
        when_to_use="transient",
        fallback_mode="retry_with_backoff",
        operator_explanation="Run failed with a transient error (e.g. network or temporary resource). Retry with backoff is recommended. Check defer_until and run 'background retry <run_id>' if needed.",
        still_works=["retry", "background status", "background history"],
        disabled_flows=[],
    ),
    AsyncDegradedFallbackProfile(
        profile_id="blocked_approval",
        name="Blocked (approval / policy)",
        when_to_use="blocked",
        fallback_mode="handoff",
        operator_explanation="Run is blocked by approval or policy. Resolve approval registry or policy overrides, then retry or run in simulate-only mode.",
        still_works=["simulate only", "background queue", "background status"],
        disabled_flows=["real execution until approval present"],
    ),
    AsyncDegradedFallbackProfile(
        profile_id="policy_suppressed",
        name="Policy suppressed",
        when_to_use="policy_suppressed",
        fallback_mode="skip",
        operator_explanation="Run was suppressed by policy or operator. No automatic retry. Use 'background queue' to re-add or change policy if this workflow should run.",
        still_works=["background queue", "background status"],
        disabled_flows=[],
    ),
    AsyncDegradedFallbackProfile(
        profile_id="degraded_simulate",
        name="Degraded (simulate only)",
        when_to_use="degraded",
        fallback_mode="degraded_simulate",
        operator_explanation="System is in degraded mode. Background runs use simulate-only. Fix degraded subsystem (see reliability report) to restore full execution.",
        still_works=["simulate", "background run (simulate)", "reliability report"],
        disabled_flows=["real execution in background"],
    ),
]


def get_fallback_for_failure(
    failure_code: str,
    run: BackgroundRun | None = None,
) -> AsyncDegradedFallbackProfile | None:
    """Return the async degraded fallback profile that applies to this failure code."""
    for p in ASYNC_DEGRADED_FALLBACK_PROFILES:
        if p.when_to_use == failure_code:
            return p
    if failure_code:
        return ASYNC_DEGRADED_FALLBACK_PROFILES[0]  # transient as generic
    return None


def build_degraded_fallback_report(
    limit: int = 20,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Build operator-facing report: runs that failed or are deferred, with failure classification,
    applicable fallback profile, and clear explanation.
    """
    root = Path(repo_root).resolve() if repo_root else None
    runs = list_runs(limit=limit * 2, status_filter=None, repo_root=root)
    failed_or_deferred = [r for r in runs if r.get("status") in ("failed", "blocked", "deferred", "needs_review")]
    entries: list[dict[str, Any]] = []
    for r in failed_or_deferred[:limit]:
        run_id = r.get("run_id", "")
        run = load_run(run_id, root)
        failure_code = classify_failure(run) if run else ""
        profile = get_fallback_for_failure(failure_code, run) if run else None
        entry: dict[str, Any] = {
            "run_id": run_id,
            "automation_id": r.get("automation_id", ""),
            "plan_ref": r.get("plan_ref", ""),
            "status": r.get("status", ""),
            "failure_code": failure_code,
            "outcome_summary": r.get("outcome_summary", ""),
            "timestamp_end": r.get("timestamp_end", ""),
        }
        if profile:
            entry["fallback_profile_id"] = profile.profile_id
            entry["fallback_profile_name"] = profile.name
            entry["fallback_mode"] = profile.fallback_mode
            entry["operator_explanation"] = profile.operator_explanation
            entry["still_works"] = profile.still_works
            entry["disabled_flows"] = profile.disabled_flows
        if run and run.failure_retry.defer_until:
            entry["defer_until"] = run.failure_retry.defer_until
        if run and run.failure_retry.retry_count is not None:
            entry["retry_count"] = run.failure_retry.retry_count
            entry["max_retries"] = run.failure_retry.max_retries
        entries.append(entry)
    return {
        "report_type": "degraded_fallback",
        "entries": entries,
        "profiles_available": [p.profile_id for p in ASYNC_DEGRADED_FALLBACK_PROFILES],
    }
