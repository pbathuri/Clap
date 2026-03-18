"""
M36E–M36H: Unified work queue (collect, prioritize, mode views, summary).
M36H.1: Queue bundles by mode, sections by project/episode, overloaded summary.
"""

from workflow_dataset.unified_queue.models import (
    UnifiedQueueItem,
    QueueSection,
    QueueViewMode,
    ModeAwareQueueView,
    QueueSummary,
    SourceSubsystem,
    ActionabilityClass,
    RoutingTarget,
)
from workflow_dataset.unified_queue.collect import build_unified_queue
from workflow_dataset.unified_queue.prioritize import (
    rank_unified_queue,
    build_sections_by_project,
    build_sections_by_episode,
)
from workflow_dataset.unified_queue.views import (
    build_mode_view,
    build_mode_aware_view_bundle,
)
from workflow_dataset.unified_queue.summary import build_queue_summary

__all__ = [
    "UnifiedQueueItem",
    "QueueSection",
    "QueueViewMode",
    "ModeAwareQueueView",
    "QueueSummary",
    "SourceSubsystem",
    "ActionabilityClass",
    "RoutingTarget",
    "build_unified_queue",
    "rank_unified_queue",
    "build_sections_by_project",
    "build_sections_by_episode",
    "build_mode_view",
    "build_mode_aware_view_bundle",
    "build_queue_summary",
]
