"""
M46A–M46D: Build deployment health snapshot from state, drift detection, alert classification.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.long_run_health.models import (
    DeploymentHealthSnapshot,
    DegradationTrend,
)
from workflow_dataset.long_run_health.indicators import build_subsystem_health_signals
from workflow_dataset.long_run_health.drift_detection import collect_drift_signals
from workflow_dataset.long_run_health.alert_state import classify_alert_state
from workflow_dataset.long_run_health.stability_windows import build_window
from workflow_dataset.long_run_health.threshold_profiles import get_threshold_profile
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _get_state(repo_root: Path) -> dict[str, Any]:
    """Load mission_control state (read-only)."""
    try:
        from workflow_dataset.mission_control.state import get_mission_control_state
        return get_mission_control_state(repo_root=repo_root)
    except Exception:
        return {}


def build_deployment_health_snapshot(
    window_kind: str = "rolling_7",
    repo_root: Path | str | None = None,
    vertical_id: str = "",
    threshold_profile_id: str = "balanced",
) -> DeploymentHealthSnapshot:
    """
    Build a full deployment health snapshot: indicators, drift signals, alert state.
    Read-only from mission_control and stores.
    """
    root = _repo_root(repo_root)
    state = _get_state(root)
    window = build_window(window_kind or "rolling_7")
    snapshot_id = stable_id("snapshot", window.kind, utc_now_iso()[:16], prefix="health_")

    profile = get_threshold_profile(threshold_profile_id or "balanced")
    subsystem_signals = build_subsystem_health_signals(state)
    drift_signals = collect_drift_signals(
        state, window_kind=window.kind, repo_root=root, threshold_profile=profile
    )

    from workflow_dataset.long_run_health.indicators import (
        operator_burden_from_state,
        memory_quality_from_state,
        routing_quality_from_state,
        execution_reliability_from_state,
    )
    operator_burden = operator_burden_from_state(state)
    memory_quality = memory_quality_from_state(state)
    routing_quality = routing_quality_from_state(state)
    execution_reliability = execution_reliability_from_state(state)

    # Degradation trends: simple pass from low subsystem scores
    degradation_trends: list[DegradationTrend] = []
    for s in subsystem_signals:
        if s.status == "degraded" and s.score < 0.5:
            degradation_trends.append(DegradationTrend(
                subsystem_id=s.subsystem_id,
                metric_id="score",
                direction="degrading",
                magnitude=0.5 - s.score,
                summary=s.summary,
            ))

    alert_state, alert_explanation = classify_alert_state(
        drift_signals=drift_signals,
        subsystem_signals=subsystem_signals,
    )

    return DeploymentHealthSnapshot(
        snapshot_id=snapshot_id,
        window=window,
        subsystem_signals=subsystem_signals,
        drift_signals=drift_signals,
        degradation_trends=degradation_trends,
        operator_burden=operator_burden,
        memory_quality=memory_quality,
        routing_quality=routing_quality,
        execution_reliability=execution_reliability,
        alert_state=alert_state,
        alert_explanation=alert_explanation,
        generated_at_iso=utc_now_iso(),
        vertical_id=vertical_id or "default",
    )
