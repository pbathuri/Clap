"""
M46A–M46D: Long-run health model + drift detection.
Local-first sustained deployment health, drift signals, degradation trends, alert states.
"""

from workflow_dataset.long_run_health.models import (
    DeploymentHealthSnapshot,
    SubsystemHealthSignal,
    DriftSignal,
    DegradationTrend,
    OperatorBurdenIndicator,
    MemoryQualityIndicator,
    RoutingQualityIndicator,
    ExecutionReliabilityIndicator,
    AlertState,
    AlertStateExplanation,
    StabilityWindow,
)
from workflow_dataset.long_run_health.snapshot import build_deployment_health_snapshot
from workflow_dataset.long_run_health.drift_detection import (
    collect_drift_signals,
    execution_loop_drift,
    intervention_rate_drift,
    queue_calmness_drift,
    memory_quality_drift,
    routing_quality_drift,
    takeover_frequency_drift,
    triage_recurrence_drift,
    value_regression_drift,
)
from workflow_dataset.long_run_health.indicators import (
    operator_burden_from_state,
    memory_quality_from_state,
    routing_quality_from_state,
    execution_reliability_from_state,
    build_subsystem_health_signals,
)
from workflow_dataset.long_run_health.alert_state import classify_alert_state
from workflow_dataset.long_run_health.store import (
    save_snapshot,
    save_drift_signal,
    load_snapshot,
    load_drift_signal,
    list_snapshots,
    list_drift_signals,
    get_health_dir,
)
from workflow_dataset.long_run_health.reports import (
    format_long_run_report,
    format_drift_report,
    format_subsystem_health,
    format_alert_explanation,
)
from workflow_dataset.long_run_health.mission_control import long_run_health_slice
from workflow_dataset.long_run_health.stability_windows import (
    list_stability_windows,
    get_stability_window,
    build_window,
)
from workflow_dataset.long_run_health.threshold_profiles import (
    list_threshold_profiles,
    get_threshold_profile,
    DriftThresholdProfile,
    PROFILE_CONSERVATIVE,
    PROFILE_BALANCED,
    PROFILE_PRODUCTION_STRICT,
)

__all__ = [
    "DeploymentHealthSnapshot",
    "SubsystemHealthSignal",
    "DriftSignal",
    "DegradationTrend",
    "OperatorBurdenIndicator",
    "MemoryQualityIndicator",
    "RoutingQualityIndicator",
    "ExecutionReliabilityIndicator",
    "AlertState",
    "AlertStateExplanation",
    "StabilityWindow",
    "build_deployment_health_snapshot",
    "collect_drift_signals",
    "execution_loop_drift",
    "intervention_rate_drift",
    "queue_calmness_drift",
    "memory_quality_drift",
    "routing_quality_drift",
    "takeover_frequency_drift",
    "triage_recurrence_drift",
    "value_regression_drift",
    "operator_burden_from_state",
    "memory_quality_from_state",
    "routing_quality_from_state",
    "execution_reliability_from_state",
    "build_subsystem_health_signals",
    "classify_alert_state",
    "save_snapshot",
    "save_drift_signal",
    "load_snapshot",
    "load_drift_signal",
    "list_snapshots",
    "list_drift_signals",
    "get_health_dir",
    "format_long_run_report",
    "format_drift_report",
    "format_subsystem_health",
    "format_alert_explanation",
    "long_run_health_slice",
    "list_stability_windows",
    "get_stability_window",
    "build_window",
    "list_threshold_profiles",
    "get_threshold_profile",
    "DriftThresholdProfile",
    "PROFILE_CONSERVATIVE",
    "PROFILE_BALANCED",
    "PROFILE_PRODUCTION_STRICT",
]
