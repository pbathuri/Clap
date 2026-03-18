"""
M38D: Cohort explain — why a surface is supported/experimental/blocked for a cohort; what cohort allows.
"""

from __future__ import annotations

from workflow_dataset.cohort.profiles import get_cohort_profile
from workflow_dataset.cohort.surface_matrix import get_support_level, get_matrix
from workflow_dataset.cohort.models import SUPPORT_BLOCKED, SUPPORT_EXPERIMENTAL, SUPPORT_SUPPORTED


def explain_surface(surface_id: str, cohort_id: str) -> dict[str, str]:
    """Explain surface support for this cohort: level, reason, command_hint."""
    profile = get_cohort_profile(cohort_id)
    level = get_support_level(cohort_id, surface_id)
    reason = ""
    if level == SUPPORT_SUPPORTED:
        reason = "In scope for this cohort; supported."
    elif level == SUPPORT_EXPERIMENTAL:
        reason = "In scope but experimental; best-effort, known limitations may apply."
    else:
        reason = "Out of scope for this cohort; use a different cohort profile to allow."
    # Command hint from default_experience if available
    command_hint = ""
    try:
        from workflow_dataset.default_experience.surfaces import get_surface_by_id
        s = get_surface_by_id(surface_id)
        if s:
            command_hint = s.command_hint or ""
    except Exception:
        pass
    return {
        "surface_id": surface_id,
        "cohort_id": cohort_id,
        "support_level": level,
        "reason": reason,
        "command_hint": command_hint,
    }


def explain_cohort(cohort_id: str) -> dict[str, str | list]:
    """Explain what this cohort allows: summary, supported count, experimental count, blocked count, trust posture."""
    profile = get_cohort_profile(cohort_id)
    if not profile:
        return {"cohort_id": cohort_id, "error": "unknown cohort"}
    matrix = get_matrix(cohort_id)
    supported = [s for s, lv in matrix.items() if lv == SUPPORT_SUPPORTED]
    experimental = [s for s, lv in matrix.items() if lv == SUPPORT_EXPERIMENTAL]
    blocked = [s for s, lv in matrix.items() if lv == SUPPORT_BLOCKED]
    return {
        "cohort_id": profile.cohort_id,
        "label": profile.label,
        "description": profile.description,
        "supported_count": len(supported),
        "experimental_count": len(experimental),
        "blocked_count": len(blocked),
        "allowed_trust_tiers": list(profile.allowed_trust_tier_ids),
        "allowed_workday_modes": list(profile.allowed_workday_modes),
        "allowed_automation_scope": profile.allowed_automation_scope,
        "required_readiness": profile.required_readiness,
        "support_expectations": profile.support_expectations,
        "supported_surfaces": supported[:20],
        "blocked_surfaces": blocked[:20],
    }
