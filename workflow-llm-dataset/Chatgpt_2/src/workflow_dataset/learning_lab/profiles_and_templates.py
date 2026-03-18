"""
M41D.1: Learning profiles and safe experiment templates with production-adjacent safety boundaries.
"""

from __future__ import annotations

from workflow_dataset.learning_lab.models import (
    LearningProfile,
    ExperimentTemplate,
    PROFILE_CONSERVATIVE,
    PROFILE_BALANCED,
    PROFILE_RESEARCH_HEAVY,
    TEMPLATE_PROMPT_TUNING,
    TEMPLATE_ROUTING_CHANGES,
    TEMPLATE_QUEUE_TUNING,
    TEMPLATE_TRUST_THRESHOLD_TUNING,
    ENV_LOCAL_ONLY,
    ENV_PRODUCTION_ADJACENT,
)

# ----- Built-in learning profiles -----
LEARNING_PROFILES: list[LearningProfile] = [
    LearningProfile(
        profile_id=PROFILE_CONSERVATIVE,
        label="Conservative",
        description="Minimal local learning: few pending experiments, only approved templates; production-adjacent restricted to trust-threshold and read-only prompt tweaks.",
        max_pending_experiments=3,
        allow_production_adjacent=True,
        allowed_template_ids=[TEMPLATE_PROMPT_TUNING, TEMPLATE_TRUST_THRESHOLD_TUNING],
        production_adjacent_template_ids=[TEMPLATE_TRUST_THRESHOLD_TUNING],
        safety_notes="In production-adjacent: only trust_threshold_tuning with narrow bounds. No routing or queue changes.",
    ),
    LearningProfile(
        profile_id=PROFILE_BALANCED,
        label="Balanced",
        description="Moderate experiments; all templates allowed locally; production-adjacent allows prompt_tuning and trust_threshold_tuning.",
        max_pending_experiments=10,
        allow_production_adjacent=True,
        allowed_template_ids=[TEMPLATE_PROMPT_TUNING, TEMPLATE_ROUTING_CHANGES, TEMPLATE_QUEUE_TUNING, TEMPLATE_TRUST_THRESHOLD_TUNING],
        production_adjacent_template_ids=[TEMPLATE_PROMPT_TUNING, TEMPLATE_TRUST_THRESHOLD_TUNING],
        safety_notes="Routing and queue tuning are local_only. Prompt and trust-threshold changes may run in production-adjacent with review.",
    ),
    LearningProfile(
        profile_id=PROFILE_RESEARCH_HEAVY,
        label="Research-heavy",
        description="More experiments and all templates locally; production-adjacent same as balanced (no routing/queue in prod-adjacent).",
        max_pending_experiments=25,
        allow_production_adjacent=True,
        allowed_template_ids=[TEMPLATE_PROMPT_TUNING, TEMPLATE_ROUTING_CHANGES, TEMPLATE_QUEUE_TUNING, TEMPLATE_TRUST_THRESHOLD_TUNING],
        production_adjacent_template_ids=[TEMPLATE_PROMPT_TUNING, TEMPLATE_TRUST_THRESHOLD_TUNING],
        safety_notes="Local-first; production-adjacent boundaries unchanged from balanced to avoid accidental rollout.",
    ),
]

# ----- Safe experiment templates -----
EXPERIMENT_TEMPLATES: list[ExperimentTemplate] = [
    ExperimentTemplate(
        template_id=TEMPLATE_PROMPT_TUNING,
        label="Prompt tuning",
        description="Adjust system or user prompt text for a subsystem; compare before/after on local slice.",
        experiment_type=TEMPLATE_PROMPT_TUNING,
        allowed_subsystems=["assist_engine", "routing", "specialization"],
        production_adjacent_allowed=True,
        safety_notes="In production-adjacent: small deltas only; require diff review.",
    ),
    ExperimentTemplate(
        template_id=TEMPLATE_ROUTING_CHANGES,
        label="Routing changes",
        description="Change routing rules or model selection; evaluate on local slice before any rollout.",
        experiment_type=TEMPLATE_ROUTING_CHANGES,
        allowed_subsystems=["routing", "mission_control"],
        production_adjacent_allowed=False,
        safety_notes="Local only. Not allowed in production-adjacent environments.",
    ),
    ExperimentTemplate(
        template_id=TEMPLATE_QUEUE_TUNING,
        label="Queue tuning",
        description="Tune retry limits, backoff, or queue ordering; measure impact on local runs.",
        experiment_type=TEMPLATE_QUEUE_TUNING,
        allowed_subsystems=["devlab", "corrections", "ops_jobs"],
        production_adjacent_allowed=False,
        safety_notes="Local only. Production-adjacent queue changes require separate change control.",
    ),
    ExperimentTemplate(
        template_id=TEMPLATE_TRUST_THRESHOLD_TUNING,
        label="Trust threshold tuning",
        description="Adjust confidence or trust thresholds for escalation/auto-apply; validate on local evidence.",
        experiment_type=TEMPLATE_TRUST_THRESHOLD_TUNING,
        allowed_subsystems=["safe_adaptation", "assist_engine", "corrections"],
        production_adjacent_allowed=True,
        safety_notes="In production-adjacent: narrow bounds; require comparison report before promote.",
    ),
]


def get_profiles() -> list[LearningProfile]:
    """Return all built-in learning profiles."""
    return list(LEARNING_PROFILES)


def get_templates() -> list[ExperimentTemplate]:
    """Return all built-in experiment templates."""
    return list(EXPERIMENT_TEMPLATES)


def get_profile(profile_id: str) -> LearningProfile | None:
    """Return profile by id or None."""
    for p in LEARNING_PROFILES:
        if p.profile_id == profile_id:
            return p
    return None


def get_template(template_id: str) -> ExperimentTemplate | None:
    """Return template by id or None."""
    for t in EXPERIMENT_TEMPLATES:
        if t.template_id == template_id:
            return t
    return None


def get_templates_allowed_for_profile(
    profile_id: str,
    production_adjacent: bool = False,
) -> list[str]:
    """
    Return template_ids allowed for this profile in the given environment.
    production_adjacent=True means we are in a production-adjacent environment.
    """
    profile = get_profile(profile_id)
    if not profile:
        return []
    if production_adjacent:
        if not profile.allow_production_adjacent:
            return []
        return list(profile.production_adjacent_template_ids)
    # local_only: use allowed_template_ids; if empty treat as all templates
    allowed = profile.allowed_template_ids
    if not allowed:
        return [t.template_id for t in EXPERIMENT_TEMPLATES]
    return list(allowed)


def is_experiment_allowed_in_environment(
    profile_id: str,
    template_id: str,
    production_adjacent: bool,
) -> bool:
    """
    True if running an experiment with this template is allowed for this profile
    in the given environment (local_only vs production_adjacent).
    """
    allowed = get_templates_allowed_for_profile(profile_id, production_adjacent)
    return template_id in allowed
