"""
M40D.1: Production-default workspace/day/queue profiles for the active cut.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.production_cut.models import ProductionCut, ProductionDefaultProfile
from workflow_dataset.production_cut.store import get_active_cut


def get_production_default_profile(
    cut: ProductionCut | None = None,
    repo_root: Any = None,
) -> ProductionDefaultProfile | None:
    """
    Build production-default profile (workspace/day/queue/experience) for the cut.
    Returns None if no cut or no default_profile on cut.
    """
    if cut is None:
        cut = get_active_cut(repo_root)
    if not cut or not cut.default_profile:
        return None
    dp = cut.default_profile
    # Derive workspace preset from workday when aligned (founder_operator -> founder_operator)
    workspace_preset_id = dp.workday_preset_id or ""
    label = f"Production default for {cut.label or cut.vertical_id}"
    if cut.chosen_vertical and cut.chosen_vertical.label:
        label = f"Production default for {cut.chosen_vertical.label}"
    hint = dp.role_operating_hint or "Use production-cut scope to see included surfaces."
    operator_summary = f"workday={dp.workday_preset_id}  experience={dp.default_experience_profile_id}  operator_mode={dp.operator_mode_usage}"
    return ProductionDefaultProfile(
        label=label,
        vertical_id=cut.vertical_id,
        workspace_preset_id=workspace_preset_id,
        workday_preset_id=dp.workday_preset_id,
        queue_section_order=list(dp.queue_section_order),
        default_experience_profile_id=dp.default_experience_profile_id,
        operator_mode_usage=dp.operator_mode_usage,
        role_operating_hint=dp.role_operating_hint,
        operator_summary=operator_summary,
    )
