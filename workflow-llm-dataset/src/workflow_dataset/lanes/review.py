"""
M28H.1: Parent/child review summaries and operator approval before accepting lane results.
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

from workflow_dataset.lanes.models import (
    HANDOFF_STATUS_DELIVERED,
    HANDOFF_STATUS_APPROVED,
    HANDOFF_STATUS_REJECTED,
    HANDOFF_STATUS_ACCEPTED,
)
from workflow_dataset.lanes.store import load_lane, save_lane


def build_parent_child_review(lane_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Build parent/child review summary: parent project/goal, child lane summary, artifacts, handoff status, recommendation.
    """
    lane = load_lane(lane_id, repo_root)
    if not lane:
        return {"error": "lane not found", "lane_id": lane_id}

    parent_project = lane.project_id
    parent_goal = lane.goal_id
    child_lane_id = lane.lane_id
    summary_snapshot = (
        lane.handoff.summary
        if lane.handoff
        else f"status={lane.status} artifacts={len(lane.artifacts)}"
    )
    artifacts_snapshot = [{"label": a.label, "path_or_type": a.path_or_type} for a in lane.artifacts]
    handoff_status = (lane.handoff.status if lane.handoff else "") or "no_handoff"
    recommendation = "approve" if handoff_status == HANDOFF_STATUS_DELIVERED else ("accept_into_project" if handoff_status == HANDOFF_STATUS_APPROVED else "none")

    return {
        "lane_id": lane_id,
        "parent_project_id": parent_project,
        "parent_goal_id": parent_goal,
        "child_lane_id": child_lane_id,
        "summary_snapshot": summary_snapshot,
        "artifacts_snapshot": artifacts_snapshot,
        "artifacts_count": len(lane.artifacts),
        "handoff_status": handoff_status,
        "handoff_id": lane.handoff.handoff_id if lane.handoff else "",
        "recommendation": recommendation,
        "approved_at": lane.handoff.approved_at if lane.handoff else "",
        "approved_by": lane.handoff.approved_by if lane.handoff else "",
        "rejection_reason": lane.handoff.rejection_reason if lane.handoff else "",
    }


def format_parent_child_review(lane_id: str, repo_root: Path | str | None = None) -> str:
    """Format parent/child review as readable text for operator."""
    r = build_parent_child_review(lane_id, repo_root)
    if r.get("error"):
        return f"Error: {r['error']}"

    lines = [
        "=== Parent/Child review ===",
        f"Parent: project={r.get('parent_project_id')}  goal={r.get('parent_goal_id')}",
        f"Child lane: {r.get('child_lane_id')}",
        f"Handoff: {r.get('handoff_status')}  id={r.get('handoff_id')}",
        f"Summary: {str(r.get('summary_snapshot', ''))[:200]}",
        f"Artifacts: {r.get('artifacts_count', 0)}",
    ]
    for a in r.get("artifacts_snapshot", [])[:10]:
        lines.append(f"  - {a.get('label')}  {a.get('path_or_type')}")
    if r.get("recommendation"):
        lines.append(f"Recommendation: {r['recommendation']}")
    if r.get("approved_by"):
        lines.append(f"Approved by: {r['approved_by']} at {r.get('approved_at')}")
    if r.get("rejection_reason"):
        lines.append(f"Rejection: {r['rejection_reason']}")
    return "\n".join(lines)


def approve_lane_handoff(
    lane_id: str,
    approved_by: str = "operator",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Operator approval: set handoff status to approved."""
    lane = load_lane(lane_id, repo_root)
    if not lane:
        return {"ok": False, "error": "lane not found", "lane_id": lane_id}
    if not lane.handoff:
        return {"ok": False, "error": "no handoff to approve", "lane_id": lane_id}
    if lane.handoff.status != HANDOFF_STATUS_DELIVERED:
        return {"ok": False, "error": f"handoff status is {lane.handoff.status}, expected delivered", "lane_id": lane_id}

    lane.handoff.status = HANDOFF_STATUS_APPROVED
    lane.handoff.approved_at = utc_now_iso()
    lane.handoff.approved_by = approved_by
    lane.handoff.rejection_reason = ""
    lane.updated_at = utc_now_iso()
    save_lane(lane, repo_root)
    return {"ok": True, "lane_id": lane_id, "status": HANDOFF_STATUS_APPROVED}


def reject_lane_handoff(
    lane_id: str,
    reason: str,
    rejected_by: str = "operator",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Operator rejection: set handoff status to rejected."""
    lane = load_lane(lane_id, repo_root)
    if not lane:
        return {"ok": False, "error": "lane not found", "lane_id": lane_id}
    if not lane.handoff:
        return {"ok": False, "error": "no handoff to reject", "lane_id": lane_id}
    if lane.handoff.status != HANDOFF_STATUS_DELIVERED:
        return {"ok": False, "error": f"handoff status is {lane.handoff.status}, expected delivered", "lane_id": lane_id}

    lane.handoff.status = HANDOFF_STATUS_REJECTED
    lane.handoff.approved_at = utc_now_iso()
    lane.handoff.approved_by = rejected_by
    lane.handoff.rejection_reason = reason or "rejected by operator"
    lane.updated_at = utc_now_iso()
    save_lane(lane, repo_root)
    return {"ok": True, "lane_id": lane_id, "status": HANDOFF_STATUS_REJECTED}


def accept_lane_results_into_project(
    lane_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Accept approved lane results into the main project (attach artifacts to project). Only when handoff is approved."""
    lane = load_lane(lane_id, repo_root)
    if not lane:
        return {"ok": False, "error": "lane not found", "lane_id": lane_id}
    if not lane.handoff:
        return {"ok": False, "error": "no handoff", "lane_id": lane_id}
    if lane.handoff.status != HANDOFF_STATUS_APPROVED:
        return {"ok": False, "error": f"handoff must be approved first (current: {lane.handoff.status})", "lane_id": lane_id}
    if not lane.project_id:
        return {"ok": False, "error": "lane has no project_id", "lane_id": lane_id}

    try:
        from workflow_dataset.project_case.store import attach_artifact, load_project
    except Exception as e:
        return {"ok": False, "error": str(e), "lane_id": lane_id}

    if not load_project(lane.project_id, repo_root):
        return {"ok": False, "error": f"project not found: {lane.project_id}", "lane_id": lane_id}

    attached = 0
    for a in lane.artifacts:
        path_or_label = a.path_or_type or a.label
        if path_or_label and path_or_label != "simulated":
            if attach_artifact(lane.project_id, path_or_label, repo_root):
                attached += 1
        if a.label and (not a.path_or_type or a.path_or_type == "simulated"):
            if attach_artifact(lane.project_id, f"lane:{lane_id}:{a.label}", repo_root):
                attached += 1

    lane.handoff.status = HANDOFF_STATUS_ACCEPTED
    lane.handoff.acknowledged_at = utc_now_iso()
    lane.updated_at = utc_now_iso()
    save_lane(lane, repo_root)
    return {"ok": True, "lane_id": lane_id, "status": HANDOFF_STATUS_ACCEPTED, "artifacts_attached": attached}
