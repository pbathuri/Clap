"""
M24: Pack categories and priority for multi-pack resolution.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class PackCategory(str, Enum):
    """Category of pack for resolution priority."""

    PRIMARY_ROLE = "primary_role"
    SECONDARY_WORKFLOW = "secondary_workflow"
    TEMPORARY_TASK = "temporary_task"
    SUPPORT = "support"
    EXPERIMENTAL = "experimental"


# Priority order: higher number = higher priority for precedence
CATEGORY_PRIORITY: dict[PackCategory, int] = {
    PackCategory.PRIMARY_ROLE: 100,
    PackCategory.TEMPORARY_TASK: 90,  # pinned task/session
    PackCategory.SECONDARY_WORKFLOW: 50,
    PackCategory.SUPPORT: 30,
    PackCategory.EXPERIMENTAL: 10,
}


def get_priority_for_category(category: PackCategory) -> int:
    """Return numeric priority for precedence (higher wins)."""
    return CATEGORY_PRIORITY.get(category, 0)


def infer_category_from_manifest(manifest: Any) -> PackCategory:
    """
    Infer category from manifest. Default: SECONDARY_WORKFLOW.
    PRIMARY_ROLE is set by activation state, not manifest.
    """
    tags = getattr(manifest, "role_tags", None) or []
    if not tags:
        return PackCategory.SUPPORT
    # Experimental if manifest has a flag (future)
    if getattr(manifest, "experimental", False):
        return PackCategory.EXPERIMENTAL
    return PackCategory.SECONDARY_WORKFLOW
