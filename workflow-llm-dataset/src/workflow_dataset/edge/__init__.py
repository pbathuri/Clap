"""
M23B: Edge / Hardware Readiness Layer. Local deployment profile, readiness checks, workflow matrix.
No cloud; no hardware device specs; inspectable outputs only.
"""

from workflow_dataset.edge.profile import build_edge_profile
from workflow_dataset.edge.checks import run_readiness_checks
from workflow_dataset.edge.report import (
    generate_edge_readiness_report,
    generate_missing_dependency_report,
    generate_workflow_matrix_report,
    generate_package_report,
)

__all__ = [
    "build_edge_profile",
    "generate_edge_readiness_report",
    "generate_missing_dependency_report",
    "generate_workflow_matrix_report",
    "generate_package_report",
    "run_readiness_checks",
]
