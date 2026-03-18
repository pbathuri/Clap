"""
M24A: External capability activation planner — what is available, safe to activate, recommended;
blocked/rejected; pull/install/enable plans (plans only, no auto-download). Local-first, explicit, approval-aware.
"""

from workflow_dataset.external_capability.schema import ExternalCapabilitySource
from workflow_dataset.external_capability.registry import (
    load_external_sources,
    list_external_sources,
    get_external_source,
)
from workflow_dataset.external_capability.planner import (
    ActivationPlanner,
    plan_activations,
)
from workflow_dataset.external_capability.plans import build_activation_plan
from workflow_dataset.external_capability.compatibility import (
    build_compatibility_matrix,
    recommend_capabilities_for_pack,
    CompatibilityRow,
    CapabilityRecommendationResult,
    CapabilityRecommendationEntry,
)

__all__ = [
    "ExternalCapabilitySource",
    "load_external_sources",
    "list_external_sources",
    "get_external_source",
    "ActivationPlanner",
    "plan_activations",
    "build_activation_plan",
    "build_compatibility_matrix",
    "recommend_capabilities_for_pack",
    "CompatibilityRow",
    "CapabilityRecommendationResult",
    "CapabilityRecommendationEntry",
]
