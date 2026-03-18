"""
M50E–M50H Phase A/B: Build v1 support posture from release_readiness, stability_reviews, deploy_bundle, reliability, repair_loops.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workflow_dataset.v1_ops.models import V1SupportPosture


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _guidance_to_support_level(guidance: str) -> str:
    g = (guidance or "").strip().lower()
    if g == "rollback" or "rollback" in g:
        return "maintenance"
    if g in ("needs_operator", "needs operator"):
        return "maintenance"
    if g in ("safe_to_continue", "safe to continue"):
        return "sustained"
    return "sustained"


def build_v1_support_posture(repo_root: Path | str | None = None) -> V1SupportPosture:
    """
    Build v1 support posture by aggregating:
    - release_readiness supportability (guidance, confidence)
    - stability_reviews active cadence (next due)
    - deploy_bundle recovery/rollback when active bundle exists
    - repair_loops mission_control slice (repair needed)
    """
    root = _repo_root(repo_root)
    now = datetime.now(timezone.utc)
    as_of = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    support_paths: list[str] = []
    support_level = "sustained"
    recovery_posture_summary = ""
    rollback_ready = False
    maintenance_rhythm_id = "stable_v1_daily_weekly"
    review_cadence_id = "rolling_stability"

    # Release readiness / supportability
    try:
        from workflow_dataset.release_readiness.supportability import build_supportability_report
        report = build_supportability_report(root)
        guidance = report.get("guidance") or report.get("recommended_next_support_action") or ""
        support_level = _guidance_to_support_level(guidance)
        support_paths.append("release_readiness: workflow-dataset supportability")
    except Exception:
        support_paths.append("release_readiness: (unavailable)")

    # Stability reviews cadence
    try:
        from workflow_dataset.stability_reviews.cadences import load_active_cadence, next_review_due_iso
        cadence = load_active_cadence(root)
        review_cadence_id = cadence.cadence_id
        next_due = next_review_due_iso(cadence)
        support_paths.append(f"stability_reviews: workflow-dataset stability-reviews latest (next_due={next_due[:10]})")
    except Exception:
        support_paths.append("stability_reviews: (unavailable)")

    # Deploy bundle recovery + rollback
    try:
        from workflow_dataset.deploy_bundle import get_active_bundle, get_rollback_readiness, build_recovery_report
        active = get_active_bundle(root)
        if active:
            bid = active.get("active_bundle_id") or active.get("bundle_id") or active.get("id") or "founder_operator_prod"
            rec = build_recovery_report(bid, repo_root=root)
            recovery_posture_summary = (
                rec.get("degraded_startup_guidance")
                or rec.get("recovery_posture", {}).get("degraded_startup_guidance")
                or "Run workflow-dataset deploy-bundle recovery-report for recovery steps."
            )
            if len(recovery_posture_summary) > 300:
                recovery_posture_summary = recovery_posture_summary[:297] + "..."
            roll = get_rollback_readiness(bid, repo_root=root)
            rollback_ready = bool(roll.get("ready", False))
            support_paths.append("deploy_bundle: workflow-dataset deploy-bundle recovery-report")
    except Exception:
        recovery_posture_summary = recovery_posture_summary or "Run workflow-dataset deploy-bundle recovery-report."
        support_paths.append("deploy_bundle: (unavailable)")

    # Repair loops: if top repair needed, mention
    try:
        from workflow_dataset.mission_control.state import get_mission_control_state
        state = get_mission_control_state(root)
        repair = state.get("repair_slice") or {}
        if repair.get("top_repair_needed_id") or repair.get("active_repair_loop_id"):
            support_paths.append("repair_loops: workflow-dataset repair-loops list (action needed)")
    except Exception:
        pass

    return V1SupportPosture(
        posture_id="v1_stable_posture",
        support_level=support_level,
        support_paths=support_paths,
        maintenance_rhythm_id=maintenance_rhythm_id,
        review_cadence_id=review_cadence_id,
        recovery_posture_summary=recovery_posture_summary or "See recovery playbooks and deploy-bundle recovery-report.",
        rollback_ready=rollback_ready,
        as_of_utc=as_of,
    )
