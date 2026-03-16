"""
M23M: Explicit learning rules. Which correction categories can propose which updates; blocked targets.
"""

from __future__ import annotations

# Categories that may drive a proposed update (one correction can be enough for low-risk)
ELIGIBLE_CATEGORIES_TO_TARGET: dict[str, list[str]] = {
    "bad_job_parameter_default": ["specialization_params"],
    "bad_path_app_preference": ["specialization_paths"],
    "output_style_correction": ["specialization_output_style"],
    "trust_notes_correction": ["job_pack_trust_notes"],
    "routine_ordering_correction": ["routine_ordering"],
    "context_trigger_false_positive": ["trigger_suppression"],
    "context_trigger_false_negative": ["trigger_suppression"],
}

# Targets that must NEVER be updated from corrections (no privilege escalation)
BLOCKED_TARGETS = (
    "trust_level",           # no simulate_only -> trusted_for_real
    "approval_registry",     # no adding approved_paths / approved_action_scopes
    "real_mode_eligibility",  # no turning on real without job pack + approval flow
)

LEARNING_RULES = {
    "specialization_params": {
        "categories": ["bad_job_parameter_default"],
        "evidence_required": "corrected_value must be dict of param key -> value",
        "auto_eligible": True,
        "risk": "low",
    },
    "specialization_paths": {
        "categories": ["bad_path_app_preference"],
        "evidence_required": "corrected_value can be list of paths or single path",
        "auto_eligible": True,
        "risk": "low",
    },
    "specialization_output_style": {
        "categories": ["output_style_correction"],
        "evidence_required": "corrected_value string",
        "auto_eligible": True,
        "risk": "low",
    },
    "job_pack_trust_notes": {
        "categories": ["trust_notes_correction", "trust_level_too_high", "trust_level_too_low"],
        "evidence_required": "advisory note only; does not change trust_level",
        "auto_eligible": True,
        "risk": "low",
    },
    "routine_ordering": {
        "categories": ["routine_ordering_correction"],
        "evidence_required": "corrected_value list of job_pack_ids in order",
        "auto_eligible": False,
        "risk": "medium",
    },
    "trigger_suppression": {
        "categories": ["context_trigger_false_positive", "context_trigger_false_negative"],
        "evidence_required": "source_reference_id (job or routine), trigger_type in notes or corrected_value",
        "auto_eligible": True,
        "risk": "low",
    },
}


def get_targets_for_category(category: str) -> list[str]:
    """Return list of update targets this category can propose."""
    return list(ELIGIBLE_CATEGORIES_TO_TARGET.get(category, []))
