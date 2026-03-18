"""
M38A: Built-in cohort profiles — internal_demo, careful_first_user, bounded_operator_pilot, document_heavy_pilot, developer_assist_pilot.
"""

from __future__ import annotations

from workflow_dataset.cohort.models import (
    CohortProfile,
    READINESS_READY_OR_DEGRADED,
    READINESS_ANY,
    READINESS_READY_ONLY,
    SUPPORT_BLOCKED,
    SUPPORT_EXPERIMENTAL,
    SUPPORT_SUPPORTED,
)

# Cohort ids
COHORT_INTERNAL_DEMO = "internal_demo"
COHORT_CAREFUL_FIRST_USER = "careful_first_user"
COHORT_BOUNDED_OPERATOR_PILOT = "bounded_operator_pilot"
COHORT_DOCUMENT_HEAVY_PILOT = "document_heavy_pilot"
COHORT_DEVELOPER_ASSIST_PILOT = "developer_assist_pilot"

# Surface ids (align with default_experience + extended)
_SURFACES = [
    "workspace_home", "day_status", "queue_summary", "approvals_urgent", "continuity_carry_forward",
    "workspace_home_full", "mission_control", "queue_list", "review_studio", "timeline", "automation_inbox", "day_modes",
    "trust_cockpit", "policy_board", "operator_mode", "approvals_policy",
    "automation_run", "background_run", "copilot_plan", "agent_loop",
]


def _surface_support(
    supported: list[str],
    experimental: list[str],
    blocked: list[str] | None = None,
) -> dict[str, str]:
    out = {}
    for s in _SURFACES:
        if s in supported:
            out[s] = SUPPORT_SUPPORTED
        elif s in (experimental or []):
            out[s] = SUPPORT_EXPERIMENTAL
        else:
            out[s] = SUPPORT_BLOCKED
    if blocked:
        for s in blocked:
            out[s] = SUPPORT_BLOCKED
    return out


INTERNAL_DEMO = CohortProfile(
    cohort_id=COHORT_INTERNAL_DEMO,
    label="Internal demo",
    description="Broad scope for internal demos; most surfaces supported.",
    surface_support=_surface_support(
        supported=_SURFACES,
        experimental=[],
    ),
    allowed_trust_tier_ids=["observe_only", "suggest_only", "draft_only", "sandbox_write", "queued_execute", "bounded_trusted_real", "commit_or_send_candidate"],
    allowed_workday_modes=["start", "focus", "review", "operator", "wrap_up", "resume"],
    allowed_automation_scope="both",
    required_readiness=READINESS_ANY,
    default_workday_preset_id="founder_operator",
    default_experience_profile_id="full",
    support_expectations="Full access for demo; no commitment to support all surfaces.",
)

CAREFUL_FIRST_USER = CohortProfile(
    cohort_id=COHORT_CAREFUL_FIRST_USER,
    label="Careful first user",
    description="Narrow scope for first real users; calm home, supported core only; operator and trust expert surfaces blocked.",
    surface_support=_surface_support(
        supported=[
            "workspace_home", "day_status", "queue_summary", "approvals_urgent", "continuity_carry_forward",
            "workspace_home_full", "queue_list", "review_studio", "day_modes",
        ],
        experimental=["mission_control", "timeline", "automation_inbox", "automation_run", "background_run", "copilot_plan", "agent_loop"],
        blocked=["trust_cockpit", "policy_board", "operator_mode", "approvals_policy"],
    ),
    allowed_trust_tier_ids=["observe_only", "suggest_only", "draft_only", "sandbox_write"],
    allowed_workday_modes=["start", "focus", "review", "wrap_up", "resume"],
    allowed_automation_scope="simulate_only",
    required_readiness=READINESS_READY_OR_DEGRADED,
    default_workday_preset_id="analyst",
    default_experience_profile_id="calm_default",
    support_expectations="Supported surfaces are in scope; experimental best-effort; blocked surfaces out of scope.",
)

