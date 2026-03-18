"""
M34H.1: Operator-facing failure and fallback explanations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.background_run.models import BackgroundRun
from workflow_dataset.background_run.recovery import classify_failure
from workflow_dataset.background_run.degraded_fallback import get_fallback_for_failure


def build_failure_explanation(run: BackgroundRun) -> dict[str, Any]:
    """
    Build a clear operator-facing explanation of why this run failed or is blocked.
    """
    failure_code = classify_failure(run)
    lines: list[str] = []
    if run.failure_retry.failed and run.failure_retry.failure_reason:
        lines.append(f"Failure: {run.failure_retry.failure_reason}")
    if failure_code:
        lines.append(f"Classification: {failure_code}")
    if failure_code == "blocked":
        lines.append("This run is blocked (e.g. approval or policy). Resolve the blocker before retrying.")
    elif failure_code == "policy_suppressed":
        lines.append("This run was suppressed by policy or operator. Re-add to queue or change policy to run again.")
    elif failure_code == "transient":
        lines.append("This looks like a transient failure. Retry with backoff is recommended.")
    elif failure_code == "degraded":
        lines.append("System is in degraded mode. Run in simulate-only or fix degraded subsystem.")
    if run.failure_retry.retry_count > 0:
        lines.append(f"Retry count: {run.failure_retry.retry_count} (max: {run.failure_retry.max_retries})")
    if run.failure_retry.defer_until:
        lines.append(f"Next run not before: {run.failure_retry.defer_until}")
    return {
        "run_id": run.run_id,
        "automation_id": run.automation_id,
        "status": run.status,
        "failure_code": failure_code,
        "explanation_lines": lines,
        "summary": " ".join(lines) if lines else "No failure details available.",
    }


def build_fallback_explanation(
    run: BackgroundRun,
    fallback_profile: Any | None = None,
) -> dict[str, Any]:
    """
    Build operator-facing explanation of what fallback applies and what to do next.
    """
    failure_code = classify_failure(run)
    profile = fallback_profile or get_fallback_for_failure(failure_code, run)
    out: dict[str, Any] = {
        "run_id": run.run_id,
        "automation_id": run.automation_id,
        "failure_code": failure_code,
        "fallback_profile_id": "",
        "fallback_mode": "",
        "operator_explanation": "",
        "still_works": [],
        "disabled_flows": [],
        "recommended_action": "",
    }
    if profile:
        out["fallback_profile_id"] = profile.profile_id
        out["fallback_mode"] = profile.fallback_mode
        out["operator_explanation"] = profile.operator_explanation
        out["still_works"] = list(profile.still_works)
        out["disabled_flows"] = list(profile.disabled_flows)
        if profile.fallback_mode == "retry_with_backoff":
            out["recommended_action"] = f"Run 'workflow-dataset background retry {run.run_id}' after defer_until, or run now without backoff (retry with --no-backoff if supported)."
        elif profile.fallback_mode == "handoff":
            out["recommended_action"] = "Resolve approval or policy, then retry. Or run 'workflow-dataset background handoff-to-review' to add to intervention inbox."
        elif profile.fallback_mode == "skip":
            out["recommended_action"] = "No automatic retry. Re-add to queue with 'workflow-dataset background queue --add <id> --plan-ref <ref>' if this workflow should run."
        elif profile.fallback_mode == "degraded_simulate":
            out["recommended_action"] = "Run in simulate-only, or run 'workflow-dataset reliability report' to fix degraded subsystem."
    return out
