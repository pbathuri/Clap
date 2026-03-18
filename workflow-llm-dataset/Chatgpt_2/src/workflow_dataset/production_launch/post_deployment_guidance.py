"""
M40L.1: Post-deployment guidance — continue / narrow / rollback / repair from current state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.production_launch.models import PostDeploymentGuidance


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_post_deployment_guidance(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Recommend ongoing action after deployment: continue, narrow, rollback, or repair.
    Evidence-based from release readiness, triage/cohort health, reliability, supportability.
    """
    root = _repo_root(repo_root)
    out: dict[str, Any] = {
        "guidance": PostDeploymentGuidance.CONTINUE.value,
        "reason": "",
        "recommended_actions": [],
        "evidence": {},
    }

    # Release readiness
    try:
        from workflow_dataset.release_readiness.readiness import build_release_readiness
        rr = build_release_readiness(root)
        out["evidence"]["release_readiness_status"] = rr.status
        out["evidence"]["blocker_count"] = len(rr.blockers)
        out["evidence"]["guidance"] = rr.supportability.guidance or ""
        if rr.status == "blocked" or rr.supportability.guidance == "needs_rollback":
            out["guidance"] = PostDeploymentGuidance.ROLLBACK.value
            out["reason"] = "Release readiness blocked or guidance=needs_rollback."
            out["recommended_actions"] = [
                "workflow-dataset release readiness",
                "Resolve blockers then re-evaluate.",
                "Consider rollback if user impact is high.",
            ]
            return out
        if rr.status == "degraded" or rr.supportability.guidance == "needs_operator":
            out["evidence"]["degraded"] = True
    except Exception as e:
        out["evidence"]["readiness_error"] = str(e)

    # Triage / cohort health
    try:
        from workflow_dataset.triage.health import build_cohort_health_summary
        health = build_cohort_health_summary(root)
        out["evidence"]["open_issue_count"] = health.get("open_issue_count", 0)
        out["evidence"]["highest_severity"] = health.get("highest_severity", "")
        out["evidence"]["recommended_downgrade"] = health.get("recommended_downgrade", False)
        if health.get("recommended_downgrade"):
            out["guidance"] = PostDeploymentGuidance.ROLLBACK.value
            out["reason"] = "Cohort health recommends downgrade."
            out["recommended_actions"] = [
                "workflow-dataset release triage",
                "workflow-dataset cohort explain",
                "Address critical/high issues or narrow cohort before continuing.",
            ]
            return out
        if health.get("highest_severity") == "critical":
            out["guidance"] = PostDeploymentGuidance.REPAIR.value
            out["reason"] = "Critical triage issue(s) open; repair before expanding."
            out["recommended_actions"] = [
                "workflow-dataset release triage",
                "Triage and mitigate critical issues.",
                "Re-run production-runbook ongoing-summary after mitigation.",
            ]
            return out
        if health.get("highest_severity") == "high" and out["guidance"] == PostDeploymentGuidance.CONTINUE.value:
            out["guidance"] = PostDeploymentGuidance.NARROW.value
            out["reason"] = "High-severity issues open; narrow scope until triaged."
            out["recommended_actions"] = [
                "workflow-dataset release triage",
                "Do not add new users/cohorts until high issues investigated.",
                "Consider narrowing to current cohort only.",
            ]
    except Exception as e:
        out["evidence"]["triage_error"] = str(e)

    # Reliability (golden-path)
    try:
        from workflow_dataset.reliability import load_latest_run
        latest = load_latest_run(root)
        outcome = (latest or {}).get("outcome", "")
        out["evidence"]["reliability_outcome"] = outcome
        if outcome in ("blocked", "fail") and out["guidance"] == PostDeploymentGuidance.CONTINUE.value:
            out["guidance"] = PostDeploymentGuidance.REPAIR.value
            out["reason"] = f"Reliability latest run outcome={outcome}; repair before continuing."
            out["recommended_actions"] = [
                "workflow-dataset reliability run",
                "workflow-dataset recovery suggest --subsystem <subsystem>",
                "Re-run production-runbook ongoing-summary after fix.",
            ]
    except Exception as e:
        out["evidence"]["reliability_error"] = str(e)

    # Default: continue (with optional actions if degraded)
    if out["guidance"] == PostDeploymentGuidance.CONTINUE.value:
        out["reason"] = "No blockers; triage and reliability acceptable. Continue operating; run regular review cycles."
        out["recommended_actions"] = [
            "workflow-dataset production-runbook review-cycle show",
            "workflow-dataset production-runbook sustained-use checkpoint",
            "Schedule next review per runbook.",
        ]
    return out
