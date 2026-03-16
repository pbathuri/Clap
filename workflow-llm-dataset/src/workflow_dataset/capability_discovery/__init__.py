"""
M23D-F1: Capability discovery and approval registry. Local-only; lightweight scan.
"""

from workflow_dataset.capability_discovery.models import (
    CapabilityProfile,
    AdapterCapability,
    ActionScope,
)
from workflow_dataset.capability_discovery.approval_registry import (
    ApprovalRegistry,
    load_approval_registry,
    save_approval_registry,
    get_registry_path,
)
from workflow_dataset.capability_discovery.discovery import run_scan
from workflow_dataset.capability_discovery.report import format_profile_report

__all__ = [
    "CapabilityProfile",
    "AdapterCapability",
    "ActionScope",
    "ApprovalRegistry",
    "load_approval_registry",
    "save_approval_registry",
    "get_registry_path",
    "run_scan",
    "format_profile_report",
]
