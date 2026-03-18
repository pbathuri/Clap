"""
M50E–M50H Phase D: Mission control slice for v1 ops — support posture, overdue maintenance, top v1 risk, recommended action, rollback readiness.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.v1_ops.posture import build_v1_support_posture
from workflow_dataset.v1_ops.maintenance_pack import build_stable_v1_maintenance_pack, _rollback_readiness


def get_v1_ops_state(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Build v1_ops mission-control slice:
    - current_support_posture
    - overdue_maintenance_or_review
    - top_unresolved_v1_risk
    - recommended_stable_v1_support_action
    - rollback_readiness_posture
    """
    root = Path(repo_root).resolve() if repo_root else Path.cwd()
    try:
        from workflow_dataset.path_utils import get_repo_root
        root = Path(get_repo_root()).resolve()
    except Exception:
        pass
    if repo_root is not None:
        root = Path(repo_root).resolve()

    posture = build_v1_support_posture(root)
    pack = build_stable_v1_maintenance_pack(root)
    rollback = _rollback_readiness(root)

    # Overdue: next review due in the past
    overdue = False
    try:
        from datetime import datetime, timezone
        rc = pack.review_cadence_ref
        if rc and rc.next_due_iso:
            try:
                next_dt = datetime.fromisoformat(rc.next_due_iso.replace("Z", "+00:00"))
                if getattr(next_dt, "tzinfo", None) and next_dt < datetime.now(timezone.utc):
                    overdue = True
            except Exception:
                pass
    except Exception:
        pass

    # Top unresolved v1 risk
    top_risk = ""
    try:
        from workflow_dataset.mission_control.state import get_mission_control_state
        state = get_mission_control_state(root)
        repair = state.get("repair_slice") or {}
        if repair.get("top_repair_needed_id"):
            top_risk = "Repair needed: %s" % repair.get("top_repair_needed_id", "")
        elif posture.support_level == "maintenance":
            top_risk = "Support level is maintenance; check supportability and stability decision."
        if not top_risk and state.get("deploy_bundle_state", {}).get("blocked_deployment_risks"):
            top_risk = "Blocked deployment risks: " + "; ".join((state["deploy_bundle_state"]["blocked_deployment_risks"] or [])[:2])
    except Exception:
        if posture.support_level == "maintenance":
            top_risk = "Support level is maintenance."

    # Recommended action
    recommended = "Run: workflow-dataset v1-ops maintenance-pack and stability-reviews latest."
    if posture.support_level == "maintenance":
        recommended = "Check supportability and stability-decision pack; consider repair or rollback."
    if overdue:
        recommended = "Run stability-reviews generate; then v1-ops maintenance-pack."
    if top_risk and "repair" in top_risk.lower():
        recommended = "Run repair-loops list; execute or escalate top repair."

    return {
        "current_support_posture": posture.to_dict(),
        "overdue_maintenance_or_review": overdue,
        "top_unresolved_v1_risk": top_risk,
        "recommended_stable_v1_support_action": recommended,
        "rollback_readiness_posture": rollback.to_dict(),
    }
