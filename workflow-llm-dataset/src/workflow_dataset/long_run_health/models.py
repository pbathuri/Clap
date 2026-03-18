"""
M46A–M46D: Data models for long-run health, drift, degradation, stability window, indicators, alert state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AlertState(str, Enum):
    """Deployment alert state: explainable, evidence-tied."""
    HEALTHY = "healthy"
    WATCH = "watch"
    DEGRADED = "degraded"
    REPAIR_NEEDED = "repair-needed"
    ROLLBACK_CONSIDER = "rollback-consider"
    PAUSE_CONSIDER = "pause-consider"


@dataclass
class StabilityWindow:
    """Time window for health/drift: daily, weekly, rolling N days."""
    kind: str  # daily | weekly | rolling_7 | rolling_30
    start_iso: str = ""
    end_iso: str = ""
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "start_iso": self.start_iso,
            "end_iso": self.end_iso,
            "label": self.label,
        }


@dataclass
class SubsystemHealthSignal:
    """Health signal for one subsystem (e.g. memory_os, queue, execution_loops)."""
    subsystem_id: str
    label: str = ""
    status: str = "unknown"  # ok | warning | degraded | error
    score: float = 0.0  # 0–1, higher = healthier
    summary: str = ""
    evidence_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "subsystem_id": self.subsystem_id,
            "label": self.label,
            "status": self.status,
            "score": self.score,
            "summary": self.summary,
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass
class DriftSignal:
    """A single drift signal: kind, subsystem, severity, evidence."""
    drift_id: str
    kind: str  # execution_loop | intervention_rate | queue_calmness | memory_quality | routing_quality | takeover_frequency | triage_recurrence | value_regression
    subsystem_id: str
    severity: str  # low | medium | high
    summary: str = ""
    baseline_value: float | None = None
    current_value: float | None = None
    window_kind: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    created_at_iso: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "drift_id": self.drift_id,
            "kind": self.kind,
            "subsystem_id": self.subsystem_id,
            "severity": self.severity,
            "summary": self.summary,
            "baseline_value": self.baseline_value,
            "current_value": self.current_value,
            "window_kind": self.window_kind,
            "evidence_refs": list(self.evidence_refs),
            "created_at_iso": self.created_at_iso,
        }


@dataclass
class DegradationTrend:
    """Trend over a window: direction and magnitude."""
    subsystem_id: str
    metric_id: str
    direction: str  # improving | stable | degrading
    magnitude: float = 0.0  # e.g. delta or rate
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "subsystem_id": self.subsystem_id,
            "metric_id": self.metric_id,
            "direction": self.direction,
            "magnitude": self.magnitude,
            "summary": self.summary,
        }


@dataclass
class OperatorBurdenIndicator:
    """Operator burden: review count, takeover count, triage load, summary."""
    review_count: int = 0
    takeover_count: int = 0
    triage_open_count: int = 0
    summary: str = ""
    trend: str = "stable"  # decreasing | stable | increasing

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_count": self.review_count,
            "takeover_count": self.takeover_count,
            "triage_open_count": self.triage_open_count,
            "summary": self.summary,
            "trend": self.trend,
        }


@dataclass
class MemoryQualityIndicator:
    """Memory/retrieval quality: recommendation count, weak cautions, usefulness hint."""
    recommendation_count: int = 0
    weak_caution_count: int = 0
    usefulness_summary: str = ""
    score: float = 0.0  # 0–1

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_count": self.recommendation_count,
            "weak_caution_count": self.weak_caution_count,
            "usefulness_summary": self.usefulness_summary,
            "score": self.score,
        }


@dataclass
class RoutingQualityIndicator:
    """Model/runtime routing quality (from runtime_mesh / eval)."""
    summary: str = ""
    score: float = 0.0
    fallback_used: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "score": self.score,
            "fallback_used": self.fallback_used,
        }


@dataclass
class ExecutionReliabilityIndicator:
    """Execution loop success/failure, shadow confidence, supervisory state."""
    loops_completed: int = 0
    loops_failed_or_stopped: int = 0
    shadow_forced_takeover_count: int = 0
    summary: str = ""
    score: float = 0.0  # 0–1

    def to_dict(self) -> dict[str, Any]:
        return {
            "loops_completed": self.loops_completed,
            "loops_failed_or_stopped": self.loops_failed_or_stopped,
            "shadow_forced_takeover_count": self.shadow_forced_takeover_count,
            "summary": self.summary,
            "score": self.score,
        }


@dataclass
class AlertStateExplanation:
    """Why a given alert state was chosen; evidence-backed. M46D.1: short_summary for operator clarity."""
    state: AlertState
    rationale: str
    evidence_refs: list[str] = field(default_factory=list)
    confidence: str = "medium"  # low | medium | high
    contradictory: bool = False
    short_summary: str = ""  # One-line "why healthy / watch / degraded / repair-needed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "rationale": self.rationale,
            "evidence_refs": list(self.evidence_refs),
            "confidence": self.confidence,
            "contradictory": self.contradictory,
            "short_summary": self.short_summary,
        }


@dataclass
class DeploymentHealthSnapshot:
    """Full deployment health snapshot: window, subsystems, drift, trend, alert."""
    snapshot_id: str
    window: StabilityWindow
    subsystem_signals: list[SubsystemHealthSignal] = field(default_factory=list)
    drift_signals: list[DriftSignal] = field(default_factory=list)
    degradation_trends: list[DegradationTrend] = field(default_factory=list)
    operator_burden: OperatorBurdenIndicator | None = None
    memory_quality: MemoryQualityIndicator | None = None
    routing_quality: RoutingQualityIndicator | None = None
    execution_reliability: ExecutionReliabilityIndicator | None = None
    alert_state: AlertState = AlertState.HEALTHY
    alert_explanation: AlertStateExplanation | None = None
    generated_at_iso: str = ""
    vertical_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "window": self.window.to_dict(),
            "subsystem_signals": [s.to_dict() for s in self.subsystem_signals],
            "drift_signals": [d.to_dict() for d in self.drift_signals],
            "degradation_trends": [t.to_dict() for t in self.degradation_trends],
            "operator_burden": self.operator_burden.to_dict() if self.operator_burden else None,
            "memory_quality": self.memory_quality.to_dict() if self.memory_quality else None,
            "routing_quality": self.routing_quality.to_dict() if self.routing_quality else None,
            "execution_reliability": self.execution_reliability.to_dict() if self.execution_reliability else None,
            "alert_state": self.alert_state.value,
            "alert_explanation": self.alert_explanation.to_dict() if self.alert_explanation else None,
            "generated_at_iso": self.generated_at_iso,
            "vertical_id": self.vertical_id,
        }
