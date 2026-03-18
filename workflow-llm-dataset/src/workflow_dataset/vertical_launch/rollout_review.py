"""
M39L.1: Vertical rollout review packs — evidence summary, what's working/not,
recommended continue/narrow/pause/expand decision, operator summary.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.vertical_launch.models import (
    RolloutReviewPack,
    RolloutDecision,
    ROLLOUT_CONTINUE,
    ROLLOUT_NARROW,
    ROLLOUT_PAUSE,
    ROLLOUT_EXPAND,
)
from workflow_dataset.vertical_launch.dashboard import build_value_dashboard
from workflow_dataset.vertical_launch.store import list_rollout_decisions
from workflow_dataset.vertical_launch.kits import build_launch_kit_for_vertical


def _normalize_launch_kit_id(id: str) -> str:
    if not id:
        return ""
    return id if id.endswith("_launch") else f"{id}_launch"


def get_recommended_decision(
    proof_met_count: int,
    proof_failed_count: int,
    first_value_reached: bool,
    blocked_step_index: int,
) -> tuple[str, str]:
    """
    Recommend rollout decision and rationale from dashboard signals.
    Returns (decision, rationale).
    """
    if proof_failed_count > 2 or blocked_step_index > 0 and proof_met_count < 2:
        return (
            ROLLOUT_PAUSE,
            "Multiple proofs failed or blocked early with little progress; pause and fix before continuing.",
        )
    if blocked_step_index > 0:
        return (
            ROLLOUT_NARROW,
            "Path blocked; narrow scope (e.g. simulate-only or fewer surfaces) or run recovery before expanding.",
        )
    if not first_value_reached and proof_met_count < 2:
        return (
            ROLLOUT_NARROW,
            "First-value not yet reached; continue with narrow scope until first-value milestone.",
        )
    if first_value_reached and proof_met_count >= 3:
        return (
            ROLLOUT_EXPAND,
            "First-value reached and multiple proofs met; consider expanding scope or adding users.",
        )
    if first_value_reached:
        return (
            ROLLOUT_CONTINUE,
            "First-value reached; continue current scope and collect more proof signals.",
        )
    return (
        ROLLOUT_CONTINUE,
        "Continue current scope; run first-value path to reach first-value milestone.",
    )


def build_rollout_review_pack(
    launch_kit_id_or_pack_id: str,
    repo_root: Path | str | None = None,
) -> RolloutReviewPack:
    """
    Build rollout review pack for a vertical: dashboard + previous decisions,
    recommended decision (continue/narrow/pause/expand), operator summary.
    """
    try:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
    except Exception:
        now = ""
    root = Path(repo_root).resolve() if repo_root else None
    launch_kit_id = _normalize_launch_kit_id(launch_kit_id_or_pack_id)
    pack_id = launch_kit_id.replace("_launch", "") if launch_kit_id else launch_kit_id_or_pack_id
    if not launch_kit_id:
        launch_kit_id = pack_id + "_launch"

    dashboard = build_value_dashboard(launch_kit_id_or_pack_id, repo_root=root)
    kit = build_launch_kit_for_vertical(pack_id)
    previous = list_rollout_decisions(launch_kit_id=launch_kit_id, limit=10, repo_root=root)
    previous_decisions = [
        RolloutDecision(
            decision_id=d.get("decision_id", ""),
            vertical_id=d.get("vertical_id", ""),
            launch_kit_id=d.get("launch_kit_id", ""),
            decision=d.get("decision", ROLLOUT_CONTINUE),
            rationale=d.get("rationale", ""),
            recorded_at_utc=d.get("recorded_at_utc", ""),
            recorded_by=d.get("recorded_by", ""),
        )
        for d in previous
    ]

    proof_met = dashboard.get("proof_summary", {}).get("met_count", 0)
    proof_pending = dashboard.get("proof_summary", {}).get("pending_count", 0)
    proof_failed = dashboard.get("proof_summary", {}).get("failed_count", 0)
    first_value_reached = dashboard.get("proof_summary", {}).get("first_value_milestone_reached", False)
    blocked = dashboard.get("milestone_progress", {}).get("blocked_step_index", 0)

    recommended_decision, recommended_rationale = get_recommended_decision(
        proof_met, proof_failed, first_value_reached, blocked,
    )

    evidence_summary = (
        f"Proofs met: {proof_met}, pending: {proof_pending}, failed: {proof_failed}. "
        f"First-value reached: {first_value_reached}. Blocked step: {blocked or 'none'}. "
        f"Previous decisions: {len(previous_decisions)}."
    )

    return RolloutReviewPack(
        vertical_id=pack_id,
        launch_kit_id=launch_kit_id,
        curated_pack_id=pack_id,
        label=kit.label,
        evidence_summary=evidence_summary,
        what_is_working=list(dashboard.get("what_is_working", [])),
        what_is_not_working=list(dashboard.get("what_is_not_working", [])),
        recommended_decision=recommended_decision,
        recommended_rationale=recommended_rationale,
        operator_summary=dashboard.get("operator_summary", ""),
        proof_met_count=proof_met,
        proof_pending_count=proof_pending,
        first_value_reached=first_value_reached,
        blocked_step_index=blocked,
        previous_decisions=previous_decisions,
        generated_at_utc=now,
    )


def list_rollout_review_packs(repo_root: Path | str | None = None) -> list[RolloutReviewPack]:
    """Build rollout review pack for each known launch kit."""
    from workflow_dataset.vertical_launch.kits import list_launch_kits
    kits = list_launch_kits()
    return [build_rollout_review_pack(k.launch_kit_id, repo_root) for k in kits]
