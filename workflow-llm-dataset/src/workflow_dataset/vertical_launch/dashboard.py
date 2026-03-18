"""
M39L.1: Vertical value dashboard — aggregate proof state, milestone progress,
what is working / what is not, operator-facing summary.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.vertical_launch.store import get_active_launch, get_proof_state
from workflow_dataset.vertical_launch.success_proof import build_success_proof_report
from workflow_dataset.vertical_packs.progress import build_milestone_progress_output
from workflow_dataset.vertical_launch.kits import build_launch_kit_for_vertical


def _normalize_launch_kit_id(launch_kit_id: str) -> str:
    if not launch_kit_id:
        return ""
    return launch_kit_id if launch_kit_id.endswith("_launch") else f"{launch_kit_id}_launch"


def build_value_dashboard(
    launch_kit_id_or_pack_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Build vertical value dashboard for a launch kit. Aggregates:
    - launch_kit_id, curated_pack_id, label
    - launch_started_at_utc (if this kit is active)
    - proof summary (met_count, pending_count, failed_count, first_value_milestone_reached)
    - milestone progress (reached_milestone_ids, next_milestone_id, blocked_step_index)
    - what_is_working: list of short strings (proofs met, milestones reached, no block)
    - what_is_not_working: list of short strings (blocked step, proofs pending/failed, no launch)
    - operator_summary: one-paragraph operator-facing summary
    """
    root = Path(repo_root).resolve() if repo_root else None
    launch_kit_id = _normalize_launch_kit_id(launch_kit_id_or_pack_id)
    pack_id = launch_kit_id.replace("_launch", "") if launch_kit_id else launch_kit_id_or_pack_id
    if not launch_kit_id:
        launch_kit_id = pack_id + "_launch"

    kit = build_launch_kit_for_vertical(pack_id)
    active = get_active_launch(root)
    is_active = active.get("active_launch_kit_id") == launch_kit_id
    proof_report = build_success_proof_report(launch_kit_id, repo_root=root)
    progress = build_milestone_progress_output(root) if is_active else {}
    if not is_active:
        progress = progress or {}
    # When not active, progress may be for another pack; only use if pack matches
    if progress.get("active_curated_pack_id") != pack_id:
        progress = {}

    proof_met = proof_report.get("met_count", 0)
    proof_pending = proof_report.get("pending_count", 0)
    proof_failed = proof_report.get("failed_count", 0)
    first_value_reached = proof_report.get("first_value_milestone_reached", False)
    reached_milestones = progress.get("reached_milestone_ids", [])
    next_milestone = progress.get("next_milestone_id", "")
    next_milestone_label = progress.get("next_vertical_milestone_label", "")
    blocked = progress.get("blocked_step_index", 0)
    launch_started_at = active.get("launch_started_at_utc", "") if is_active else ""

    what_is_working: list[str] = []
    what_is_not_working: list[str] = []

    if proof_met > 0:
        what_is_working.append(f"{proof_met} success proof(s) met")
    if first_value_reached:
        what_is_working.append("First-value milestone reached")
    if reached_milestones:
        what_is_working.append(f"Milestones reached: {', '.join(reached_milestones[:5])}{'...' if len(reached_milestones) > 5 else ''}")
    if is_active and launch_started_at:
        what_is_working.append("Launch active (started " + launch_started_at[:10] + ")")
    if not blocked and is_active:
        what_is_working.append("No blocked step")

    if not is_active and not launch_started_at:
        what_is_not_working.append("Launch not started for this vertical")
    if blocked:
        what_is_not_working.append(f"Blocked at step {blocked}; run vertical-packs progress or recovery")
    if proof_pending > 0:
        what_is_not_working.append(f"{proof_pending} proof(s) still pending")
    if proof_failed > 0:
        what_is_not_working.append(f"{proof_failed} proof(s) failed")
    if not next_milestone and is_active and not reached_milestones:
        what_is_not_working.append("No milestone progress yet; run first-value path")

    if not what_is_working:
        what_is_working.append("No value signals yet (start launch and run first-value path)")
    if not what_is_not_working:
        what_is_not_working.append("—")

    operator_summary_parts = [
        f"Vertical: {kit.label}. Proofs met: {proof_met}, pending: {proof_pending}, failed: {proof_failed}.",
        f"First-value reached: {first_value_reached}. Blocked step: {blocked or 'none'}.",
    ]
    if what_is_working:
        operator_summary_parts.append("Working: " + "; ".join(what_is_working[:3]))
    if what_is_not_working and what_is_not_working != ["—"]:
        operator_summary_parts.append("Not working: " + "; ".join(what_is_not_working[:3]))
    operator_summary = " ".join(operator_summary_parts)

    return {
        "launch_kit_id": launch_kit_id,
        "curated_pack_id": pack_id,
        "label": kit.label,
        "launch_started_at_utc": launch_started_at,
        "is_active": is_active,
        "proof_summary": {
            "met_count": proof_met,
            "pending_count": proof_pending,
            "failed_count": proof_failed,
            "first_value_milestone_reached": first_value_reached,
        },
        "milestone_progress": {
            "reached_milestone_ids": list(reached_milestones),
            "next_milestone_id": next_milestone,
            "next_milestone_label": next_milestone_label,
            "blocked_step_index": blocked,
            "suggested_next_command": progress.get("suggested_next_command", "workflow-dataset vertical-packs first-value --id " + pack_id),
        },
        "what_is_working": what_is_working,
        "what_is_not_working": what_is_not_working,
        "operator_summary": operator_summary,
    }
    try:
        from datetime import datetime, timezone
        out["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    except Exception:
        out["generated_at_utc"] = ""


def list_value_dashboards(repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """Build value dashboard for each known launch kit (from list_launch_kits)."""
    from workflow_dataset.vertical_launch.kits import list_launch_kits
    kits = list_launch_kits()
    return [build_value_dashboard(k.launch_kit_id, repo_root) for k in kits]
