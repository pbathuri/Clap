"""
M46E–M46H: Mission control slice for repair loops — top repair-needed, active, failed, verified, next action.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.repair_loops.store import list_repair_loops


def repair_loops_mission_control_slice(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Build mission-control slice: top repair-needed subsystem, active loop, failed requiring escalation, verified, next recommended."""
    loops = list_repair_loops(limit=30, repo_root=repo_root)
    active = [l for l in loops if l.get("status") in ("proposed", "under_review", "approved", "executing", "verifying")]
    failed = [l for l in loops if l.get("status") == "failed" and not l.get("escalation_reason")]
    escalated = [l for l in loops if l.get("status") == "escalated"]
    verified = [l for l in loops if l.get("status") == "verified"]
    top_repair_needed_subsystem = None
    if failed:
        top_repair_needed_subsystem = failed[0].get("plan_id", "")
    active_repair_loop_id = active[0].get("repair_loop_id") if active else None
    failed_repair_requiring_escalation_id = failed[0].get("repair_loop_id") if failed else None
    verified_successful_repair_id = verified[0].get("repair_loop_id") if verified else None
    if active:
        next_recommended = f"repair-loops show --id {active[0].get('repair_loop_id')}"
        if active[0].get("status") == "approved":
            next_recommended = f"repair-loops execute --id {active[0].get('repair_loop_id')}"
        elif active[0].get("status") in ("executing", "verifying"):
            next_recommended = f"repair-loops verify --id {active[0].get('repair_loop_id')}"
    elif failed:
        next_recommended = f"repair-loops escalate --id {failed[0].get('repair_loop_id')} or repair-loops rollback --id {failed[0].get('repair_loop_id')}"
    else:
        next_recommended = "repair-loops propose --from <drift_id|run_id>"
    return {
        "top_repair_needed_subsystem": top_repair_needed_subsystem,
        "active_repair_loop_id": active_repair_loop_id,
        "active_repair_loop_count": len(active),
        "failed_repair_requiring_escalation_id": failed_repair_requiring_escalation_id,
        "failed_repair_count": len(failed),
        "escalated_repair_count": len(escalated),
        "verified_successful_repair_id": verified_successful_repair_id,
        "verified_repair_count": len(verified),
        "next_recommended_maintenance_action": next_recommended,
    }
