"""
Initial Setup Analyzer: long-running, resumable onboarding for the personal work agent.

Supports staged analysis: bootstrap → inventory → parsing → interpretation → graph enrichment → LLM prep → summary.
Local-first; no cloud. Progress and checkpoints are persisted under data/local/setup/.
"""

from workflow_dataset.setup.setup_models import (
    SetupSession,
    ScanJob,
    ArtifactFamily,
    AdapterRun,
    SetupStage,
    SetupProgress,
    ScanScope,
    DiscoveredDomain,
)
from workflow_dataset.setup.setup_manager import SetupManager
from workflow_dataset.setup.setup_summary import build_summary_markdown

__all__ = [
    "SetupSession",
    "ScanJob",
    "ArtifactFamily",
    "AdapterRun",
    "SetupStage",
    "SetupProgress",
    "ScanScope",
    "DiscoveredDomain",
    "SetupManager",
    "build_summary_markdown",
]
