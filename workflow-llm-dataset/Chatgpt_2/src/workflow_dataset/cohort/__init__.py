"""
M38A–M38D: Cohort profiles and supported surface matrix — cohort profile, surface support level, matrix, bindings, explain.
M38D.1: Readiness gates and cohort escalation/downgrade paths.
"""

from workflow_dataset.cohort.models import (
    CohortProfile,
    CohortTransition,
    ReadinessGate,
    READINESS_ANY,
    READINESS_READY_ONLY,
    READINESS_READY_OR_DEGRADED,
    SUPPORT_BLOCKED,
    SUPPORT_EXPERIMENTAL,
    SUPPORT_SUPPORTED,
    TRANSITION_DOWNGRADE,
    TRANSITION_ESCALATION,
)
from workflow_dataset.cohort.profiles import (
    get_cohort_profile,
    list_cohort_profile_ids,
    BUILTIN_COHORT_PROFILES,
    COHORT_INTERNAL_DEMO,
    COHORT_CAREFUL_FIRST_USER,
    COHORT_BOUNDED_OPERATOR_PILOT,
    COHORT_DOCUMENT_HEAVY_PILOT,
    COHORT_DEVELOPER_ASSIST_PILOT,
)
from workflow_dataset.cohort.surface_matrix import (
    get_matrix,
    get_support_level,
    get_supported_surfaces,
    get_experimental_surfaces,
    get_blocked_surfaces,
    get_all_surface_ids,
)
from workflow_dataset.cohort.bindings import (
    apply_cohort_defaults,
    get_recommended_workday_preset_id,
    get_recommended_experience_profile_id,
)
from workflow_dataset.cohort.store import (
    get_active_cohort_id,
    set_active_cohort_id,
)
from workflow_dataset.cohort.explain import (
    explain_surface,
    explain_cohort,
)
from workflow_dataset.cohort.gates import (
    evaluate_gates,
    get_gates_for_cohort,
    BUILTIN_GATES,
)
from workflow_dataset.cohort.transitions import (
    get_transitions_for_cohort,
    get_recommended_transition,
    BUILTIN_TRANSITIONS,
)

__all__ = [
    "CohortProfile",
    "READINESS_ANY",
    "READINESS_READY_ONLY",
    "READINESS_READY_OR_DEGRADED",
    "SUPPORT_BLOCKED",
    "SUPPORT_EXPERIMENTAL",
    "SUPPORT_SUPPORTED",
    "get_cohort_profile",
    "list_cohort_profile_ids",
    "BUILTIN_COHORT_PROFILES",
    "COHORT_INTERNAL_DEMO",
    "COHORT_CAREFUL_FIRST_USER",
    "COHORT_BOUNDED_OPERATOR_PILOT",
    "COHORT_DOCUMENT_HEAVY_PILOT",
    "COHORT_DEVELOPER_ASSIST_PILOT",
    "get_matrix",
    "get_support_level",
    "get_supported_surfaces",
    "get_experimental_surfaces",
    "get_blocked_surfaces",
    "get_all_surface_ids",
    "apply_cohort_defaults",
    "get_recommended_workday_preset_id",
    "get_recommended_experience_profile_id",
    "get_active_cohort_id",
    "set_active_cohort_id",
    "explain_surface",
    "explain_cohort",
    "ReadinessGate",
    "CohortTransition",
    "TRANSITION_DOWNGRADE",
    "TRANSITION_ESCALATION",
    "evaluate_gates",
    "get_gates_for_cohort",
    "BUILTIN_GATES",
    "get_transitions_for_cohort",
    "get_recommended_transition",
    "BUILTIN_TRANSITIONS",
]
