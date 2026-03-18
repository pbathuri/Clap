"""
M39A–M39D: Vertical selection and scope lock — evidence-based vertical choice, core/non-core surfaces.
"""

from workflow_dataset.vertical_selection.models import (
    VerticalCandidate,
    SurfacePolicyEntry,
    SURFACE_CLASS_CORE,
    SURFACE_CLASS_ADVANCED_AVAILABLE,
    SURFACE_CLASS_NON_CORE,
    SURFACE_POLICY_RECOMMENDED,
    SURFACE_POLICY_ALLOWED,
    SURFACE_POLICY_DISCOURAGED,
    SURFACE_POLICY_BLOCKED,
    REVEAL_ALWAYS,
    REVEAL_ON_DEMAND,
    REVEAL_AFTER_FIRST_MILESTONE,
    REVEAL_NEVER,
)
from workflow_dataset.vertical_selection.surface_policies import (
    get_surface_policy_level,
    get_surface_policy_entry,
    get_surface_policy_report,
    is_surface_experimental,
    get_advanced_reveal_rule,
)
from workflow_dataset.vertical_selection.candidates import build_candidates, get_candidate
from workflow_dataset.vertical_selection.selection import (
    rank_candidates,
    recommend_primary_secondary,
    explain_vertical,
)
from workflow_dataset.vertical_selection.scope_lock import (
    get_core_surfaces,
    get_optional_surfaces,
    get_excluded_surfaces,
    get_surface_class_for_vertical,
    get_surfaces_hidden_by_scope,
    get_scope_report,
)
from workflow_dataset.vertical_selection.store import (
    get_active_vertical_id,
    set_active_vertical_id,
)

__all__ = [
    "VerticalCandidate",
    "SurfacePolicyEntry",
    "SURFACE_CLASS_CORE",
    "SURFACE_CLASS_ADVANCED_AVAILABLE",
    "SURFACE_CLASS_NON_CORE",
    "SURFACE_POLICY_RECOMMENDED",
    "SURFACE_POLICY_ALLOWED",
    "SURFACE_POLICY_DISCOURAGED",
    "SURFACE_POLICY_BLOCKED",
    "REVEAL_ALWAYS",
    "REVEAL_ON_DEMAND",
    "REVEAL_AFTER_FIRST_MILESTONE",
    "REVEAL_NEVER",
    "get_surface_policy_level",
    "get_surface_policy_entry",
    "get_surface_policy_report",
    "is_surface_experimental",
    "get_advanced_reveal_rule",
    "build_candidates",
    "get_candidate",
    "rank_candidates",
    "recommend_primary_secondary",
    "explain_vertical",
    "get_core_surfaces",
    "get_optional_surfaces",
    "get_excluded_surfaces",
    "get_surface_class_for_vertical",
    "get_surfaces_hidden_by_scope",
    "get_scope_report",
    "get_active_vertical_id",
    "set_active_vertical_id",
]
