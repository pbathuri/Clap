"""
M38C: Cohort-specific defaults — bind cohort to workday preset, experience profile, trust posture, automation scope, readiness.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.cohort.profiles import get_cohort_profile


def apply_cohort_defaults(cohort_id: str) -> dict[str, Any]:
    """
    Resolve cohort profile and return a config dict of recommended defaults.
    Does not mutate workday/trust/default_experience state; caller may apply.
    """
    profile = get_cohort_profile(cohort_id)
    if not profile:
        return {"cohort_id": cohort_id, "error": "unknown cohort"}
    return {
        "cohort_id": profile.cohort_id,
        "label": profile.label,
        "default_workday_preset_id": profile.default_workday_preset_id,
        "default_experience_profile_id": profile.default_experience_profile_id,
        "allowed_trust_tier_ids": list(profile.allowed_trust_tier_ids),
        "allowed_workday_modes": list(profile.allowed_workday_modes),
        "allowed_automation_scope": profile.allowed_automation_scope,
        "required_readiness": profile.required_readiness,
        "support_expectations": profile.support_expectations,
    }


def get_recommended_workday_preset_id(cohort_id: str) -> str:
    """Recommended workday preset for this cohort."""
    profile = get_cohort_profile(cohort_id)
    return (profile.default_workday_preset_id if profile else "") or ""


def get_recommended_experience_profile_id(cohort_id: str) -> str:
    """Recommended default experience profile for this cohort."""
    profile = get_cohort_profile(cohort_id)
    return (profile.default_experience_profile_id if profile else "") or ""
