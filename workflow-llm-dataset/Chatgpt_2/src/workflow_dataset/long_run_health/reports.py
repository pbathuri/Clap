"""
M46A–M46D: Format long-run health and drift reports for CLI.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.long_run_health.models import (
    DeploymentHealthSnapshot,
    DriftSignal,
    SubsystemHealthSignal,
    AlertStateExplanation,
)


def format_long_run_report(snapshot: DeploymentHealthSnapshot) -> str:
    """Human-readable long-run health report."""
    lines = [
        f"[Long-run health] snapshot={snapshot.snapshot_id}  window={snapshot.window.kind}  generated={snapshot.generated_at_iso[:19]}",
        f"  alert_state={snapshot.alert_state.value}",
    ]
    if snapshot.alert_explanation:
        lines.append(f"  rationale: {snapshot.alert_explanation.rationale[:100]}...")
    lines.append("  [Subsystems]")
    for s in snapshot.subsystem_signals:
        lines.append(f"    {s.subsystem_id}: {s.status} score={s.score:.2f}  {s.summary[:60]}")
    if snapshot.drift_signals:
        lines.append("  [Drift signals]")
        for d in snapshot.drift_signals[:10]:
            lines.append(f"    {d.drift_id} {d.kind}/{d.subsystem_id} {d.severity}: {d.summary[:60]}")
    if snapshot.operator_burden:
        lines.append(f"  [Operator burden] {snapshot.operator_burden.summary}")
    return "\n".join(lines)


def format_drift_report(signals: list[DriftSignal], title: str = "Drift report") -> str:
    """Format a list of drift signals."""
    lines = [f"[{title}] count={len(signals)}"]
    for d in signals:
        lines.append(f"  {d.drift_id}  kind={d.kind}  subsystem={d.subsystem_id}  severity={d.severity}")
        lines.append(f"    {d.summary}")
        if d.baseline_value is not None and d.current_value is not None:
            lines.append(f"    baseline={d.baseline_value} current={d.current_value} window={d.window_kind}")
    return "\n".join(lines) if lines else f"[{title}] no drift signals"


def format_subsystem_health(subsystem_id: str, signals: list[SubsystemHealthSignal]) -> str:
    """Format health for one subsystem (by id)."""
    s = next((x for x in signals if x.subsystem_id == subsystem_id), None)
    if not s:
        return f"[Subsystem {subsystem_id}] not found in snapshot"
    lines = [
        f"[Subsystem] {s.subsystem_id}  label={s.label}  status={s.status}  score={s.score:.2f}",
        f"  summary: {s.summary}",
        "  evidence_refs: " + ", ".join(s.evidence_refs[:5]),
    ]
    return "\n".join(lines)


def format_alert_explanation(explanation: AlertStateExplanation) -> str:
    """Format alert state explanation for operator. M46D.1: include short_summary when present."""
    lines = [
        f"[Alert state] {explanation.state.value}  confidence={explanation.confidence}",
    ]
    if explanation.short_summary:
        lines.append(f"  why: {explanation.short_summary}")
    lines.append(f"  rationale: {explanation.rationale}")
    if explanation.evidence_refs:
        lines.append("  evidence_refs: " + ", ".join(explanation.evidence_refs[:10]))
    if explanation.contradictory:
        lines.append("  (contradictory evidence)")
    return "\n".join(lines)
