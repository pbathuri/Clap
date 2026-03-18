"""
M46A–M46D: Classify alert state from snapshot or from indicators + drift (evidence-backed).
"""

from __future__ import annotations

from workflow_dataset.long_run_health.models import (
    AlertState,
    AlertStateExplanation,
    DeploymentHealthSnapshot,
    DriftSignal,
    SubsystemHealthSignal,
)


def classify_alert_state(
    snapshot: DeploymentHealthSnapshot | None = None,
    drift_signals: list[DriftSignal] | None = None,
    subsystem_signals: list[SubsystemHealthSignal] | None = None,
) -> tuple[AlertState, AlertStateExplanation]:
    """
    Classify overall alert state. Prefer snapshot; else use drift_signals + subsystem_signals.
    Returns (state, explanation) with rationale and evidence_refs.
    """
    if snapshot is not None:
        drift_signals = snapshot.drift_signals
        subsystem_signals = snapshot.subsystem_signals
    drift_signals = drift_signals or []
    subsystem_signals = subsystem_signals or []

    evidence_refs: list[str] = []
    high_severity = sum(1 for d in drift_signals if d.severity == "high")
    medium_severity = sum(1 for d in drift_signals if d.severity == "medium")
    degraded_subsystems = [s for s in subsystem_signals if s.status == "degraded"]
    error_subsystems = [s for s in subsystem_signals if s.status == "error"]
    ok_subsystems = [s for s in subsystem_signals if s.status == "ok"]
    # Contradictory: mixed evidence (e.g. some subsystems ok but high-severity drift)
    contradictory = (high_severity >= 1 or medium_severity >= 2) and len(ok_subsystems) >= 2

    if high_severity > 0:
        evidence_refs.extend([d.drift_id for d in drift_signals if d.severity == "high"])
    if error_subsystems:
        evidence_refs.extend([s.subsystem_id for s in error_subsystems])
    if degraded_subsystems:
        evidence_refs.extend([s.subsystem_id for s in degraded_subsystems][:3])

    # Rollback-consider: eval revert/rollback + high drift
    routing_drift = next((d for d in drift_signals if d.kind == "routing_quality"), None)
    if routing_drift and routing_drift.severity == "high" and high_severity >= 1:
        return (
            AlertState.ROLLBACK_CONSIDER,
            AlertStateExplanation(
                state=AlertState.ROLLBACK_CONSIDER,
                rationale="Eval recommendation revert/rollback with high-severity drift; consider rollback.",
                evidence_refs=evidence_refs[:5],
                confidence="medium",
                contradictory=contradictory,
                short_summary="Eval suggests revert/rollback with high drift; consider rollback.",
            ),
        )

    # Pause-consider: multiple high drift or critical subsystems
    if high_severity >= 2 or len(error_subsystems) >= 1:
        return (
            AlertState.PAUSE_CONSIDER,
            AlertStateExplanation(
                state=AlertState.PAUSE_CONSIDER,
                rationale="Multiple high-severity drifts or subsystem errors; consider pausing expansion.",
                evidence_refs=evidence_refs[:5],
                confidence="medium",
                contradictory=contradictory,
                short_summary="Multiple high-severity drifts or errors; consider pausing expansion.",
            ),
        )

    # Repair-needed: any high or multiple medium drift or degraded subsystems
    if high_severity >= 1 or medium_severity >= 2 or len(degraded_subsystems) >= 2:
        return (
            AlertState.REPAIR_NEEDED,
            AlertStateExplanation(
                state=AlertState.REPAIR_NEEDED,
                rationale="Drift or degraded subsystems indicate repair recommended before continuing.",
                evidence_refs=evidence_refs[:5],
                confidence="medium",
                contradictory=contradictory,
                short_summary="Drift or degraded subsystems; repair recommended before continuing.",
            ),
        )

    # Degraded: any medium drift or any degraded subsystem
    if medium_severity >= 1 or len(degraded_subsystems) >= 1 or len(drift_signals) >= 1:
        return (
            AlertState.DEGRADED,
            AlertStateExplanation(
                state=AlertState.DEGRADED,
                rationale="Some drift or degraded subsystem; monitor and consider repair.",
                evidence_refs=evidence_refs[:5],
                confidence="low" if not drift_signals else "medium",
                contradictory=False,
                short_summary="Drift or a degraded subsystem; monitor and consider repair.",
            ),
        )

    # Watch: warnings only
    warnings = [s for s in subsystem_signals if s.status == "warning"]
    if warnings:
        return (
            AlertState.WATCH,
            AlertStateExplanation(
                state=AlertState.WATCH,
                rationale="Subsystems in warning state; no drift yet. Watch for degradation.",
                evidence_refs=[s.subsystem_id for s in warnings],
                confidence="low",
                contradictory=False,
                short_summary="Subsystems in warning; no drift yet. Watch for degradation.",
            ),
        )

    # Healthy
    return (
        AlertState.HEALTHY,
        AlertStateExplanation(
            state=AlertState.HEALTHY,
            rationale="No drift signals; subsystems ok. Sustained deployment healthy.",
            evidence_refs=[],
            confidence="medium",
            contradictory=False,
            short_summary="All subsystems ok and no drift; deployment is healthy.",
        ),
    )
