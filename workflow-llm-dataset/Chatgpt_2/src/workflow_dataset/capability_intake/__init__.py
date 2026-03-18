"""
M21: Open-source capability intake — safe source registry, classification, adoption policy.
"""

from __future__ import annotations

from workflow_dataset.capability_intake.source_models import (
    ExternalSourceCandidate,
    SourceRole,
    SourceAdoptionDecision,
)
from workflow_dataset.capability_intake.source_registry import (
    load_source_registry,
    save_source_registry,
    list_sources,
    get_source,
)
from workflow_dataset.capability_intake.source_report import write_source_report

__all__ = [
    "ExternalSourceCandidate",
    "SourceRole",
    "SourceAdoptionDecision",
    "load_source_registry",
    "save_source_registry",
    "list_sources",
    "get_source",
    "write_source_report",
]
