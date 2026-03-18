"""
M23B: Edge / Hardware Readiness Layer. Local deployment profile, readiness checks, workflow matrix.
No cloud; no hardware device specs; inspectable outputs only.
"""

from workflow_dataset.edge.profile import build_edge_profile
from workflow_dataset.edge.checks import run_readiness_checks
from workflow_dataset.edge.history import (
    record_readiness_snapshot,
    list_readiness_snapshots,
    load_latest_snapshot,
    load_previous_snapshot,
    snapshot_from_checks,
)
from workflow_dataset.edge.drift import compute_drift, generate_drift_report
from workflow_dataset.edge.report import (
    generate_edge_readiness_report,
    generate_missing_dependency_report,
    generate_workflow_matrix_report,
    generate_package_report,
    generate_tier_matrix_report,
    generate_compare_report,
    generate_degraded_report,
    generate_smoke_check_report,
    compare_tiers,
)
from workflow_dataset.edge.smoke import run_smoke_check

__all__ = [
    "build_edge_profile",
    "record_readiness_snapshot",
    "list_readiness_snapshots",
    "load_latest_snapshot",
    "load_previous_snapshot",
    "snapshot_from_checks",
    "compute_drift",
    "generate_drift_report",
    "generate_edge_readiness_report",
    "generate_missing_dependency_report",
    "generate_workflow_matrix_report",
    "generate_package_report",
    "generate_tier_matrix_report",
    "generate_compare_report",
    "generate_degraded_report",
    "generate_smoke_check_report",
    "compare_tiers",
    "run_readiness_checks",
    "run_smoke_check",
]
