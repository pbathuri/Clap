"""
M42H.1: Distillation safety profiles and production-adjacent restrictions for local training paths.
"""

from __future__ import annotations

from workflow_dataset.candidate_model_studio.models import (
    DistillationSafetyProfile,
    ProductionAdjacentRestrictions,
)
from workflow_dataset.candidate_model_studio.training_paths import (
    PATH_PROMPT_CONFIG_ONLY,
    PATH_ROUTING_ONLY,
    PATH_LIGHTWEIGHT_DISTILLATION,
    PATH_CRITIQUE_EVALUATOR,
    PATH_VERTICAL_SPECIALIST,
)

# Profile IDs
PROFILE_STRICT_PRODUCTION_ADJACENT = "strict_production_adjacent"
PROFILE_EXPERIMENTAL_ONLY = "experimental_only"
PROFILE_COUNCIL_GATED = "council_gated"
PROFILE_LAB_RESEARCH = "lab_research"


def get_safety_profile(profile_id: str) -> DistillationSafetyProfile | None:
    """Return the distillation safety profile by id, or None if unknown."""
    return _REGISTRY.get(profile_id)


def list_safety_profiles() -> list[DistillationSafetyProfile]:
    """All registered safety profiles."""
    return list(_REGISTRY.values())


def list_safety_profile_ids() -> list[str]:
    """All registered safety profile ids."""
    return list(_REGISTRY.keys())


def get_production_restrictions(profile_id: str) -> ProductionAdjacentRestrictions | None:
    """Production-adjacent restrictions for a profile, or None if profile unknown."""
    p = get_safety_profile(profile_id)
    return p.production_restrictions if p else None


_REGISTRY: dict[str, DistillationSafetyProfile] = {
    PROFILE_STRICT_PRODUCTION_ADJACENT: DistillationSafetyProfile(
        profile_id=PROFILE_STRICT_PRODUCTION_ADJACENT,
        label="Strict production-adjacent",
        description="Use when candidate may affect production-adjacent surfaces. Council required before supported; no weight changes in production scope.",
        allowed_path_ids=[PATH_PROMPT_CONFIG_ONLY, PATH_ROUTING_ONLY, PATH_CRITIQUE_EVALUATOR, PATH_VERTICAL_SPECIALIST],
        production_restrictions=ProductionAdjacentRestrictions(
            require_council_before_supported=True,
            no_weight_changes_in_production_scope=True,
            max_slice_size=0,
            experimental_only_until_council=True,
            allowed_path_ids=[],
        ),
    ),
    PROFILE_EXPERIMENTAL_ONLY: DistillationSafetyProfile(
        profile_id=PROFILE_EXPERIMENTAL_ONLY,
        label="Experimental only",
        description="Candidate stays in experimental surfaces only. No promotion to supported without switching profile.",
        allowed_path_ids=[PATH_PROMPT_CONFIG_ONLY, PATH_ROUTING_ONLY, PATH_CRITIQUE_EVALUATOR, PATH_VERTICAL_SPECIALIST, PATH_LIGHTWEIGHT_DISTILLATION],
        production_restrictions=ProductionAdjacentRestrictions(
            require_council_before_supported=True,
            no_weight_changes_in_production_scope=True,
            max_slice_size=5000,
            experimental_only_until_council=True,
            allowed_path_ids=[],
        ),
    ),
    PROFILE_COUNCIL_GATED: DistillationSafetyProfile(
        profile_id=PROFILE_COUNCIL_GATED,
        label="Council-gated",
        description="Any promotion or supported-surface use requires council review. Weight changes allowed only on bounded slice with council gate.",
        allowed_path_ids=[PATH_PROMPT_CONFIG_ONLY, PATH_ROUTING_ONLY, PATH_LIGHTWEIGHT_DISTILLATION, PATH_CRITIQUE_EVALUATOR, PATH_VERTICAL_SPECIALIST],
        production_restrictions=ProductionAdjacentRestrictions(
            require_council_before_supported=True,
            no_weight_changes_in_production_scope=True,
            max_slice_size=2000,
            experimental_only_until_council=True,
            allowed_path_ids=[],
        ),
    ),
    PROFILE_LAB_RESEARCH: DistillationSafetyProfile(
        profile_id=PROFILE_LAB_RESEARCH,
        label="Lab / research",
        description="Not for production-adjacent use. Local experiments only; no automatic promotion path.",
        allowed_path_ids=[PATH_PROMPT_CONFIG_ONLY, PATH_ROUTING_ONLY, PATH_LIGHTWEIGHT_DISTILLATION, PATH_CRITIQUE_EVALUATOR, PATH_VERTICAL_SPECIALIST],
        production_restrictions=ProductionAdjacentRestrictions(
            require_council_before_supported=True,
            no_weight_changes_in_production_scope=True,
            max_slice_size=10000,
            experimental_only_until_council=True,
            allowed_path_ids=[],
        ),
    ),
}
