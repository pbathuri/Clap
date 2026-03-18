"""
M29: Unified workspace shell + navigation state. Local-first; read-only aggregation.
"""

from workflow_dataset.workspace.models import (
    WORKSPACE_AREAS,
    WORKSPACE_VIEWS,
    WorkspaceArea,
    ActiveWorkContext,
    NavigationState,
    WorkspacePreset,
    WorkspaceHomeSnapshot,
)
from workflow_dataset.workspace.presets import (
    get_preset,
    list_preset_ids,
    WORKSPACE_PRESETS,
)
from workflow_dataset.workspace.state import (
    build_active_work_context,
    build_workspace_areas,
    build_navigation_state,
    build_workspace_home_snapshot,
)
from workflow_dataset.workspace.home import build_unified_home, format_workspace_home
from workflow_dataset.workspace.navigation import resolve_view_target, deep_link_commands

__all__ = [
    "WORKSPACE_AREAS",
    "WORKSPACE_VIEWS",
    "WorkspaceArea",
    "ActiveWorkContext",
    "NavigationState",
    "WorkspacePreset",
    "WorkspaceHomeSnapshot",
    "get_preset",
    "list_preset_ids",
    "WORKSPACE_PRESETS",
    "build_active_work_context",
    "build_workspace_areas",
    "build_navigation_state",
    "build_workspace_home_snapshot",
    "build_unified_home",
    "format_workspace_home",
    "resolve_view_target",
    "deep_link_commands",
]
