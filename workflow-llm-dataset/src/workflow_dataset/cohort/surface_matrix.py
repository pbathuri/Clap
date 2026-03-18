"""
M38B: Supported surface matrix — per-cohort surface_id -> supported | experimental | blocked.
"""

from __future__ import annotations

from workflow_dataset.default_experience.surfaces import get_all_surfaces
from workflow_dataset.cohort.models import SUPPORT_BLOCKED, SUPPORT_EXPERIMENTAL, SUPPORT_SUPPORTED
from workflow_dataset.cohort.profiles import get_cohort_profile


def get_all_surface_ids() -> list[str]:
    """All surface ids (default_experience + extended)."""
    from workflow_dataset.default_experience.surfaces import get_all_surfaces
    ids = [s.surface_id for s in get_all_surfaces()]
    # Extended surfaces not in default_experience
    extra = ["automation_run", "background_run", "copilot_plan", "agent_loop"]
    for e in extra:
        if e not in ids:
            ids.append(e)
    return ids


def get_matrix(cohort_id: str) -> dict[str, str]:
    """Per-cohort matrix: surface_id -> supported | experimental | blocked. Missing surfaces default to blocked."""
    profile = get_cohort_profile(cohort_id)
    all_ids = get_all_surface_ids()
    if not profile:
        return {sid: SUPPORT_BLOCKED for sid in all_ids}
    result = {}
    for sid in all_ids:
        result[sid] = profile.surface_support.get(sid, SUPPORT_BLOCKED)
    return result


def get_support_level(cohort_id: str, surface_id: str) -> str:
    """Return supported | experimental | blocked for this cohort and surface."""
    matrix = get_matrix(cohort_id)
    return matrix.get(surface_id, SUPPORT_BLOCKED)


def get_supported_surfaces(cohort_id: str) -> list[str]:
    """Surface ids that are supported for this cohort."""
    matrix = get_matrix(cohort_id)
    return [sid for sid, level in matrix.items() if level == SUPPORT_SUPPORTED]


def get_experimental_surfaces(cohort_id: str) -> list[str]:
    """Surface ids that are experimental for this cohort."""
    matrix = get_matrix(cohort_id)
    return [sid for sid, level in matrix.items() if level == SUPPORT_EXPERIMENTAL]


def get_blocked_surfaces(cohort_id: str) -> list[str]:
    """Surface ids that are blocked for this cohort."""
    matrix = get_matrix(cohort_id)
    return [sid for sid, level in matrix.items() if level == SUPPORT_BLOCKED]
