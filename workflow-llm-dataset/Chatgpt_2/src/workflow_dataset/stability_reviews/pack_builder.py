"""
M46I–M46L: Build stability decision pack from long-run health, drift, repair, support, value, trust, scope (read-only from existing layers).
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from workflow_dataset.stability_reviews.models import (
    StabilityDecision,
    StabilityWindow,
    EvidenceBundle,
    StabilityDecisionPack,
    ContinueRecommendation,
    NarrowRecommendation,
    RepairRecommendation,
    PauseRecommendation,
    RollbackRecommendation,
)


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_stability_decision_pack(
    repo_root: Path | str | None = None,
    window_kind: str = "rolling_7",
) -> StabilityDecisionPack:
    """
    Assemble evidence from launch pack, ongoing summary, review cycles, sustained use, post-deployment guidance
    (and read-only triage/reliability) into an evidence bundle and stability decision pack.
    window_kind: daily | weekly | rolling_7 | rolling_30.
    """
    root = _repo_root(repo_root)
    now = datetime.now(timezone.utc)
    at_iso = now.isoformat()[:19] + "Z"

    if window_kind == "daily":
        start = (now - timedelta(days=1)).isoformat()[:19] + "Z"
        label = "Last 24h"
    elif window_kind == "weekly":
        start = (now - timedelta(days=7)).isoformat()[:19] + "Z"
        label = "Last 7 days"
    elif window_kind == "rolling_30":
        start = (now - timedelta(days=30)).isoformat()[:19] + "Z"
        label = "Last 30 days"
    else:
        start = (now - timedelta(days=7)).isoformat()[:19] + "Z"
        label = "Last 7 days (rolling)"
        window_kind = "rolling_7"
    window = StabilityWindow(kind=window_kind, start_iso=start, end_iso=at_iso, label=label)

    # ---- Evidence sources (read-only; do not rebuild those systems) ----
    launch_pack: dict[str, Any] = {}
    ongoing: dict[str, Any] = {}
    guidance: dict[str, Any] = {}
    latest_cycle: dict[str, Any] | None = None
    checkpoints: list[dict[str, Any]] = []
    vertical_id = ""

    try:
        from workflow_dataset.production_launch.decision_pack import build_launch_decision_pack
        launch_pack = build_launch_decision_pack(root)
        vertical_id = (launch_pack.get("chosen_vertical_summary") or {}).get("active_vertical_id", "")
    except Exception as e:
        launch_pack = {"error": str(e)}

    try:
        from workflow_dataset.production_launch.ongoing_summary import build_ongoing_production_summary
        ongoing = build_ongoing_production_summary(root)
    except Exception as e:
        ongoing = {"error": str(e)}

    try:
        from workflow_dataset.production_launch.post_deployment_guidance import build_post_deployment_guidance
        guidance = build_post_deployment_guidance(root)
    except Exception as e:
        guidance = {"guidance": "continue", "reason": str(e), "evidence": {}}

    try:
        from workflow_dataset.production_launch.review_cycles import get_latest_review_cycle
        latest_cycle = get_latest_review_cycle(root)
    except Exception:
        pass

    try:
        from workflow_dataset.production_launch.sustained_use import list_sustained_use_checkpoints
        checkpoints = list_sustained_use_checkpoints(root, limit=5)
    except Exception:
        pass

    # Optional: triage/reliability for evidence only
    triage_issues = 0
    reliability_outcome = ""
    try:
        from workflow_dataset.triage.health import build_cohort_health_summary
        health = build_cohort_health_summary(root)
        triage_issues = health.get("open_issue_count", 0)
    except Exception:
        pass
    try:
        from workflow_dataset.reliability import load_latest_run
        latest = load_latest_run(root)
        reliability_outcome = (latest or {}).get("outcome", "")
    except Exception:
        pass

    # ---- Evidence bundle ----
    blockers = launch_pack.get("open_blockers", [])
    warnings = launch_pack.get("open_warnings", [])
    failed_gates = [g for g in launch_pack.get("release_gate_results", []) if not g.get("passed")]
    health_summary = _summarize_health(blockers, warnings, failed_gates, triage_issues, reliability_outcome)
    drift_signals: list[str] = []
    if guidance.get("evidence", {}).get("degraded"):
        drift_signals.append("Post-deployment guidance reports degraded state.")
    if ongoing.get("checkpoint_criteria_met") is False and checkpoints:
        drift_signals.append("Sustained-use criteria not met for current window.")
    repair_history_summary = _summarize_repair_history(checkpoints, latest_cycle)
    support_triage_burden = f"Open triage issues: {triage_issues}. " if triage_issues else "No open triage burden. "
    support_triage_burden += (guidance.get("evidence", {}).get("highest_severity") or "—")
    operator_burden = launch_pack.get("support_posture", "") or "Unknown"
    vertical_value_retention = ongoing.get("one_liner", "") or "No ongoing summary."
    trust_review_posture = launch_pack.get("trust_posture", "") or "Unknown"
    production_scope_compliance = "In scope" if not blockers else "Blockers present; scope at risk."

    evidence = EvidenceBundle(
        health_summary=health_summary,
        drift_signals=drift_signals,
        repair_history_summary=repair_history_summary,
        support_triage_burden=support_triage_burden,
        operator_burden=operator_burden[:200],
        vertical_value_retention=vertical_value_retention[:200],
        trust_review_posture=trust_review_posture[:200],
        production_scope_compliance=production_scope_compliance,
        raw_snapshot={
            "launch_recommended_decision": launch_pack.get("recommended_decision"),
            "guidance": guidance.get("guidance"),
            "blocker_count": len(blockers),
            "warning_count": len(warnings),
            "failed_gates_count": len(failed_gates),
            "triage_open_issues": triage_issues,
            "reliability_outcome": reliability_outcome,
        },
    )

    # ---- M46L.1: Load thresholds and rollback policy; apply operator thresholds ----
    thresholds = _load_thresholds(root)
    rollback_policy = _load_rollback_policy(root)
    reviews_for_prior = _list_reviews_for_prior(root)
    cohort_downgrade = (guidance.get("evidence") or {}).get("recommended_downgrade", False)
    consecutive_pause = _count_consecutive_pause(reviews_for_prior)
    threshold_band = _apply_thresholds(
        thresholds,
        blocker_count=len(blockers),
        warning_count=len(warnings),
        failed_gates_count=len(failed_gates),
        triage_issues=triage_issues,
        checkpoint_criteria_met=ongoing.get("checkpoint_criteria_met", False) is True,
        health_summary_has_signals=bool(health_summary and "No major" not in health_summary),
    )
    prior_stable_ref = _resolve_prior_stable_ref(rollback_policy, reviews_for_prior)
    should_rollback_by_policy, rollback_reason = _evaluate_rollback_policy(
        rollback_policy, guidance.get("guidance", ""), cohort_downgrade, len(blockers), consecutive_pause,
    )

    # ---- Decision: map guidance + launch + evidence + thresholds to stability decision ----
    recommended, rationale, rec_continue, rec_narrow, rec_repair, rec_pause, rec_rollback = _decide(
        launch_pack, guidance, evidence, ongoing,
        threshold_band=threshold_band,
        prior_stable_ref=prior_stable_ref,
        should_rollback_by_policy=should_rollback_by_policy,
        rollback_reason=rollback_reason,
        rollback_policy=rollback_policy,
    )
    evidence_refs = [
        "launch_decision_pack",
        "post_deployment_guidance",
        "ongoing_summary",
        "evidence_bundle",
    ]

    pack = StabilityDecisionPack(
        recommended_decision=recommended,
        rationale=rationale,
        evidence_refs=evidence_refs,
        evidence_bundle=evidence,
        continue_rec=rec_continue,
        narrow_rec=rec_narrow,
        repair_rec=rec_repair,
        pause_rec=rec_pause,
        rollback_rec=rec_rollback,
        generated_at_iso=at_iso,
        stability_window=window,
        vertical_id=vertical_id,
    )
    return pack


def _summarize_health(
    blockers: list,
    warnings: list,
    failed_gates: list,
    triage_issues: int,
    reliability_outcome: str,
) -> str:
    parts = []
    if blockers:
        parts.append(f"Blockers: {len(blockers)}.")
    if warnings:
        parts.append(f"Warnings: {len(warnings)}.")
    if failed_gates:
        parts.append(f"Failed gates: {len(failed_gates)}.")
    if triage_issues:
        parts.append(f"Open triage issues: {triage_issues}.")
    if reliability_outcome and reliability_outcome not in ("pass", "unknown", ""):
        parts.append(f"Reliability: {reliability_outcome}.")
    return " ".join(parts) if parts else "No major health signals in window."


def _summarize_repair_history(
    checkpoints: list[dict[str, Any]],
    latest_cycle: dict[str, Any] | None,
) -> str:
    if not checkpoints and not latest_cycle:
        return "No recorded repair/checkpoint history in window."
    recs = []
    if latest_cycle:
        recs.append(f"Latest review cycle: {latest_cycle.get('guidance_snapshot', '—')}.")
    for c in checkpoints[:3]:
        recs.append(f"Checkpoint {c.get('kind', '')}: criteria_met={c.get('criteria_met')}.")
    return " ".join(recs)


def _load_thresholds(root: Path) -> Any:
    try:
        from workflow_dataset.stability_reviews.thresholds import load_thresholds
        return load_thresholds(root)
    except Exception:
        from workflow_dataset.stability_reviews.thresholds import get_default_thresholds
        return get_default_thresholds()


def _load_rollback_policy(root: Path) -> Any:
    try:
        from workflow_dataset.stability_reviews.rollback_policy import load_rollback_policy
        return load_rollback_policy(root)
    except Exception:
        from workflow_dataset.stability_reviews.rollback_policy import get_default_rollback_policy
        return get_default_rollback_policy()


def _list_reviews_for_prior(root: Path) -> list[dict[str, Any]]:
    try:
        from workflow_dataset.stability_reviews.store import list_reviews
        return list_reviews(root, limit=20)
    except Exception:
        return []


def _count_consecutive_pause(reviews: list[dict[str, Any]]) -> int:
    n = 0
    for r in reviews:
        if (r.get("decision_pack") or {}).get("recommended_decision") != "pause":
            break
        n += 1
    return n


def _apply_thresholds(
    thresholds: Any,
    *,
    blocker_count: int,
    warning_count: int,
    failed_gates_count: int,
    triage_issues: int,
    checkpoint_criteria_met: bool,
    health_summary_has_signals: bool,
) -> dict[str, Any]:
    try:
        from workflow_dataset.stability_reviews.thresholds import apply_thresholds
        return apply_thresholds(
            thresholds,
            blocker_count=blocker_count,
            warning_count=warning_count,
            failed_gates_count=failed_gates_count,
            triage_issues=triage_issues,
            checkpoint_criteria_met=checkpoint_criteria_met,
            health_summary_has_signals=health_summary_has_signals,
        )
    except Exception:
        return {"band": "continue_with_watch", "reason": "Thresholds unavailable.", "overrides_watch": True}


def _resolve_prior_stable_ref(rollback_policy: Any, reviews: list[dict[str, Any]]) -> str:
    try:
        from workflow_dataset.stability_reviews.rollback_policy import resolve_prior_stable_ref
        return resolve_prior_stable_ref(rollback_policy, reviews)
    except Exception:
        return ""


def _evaluate_rollback_policy(
    policy: Any,
    guidance: str,
    cohort_downgrade: bool,
    blocker_count: int,
    consecutive_pause_count: int,
) -> tuple[bool, str]:
    try:
        from workflow_dataset.stability_reviews.rollback_policy import evaluate_rollback_policy
        return evaluate_rollback_policy(
            policy, guidance, cohort_downgrade, blocker_count, consecutive_pause_count,
        )
    except Exception:
        return False, ""


def _decide(
    launch_pack: dict[str, Any],
    guidance: dict[str, Any],
    evidence: EvidenceBundle,
    ongoing: dict[str, Any],
    threshold_band: dict[str, Any] | None = None,
    prior_stable_ref: str = "",
    should_rollback_by_policy: bool = False,
    rollback_reason: str = "",
    rollback_policy: Any = None,
) -> tuple[
    str, str,
    ContinueRecommendation | None,
    NarrowRecommendation | None,
    RepairRecommendation | None,
    PauseRecommendation | None,
    RollbackRecommendation | None,
]:
    g = (guidance.get("guidance") or "continue").lower()
    launch_rec = (launch_pack.get("recommended_decision") or "pause").lower()
    blockers = launch_pack.get("open_blockers", [])
    warnings = launch_pack.get("open_warnings", [])
    reason = guidance.get("reason", "")
    band = (threshold_band or {}).get("band", "continue_with_watch")

    # Rollback: guidance says rollback, or policy recommends rollback
    if g == "rollback" or should_rollback_by_policy:
        rec = RollbackRecommendation(
            rationale=reason or rollback_reason or "Post-deployment guidance recommends rollback.",
            evidence_refs=["post_deployment_guidance", "evidence_bundle"],
            prior_stable_ref=prior_stable_ref,
        )
        return (
            StabilityDecision.ROLLBACK.value,
            reason or rollback_reason or "Guidance=rollback; evidence supports rollback to prior stable state.",
            None, None, None, None, rec,
        )

    # Pause: launch decision is pause and we're not already in rollback/repair
    if launch_rec == "pause" and g != "rollback":
        rec = PauseRecommendation(
            rationale=launch_pack.get("explain", "Launch decision is pause."),
            evidence_refs=["launch_decision_pack", "evidence_bundle"],
            resume_condition="Resolve blockers and re-run stability-reviews generate.",
        )
        return (
            StabilityDecision.PAUSE.value,
            launch_pack.get("explain", "Pause deployment until blockers resolved."),
            None, None, None, rec, None,
        )

    # Repair: guidance repair or launch repair_and_review
    if g == "repair" or launch_rec == "repair_and_review":
        rec = RepairRecommendation(
            rationale=reason or "Blockers or critical issues require repair before expanding.",
            evidence_refs=["post_deployment_guidance", "launch_decision_pack", "evidence_bundle"],
            repair_bundle_ref="workflow-dataset launch-decision pack",
        )
        return (
            StabilityDecision.REPAIR.value,
            reason or "Repair recommended; run repair bundle then re-review.",
            None, None, rec, None, None,
        )

    # Narrow: guidance narrow or thresholds band = narrow
    if g == "narrow" or (band == "narrow" and not blockers):
        rec = NarrowRecommendation(
            rationale=reason or (threshold_band or {}).get("reason", "High-severity issues; narrow scope until triaged."),
            evidence_refs=["post_deployment_guidance", "evidence_bundle"],
            suggested_scope_note="Restrict to current cohort; do not add new users until high issues resolved.",
        )
        return (
            StabilityDecision.NARROW.value,
            reason or (threshold_band or {}).get("reason", "Narrow supported scope; monitor."),
            None, rec, None, None, None,
        )

    # Continue vs watch: use threshold band for operator-facing clarity
    if band == "continue_with_watch" and not blockers:
        rec = ContinueRecommendation(
            decision=StabilityDecision.CONTINUE_WITH_WATCH.value,
            rationale=reason or (threshold_band or {}).get("reason", "Continue operating; evidence is weak or warnings present—watch state."),
            evidence_refs=["evidence_bundle", "ongoing_summary", "thresholds"],
            confidence="low",
        )
        return (
            StabilityDecision.CONTINUE_WITH_WATCH.value,
            (threshold_band or {}).get("reason", "Continue with watch; gather more evidence and monitor."),
            rec, None, None, None, None,
        )

    rec = ContinueRecommendation(
        decision=StabilityDecision.CONTINUE.value,
        rationale=reason or "No blockers; within thresholds. Continue as-is. Run regular review cycles.",
        evidence_refs=["post_deployment_guidance", "evidence_bundle"],
        confidence="medium",
    )
    return (
        StabilityDecision.CONTINUE.value,
        reason or "Stability acceptable; continue deployment.",
        rec, None, None, None, None,
    )
