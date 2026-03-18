"""
M42H.1: Candidate templates — evaluator, vertical specialist, routing, calmness.
"""

from __future__ import annotations

from workflow_dataset.candidate_model_studio.models import CandidateTemplate
from workflow_dataset.candidate_model_studio.training_paths import (
    PATH_CRITIQUE_EVALUATOR,
    PATH_VERTICAL_SPECIALIST,
    PATH_ROUTING_ONLY,
    PATH_PROMPT_CONFIG_ONLY,
)
from workflow_dataset.candidate_model_studio.safety_profiles import (
    PROFILE_STRICT_PRODUCTION_ADJACENT,
    PROFILE_EXPERIMENTAL_ONLY,
)

# Template IDs
TEMPLATE_EVALUATOR = "evaluator"
TEMPLATE_VERTICAL_SPECIALIST = "vertical_specialist"
TEMPLATE_ROUTING = "routing"
TEMPLATE_CALMNESS = "calmness"


def get_template(template_id: str) -> CandidateTemplate | None:
    """Return the candidate template by id, or None if unknown."""
    return _REGISTRY.get(template_id)


def list_templates() -> list[CandidateTemplate]:
    """All registered candidate templates."""
    return list(_REGISTRY.values())


def list_template_ids() -> list[str]:
    """All registered template ids."""
    return list(_REGISTRY.keys())


_REGISTRY: dict[str, CandidateTemplate] = {
    TEMPLATE_EVALUATOR: CandidateTemplate(
        template_id=TEMPLATE_EVALUATOR,
        label="Evaluator candidate",
        description="Model or rule set used only to score/critique outputs; not primary response model. Suited to council or review pipeline.",
        default_training_path_id=PATH_CRITIQUE_EVALUATOR,
        default_boundary="experimental",
        suggested_provenance_sources=["council_disagreement", "accepted_adaptations", "production_safe"],
        default_safety_profile_id=PROFILE_STRICT_PRODUCTION_ADJACENT,
    ),
    TEMPLATE_VERTICAL_SPECIALIST: CandidateTemplate(
        template_id=TEMPLATE_VERTICAL_SPECIALIST,
        label="Vertical specialist",
        description="Narrow model or config for one vertical/subsystem. Experimental surface only until promoted.",
        default_training_path_id=PATH_VERTICAL_SPECIALIST,
        default_boundary="experimental",
        suggested_provenance_sources=["vertical_failures", "issue_clusters", "accepted_adaptations"],
        default_safety_profile_id=PROFILE_STRICT_PRODUCTION_ADJACENT,
    ),
    TEMPLATE_ROUTING: CandidateTemplate(
        template_id=TEMPLATE_ROUTING,
        label="Routing candidate",
        description="Router rules or model-selection table: which model handles which surface/workflow. No weight changes.",
        default_training_path_id=PATH_ROUTING_ONLY,
        default_boundary="experimental",
        suggested_provenance_sources=["issue_clusters", "corrections", "production_safe"],
        default_safety_profile_id=PROFILE_STRICT_PRODUCTION_ADJACENT,
    ),
    TEMPLATE_CALMNESS: CandidateTemplate(
        template_id=TEMPLATE_CALMNESS,
        label="Calmness candidate",
        description="Prompt/config only: reduce interruptiveness or adjust tone (calmness, brevity). No weight changes.",
        default_training_path_id=PATH_PROMPT_CONFIG_ONLY,
        default_boundary="experimental",
        suggested_provenance_sources=["corrections", "accepted_adaptations", "production_safe"],
        default_safety_profile_id=PROFILE_EXPERIMENTAL_ONLY,
    ),
}