BOUNDED_OPERATOR_PILOT = CohortProfile(
    cohort_id=COHORT_BOUNDED_OPERATOR_PILOT,
    label="Bounded operator pilot",
    description="Operator mode and trust in scope; approvals and policy supported; automation bounded.",
    surface_support=_surface_support(
        supported=[
            "workspace_home", "day_status", "queue_summary", "approvals_urgent", "continuity_carry_forward",
            "workspace_home_full", "mission_control", "queue_list", "review_studio", "timeline", "automation_inbox", "day_modes",
            "trust_cockpit", "policy_board", "operator_mode", "approvals_policy",
        ],
        experimental=["automation_run", "background_run", "copilot_plan", "agent_loop"],
        blocked=[],
    ),
    allowed_trust_tier_ids=["observe_only", "suggest_only", "draft_only", "sandbox_write", "queued_execute", "bounded_trusted_real"],
    allowed_workday_modes=["start", "focus", "review", "operator", "wrap_up", "resume"],
    allowed_automation_scope="both",
    required_readiness=READINESS_READY_OR_DEGRADED,
    default_workday_preset_id="founder_operator",
    default_experience_profile_id="calm_default",
    support_expectations="Operator and trust in scope; automation experimental.",
)

DOCUMENT_HEAVY_PILOT = CohortProfile(
    cohort_id=COHORT_DOCUMENT_HEAVY_PILOT,
    label="Document-heavy pilot",
    description="Artifacts, review, timeline supported; operator optional.",
    surface_support=_surface_support(
        supported=[
            "workspace_home", "day_status", "queue_summary", "approvals_urgent", "continuity_carry_forward",
            "workspace_home_full", "queue_list", "review_studio", "timeline", "automation_inbox", "day_modes",
            "trust_cockpit", "policy_board", "approvals_policy",
        ],
        experimental=["mission_control", "operator_mode", "automation_run", "background_run", "copilot_plan", "agent_loop"],
        blocked=[],
    ),
    allowed_trust_tier_ids=["observe_only", "suggest_only", "draft_only", "sandbox_write", "queued_execute"],
    allowed_workday_modes=["start", "focus", "review", "operator", "wrap_up", "resume"],
    allowed_automation_scope="simulate_only",
    required_readiness=READINESS_READY_OR_DEGRADED,
    default_workday_preset_id="document_heavy",
    default_experience_profile_id="document_heavy_calm",
    support_expectations="Document and review flows supported; operator experimental.",
)

DEVELOPER_ASSIST_PILOT = CohortProfile(
    cohort_id=COHORT_DEVELOPER_ASSIST_PILOT,
    label="Developer assist pilot",
    description="Lanes, executor, agent loop, operator supported; trust in scope.",
    surface_support=_surface_support(
        supported=[
            "workspace_home", "day_status", "queue_summary", "approvals_urgent", "continuity_carry_forward",
            "workspace_home_full", "mission_control", "queue_list", "review_studio", "timeline", "automation_inbox", "day_modes",
            "trust_cockpit", "policy_board", "operator_mode", "approvals_policy",
            "automation_run", "background_run", "copilot_plan", "agent_loop",
        ],
        experimental=[],
        blocked=[],
    ),
    allowed_trust_tier_ids=["observe_only", "suggest_only", "draft_only", "sandbox_write", "queued_execute", "bounded_trusted_real", "commit_or_send_candidate"],
    allowed_workday_modes=["start", "focus", "review", "operator", "wrap_up", "resume"],
    allowed_automation_scope="both",
    required_readiness=READINESS_READY_OR_DEGRADED,
    default_workday_preset_id="developer",
    default_experience_profile_id="developer_calm",
    support_expectations="Developer and operator surfaces supported.",
)

BUILTIN_COHORT_PROFILES: dict[str, CohortProfile] = {
    COHORT_INTERNAL_DEMO: INTERNAL_DEMO,
    COHORT_CAREFUL_FIRST_USER: CAREFUL_FIRST_USER,
    COHORT_BOUNDED_OPERATOR_PILOT: BOUNDED_OPERATOR_PILOT,
    COHORT_DOCUMENT_HEAVY_PILOT: DOCUMENT_HEAVY_PILOT,
    COHORT_DEVELOPER_ASSIST_PILOT: DEVELOPER_ASSIST_PILOT,
}


def get_cohort_profile(cohort_id: str) -> CohortProfile | None:
    key = (cohort_id or "").strip().lower().replace("-", "_")
    return BUILTIN_COHORT_PROFILES.get(key)


def list_cohort_profile_ids() -> list[str]:
    return list(BUILTIN_COHORT_PROFILES.keys())
