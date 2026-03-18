"""
M22D: Local Knowledge Intake Center. User-owned inputs snapshotted into sandbox; no cloud; operator-controlled.
"""

from workflow_dataset.intake.registry import (
    INTAKE_ROOT,
    add_intake,
    get_intake,
    list_intakes,
)
from workflow_dataset.intake.load import load_intake_content
from workflow_dataset.intake.report import intake_report

__all__ = [
    "INTAKE_ROOT",
    "add_intake",
    "get_intake",
    "list_intakes",
    "load_intake_content",
    "intake_report",
]
