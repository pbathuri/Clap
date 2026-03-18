"""
M28E–M28H: Lane execution — simulate delegated subplan, collect results, return summary to parent.
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
    WorkerLane,
    LaneArtifact,
    LaneFailure,
    LaneHandoff,
    LANE_STATUS_OPEN,
    LANE_STATUS_RUNNING,
    LANE_STATUS_BLOCKED,
    LANE_STATUS_COMPLETED,
    READINESS_READY,
    READINESS_NOT_READY,
)
from workflow_dataset.lanes.store import load_lane, save_lane


def format_lane_trust_readiness(lane: WorkerLane) -> str:
    """M28H.1: Format lane-level trust and readiness for reporting."""
    trust = lane.trust_summary or lane.permissions.permission or "simulate_only"
    readiness = lane.readiness_status or (READINESS_READY if lane.status not in (LANE_STATUS_BLOCKED,) and not lane.failure else READINESS_NOT_READY)
    reason = lane.readiness_reason or ("blocked" if lane.failure else "" if readiness == READINESS_READY else "incomplete")
    return f"trust={trust}  readiness={readiness}" + (f"  reason={reason}" if reason else "")


def update_lane_trust_readiness(lane: WorkerLane) -> None:
    """Set trust_summary and readiness_status on lane if not already set."""
    if not lane.trust_summary:
        lane.trust_summary = lane.permissions.permission or "simulate_only"
    if not lane.readiness_status:
        if lane.status == LANE_STATUS_BLOCKED or lane.failure:
            lane.readiness_status = READINESS_NOT_READY
            lane.readiness_reason = lane.failure.reason if lane.failure else "blocked"
        else:
            lane.readiness_status = READINESS_READY
            lane.readiness_reason = ""


def run_lane_simulate(lane_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Simulate execution of the lane's delegated subplan.
    Does not call executor unless explicitly wired; updates lane status and produces a minimal result.
    """
    lane = load_lane(lane_id, repo_root)
    if not lane:
        return {"ok": False, "error": "lane not found", "lane_id": lane_id}
    if lane.status not in ("open", "blocked"):
        return {"ok": False, "error": f"lane status is {lane.status}, expected open or blocked", "lane_id": lane_id}

    lane.status = LANE_STATUS_RUNNING
    lane.updated_at = utc_now_iso()
    lane.failure = None

    if not lane.subplan or not lane.subplan.steps:
        lane.status = LANE_STATUS_COMPLETED
        lane.artifacts.append(LaneArtifact(label="empty_subplan_summary", path_or_type="summary", produced_at=utc_now_iso()))
        update_lane_trust_readiness(lane)
        save_lane(lane, repo_root)
        return {"ok": True, "lane_id": lane_id, "status": lane.status, "artifacts_count": len(lane.artifacts)}

    # Simulate: for each step, record a placeholder artifact (real executor handoff would go here)
    for step in lane.subplan.steps:
        artifact = LaneArtifact(
            label=step.label[:40] or f"step_{step.step_index}",
            path_or_type="simulated",
            step_index=step.step_index,
            produced_at=utc_now_iso(),
        )
        lane.artifacts.append(artifact)

    lane.status = LANE_STATUS_COMPLETED
    lane.updated_at = utc_now_iso()
    update_lane_trust_readiness(lane)
    save_lane(lane, repo_root)
    return {"ok": True, "lane_id": lane_id, "status": lane.status, "artifacts_count": len(lane.artifacts)}


def set_lane_blocked(lane_id: str, reason: str, step_index: int | None = None, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Mark lane as blocked with a reason."""
    lane = load_lane(lane_id, repo_root)
    if not lane:
        return {"ok": False, "error": "lane not found", "lane_id": lane_id}
    from workflow_dataset.lanes.models import LaneFailure
    lane.failure = LaneFailure(reason=reason, step_index=step_index, timestamp=utc_now_iso())
    lane.status = LANE_STATUS_BLOCKED
    lane.updated_at = utc_now_iso()
    update_lane_trust_readiness(lane)
    save_lane(lane, repo_root)
    return {"ok": True, "lane_id": lane_id, "status": lane.status}


def collect_lane_results(lane_id: str, repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """Collect artifact summaries for a lane."""
    lane = load_lane(lane_id, repo_root)
    if not lane:
        return []
    return [a.to_dict() for a in lane.artifacts]


def build_lane_summary(lane_id: str, repo_root: Path | str | None = None) -> dict[str, Any]:
    """Build a lane summary for handoff to parent project/loop."""
    lane = load_lane(lane_id, repo_root)
    if not lane:
        return {"error": "lane not found", "lane_id": lane_id}
    return {
        "lane_id": lane.lane_id,
        "project_id": lane.project_id,
        "goal_id": lane.goal_id,
        "status": lane.status,
        "artifacts_count": len(lane.artifacts),
        "artifact_labels": [a.label for a in lane.artifacts],
        "failure": lane.failure.to_dict() if lane.failure else None,
        "run_id": lane.run_id,
    }


def deliver_lane_handoff(
    lane_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Create a handoff record for lane results to parent project/loop.
    Marks handoff as delivered; parent can acknowledge later.
    """
    lane = load_lane(lane_id, repo_root)
    if not lane:
        return {"ok": False, "error": "lane not found", "lane_id": lane_id}
    try:
        from workflow_dataset.utils.hashes import stable_id
    except Exception:
        def stable_id(*parts: str, prefix: str = "") -> str:
            import hashlib
            return prefix + hashlib.sha256("".join(parts).encode()).hexdigest()[:16]

    summary = build_lane_summary(lane_id, repo_root)
    if summary.get("error"):
        return {"ok": False, "error": summary["error"], "lane_id": lane_id}

    handoff_id = stable_id("handoff", lane_id, utc_now_iso(), prefix="")[:20]
    paths = [a.path_or_type for a in lane.artifacts if a.path_or_type and a.path_or_type != "simulated"]
    handoff = LaneHandoff(
        handoff_id=handoff_id,
        lane_id=lane_id,
        project_id=lane.project_id,
        goal_id=lane.goal_id,
        status="delivered",
        artifact_paths=paths,
        summary=str(summary),
        delivered_at=utc_now_iso(),
    )
    lane.handoff = handoff
    lane.updated_at = utc_now_iso()
    save_lane(lane, repo_root)
    return {"ok": True, "lane_id": lane_id, "handoff_id": handoff_id, "status": "delivered"}
