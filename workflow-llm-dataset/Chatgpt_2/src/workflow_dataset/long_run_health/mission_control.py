"""
M46A–M46D: Mission-control slice — current deployment health, strongest drift, top degraded, operator burden trend, next maintenance.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.long_run_health.snapshot import build_deployment_health_snapshot
from workflow_dataset.long_run_health.models import AlertState


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def long_run_health_slice(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Mission-control visibility: current deployment health, strongest drift signal id,
    top degraded subsystem id, operator burden trend summary, next recommended maintenance.
    Does not persist snapshot; builds in-memory.
    """
    root = _repo_root(repo_root)
    try:
        snapshot = build_deployment_health_snapshot(window_kind="rolling_7", repo_root=root)
    except Exception as e:
        return {"error": str(e)}

    strongest_drift_id = ""
    if snapshot.drift_signals:
        by_severity = {"high": 3, "medium": 2, "low": 1}
        top = max(snapshot.drift_signals, key=lambda d: by_severity.get(d.severity, 0))
        strongest_drift_id = top.drift_id

    top_degraded_id = ""
    degraded = [s for s in snapshot.subsystem_signals if s.status in ("degraded", "error")]
    if degraded:
        worst = min(degraded, key=lambda s: s.score)
        top_degraded_id = worst.subsystem_id

    operator_burden_trend = ""
    if snapshot.operator_burden:
        operator_burden_trend = snapshot.operator_burden.summary + " trend=" + snapshot.operator_burden.trend

    next_maintenance = "none"
    if snapshot.alert_state == AlertState.REPAIR_NEEDED:
        next_maintenance = "repair"
    elif snapshot.alert_state == AlertState.DEGRADED:
        next_maintenance = "review_and_consider_repair"
    elif snapshot.alert_state == AlertState.WATCH:
        next_maintenance = "watch"
    elif snapshot.alert_state in (AlertState.ROLLBACK_CONSIDER, AlertState.PAUSE_CONSIDER):
        next_maintenance = "review_rollback_or_pause"
    elif strongest_drift_id:
        next_maintenance = "review_drift_report"

    return {
        "current_alert_state": snapshot.alert_state.value,
        "strongest_drift_signal_id": strongest_drift_id,
        "top_degraded_subsystem_id": top_degraded_id,
        "operator_burden_trend_summary": operator_burden_trend,
        "next_recommended_maintenance": next_maintenance,
        "snapshot_id": snapshot.snapshot_id,
        "drift_signal_count": len(snapshot.drift_signals),
        "degraded_subsystem_count": len(degraded),
    }
