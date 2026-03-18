"""
M42E–M42H Phase C: Candidate training/distillation path types — allowed scope,
compute assumptions, risks, required evaluation before promotion.
"""

from __future__ import annotations

from workflow_dataset.candidate_model_studio.models import TrainingDistillationPath

# Path type IDs
PATH_PROMPT_CONFIG_ONLY = "prompt_config_only"
PATH_ROUTING_ONLY = "routing_only"
PATH_LIGHTWEIGHT_DISTILLATION = "lightweight_distillation"
PATH_CRITIQUE_EVALUATOR = "critique_evaluator"
PATH_VERTICAL_SPECIALIST = "vertical_specialist"

# Safety profile IDs (for default_safety_profile_id on paths)
_PROFILE_STRICT = "strict_production_adjacent"
_PROFILE_EXPERIMENTAL = "experimental_only"
_PROFILE_COUNCIL = "council_gated"
_PROFILE_LAB = "lab_research"


def get_path_descriptor(path_id: str) -> TrainingDistillationPath | None:
    """Return the descriptor for a path type, or None if unknown."""
    return _REGISTRY.get(path_id)


def list_path_ids() -> list[str]:
    """All registered path type ids."""
    return list(_REGISTRY.keys())


_REGISTRY: dict[str, TrainingDistillationPath] = {
    PATH_PROMPT_CONFIG_ONLY: TrainingDistillationPath(
        path_id=PATH_PROMPT_CONFIG_ONLY,
        label="Prompt / config only",
        allowed_scope="Prompt text, system config, or inference params only. No weight changes.",
        compute_assumptions="Local; no GPU required. Edit config/prompt and re-run eval.",
        risks=[
            "Prompt injection sensitivity",
            "Drift if prompts change without review",
        ],
        required_evaluation_before_promotion=[
            "Eval run on supported workflows",
            "Regression check vs baseline",
        ],
        default_safety_profile_id=_PROFILE_STRICT,
        production_restrictions_summary="No weight changes. Council required before supported-surface use. Prompt/config only in production scope.",
    ),
    PATH_ROUTING_ONLY: TrainingDistillationPath(
        path_id=PATH_ROUTING_ONLY,
        label="Routing only",
        allowed_scope="Router rules or model-selection table only. Which model handles which surface/workflow.",
        compute_assumptions="Local; config/routing table. No training step.",
        risks=[
            "Wrong route for edge cases",
            "Latency or cost if routing is misconfigured",
        ],
        required_evaluation_before_promotion=[
            "Routing coverage check",
            "Eval on at least one workflow per routed surface",
        ],
        default_safety_profile_id=_PROFILE_STRICT,
        production_restrictions_summary="No weight changes. Council required before supported. Routing table only; no model training in production scope.",
    ),
    PATH_LIGHTWEIGHT_DISTILLATION: TrainingDistillationPath(
        path_id=PATH_LIGHTWEIGHT_DISTILLATION,
        label="Lightweight distillation / tuning",
        allowed_scope="Bounded fine-tuning or distillation on a curated slice. Single small model or adapter.",
        compute_assumptions="Local GPU or single-node; dataset slice bounded by provenance. No full retrain.",
        risks=[
            "Overfit to slice",
            "Regressions on out-of-slice workflows",
        ],
        required_evaluation_before_promotion=[
            "Eval on slice holdout",
            "Eval on supported workflows (regression)",
            "Council review recommended for supported-surface promotion",
        ],
        default_safety_profile_id=_PROFILE_COUNCIL,
        production_restrictions_summary="Weight changes only on bounded slice. Council required before any supported-surface use. No full retrain in production scope.",
    ),
    PATH_CRITIQUE_EVALUATOR: TrainingDistillationPath(
        path_id=PATH_CRITIQUE_EVALUATOR,
        label="Critique / evaluator candidate",
        allowed_scope="Model or rule set used only to score/critique outputs. Not primary response model.",
        compute_assumptions="Local; can be prompt-based or small classifier. Used in council or review pipeline.",
        risks=[
            "Evaluator bias",
            "False positives/negatives on edge cases",
        ],
        required_evaluation_before_promotion=[
            "Calibration vs human judgments on sample",
            "Agreement with existing council perspectives on held-out set",
        ],
        default_safety_profile_id=_PROFILE_STRICT,
        production_restrictions_summary="Evaluator only; not primary model. Council required before use on supported surfaces. No weight changes in production scope.",
    ),
    PATH_VERTICAL_SPECIALIST: TrainingDistillationPath(
        path_id=PATH_VERTICAL_SPECIALIST,
        label="Vertical-specific specialist",
        allowed_scope="Narrow model or config for one vertical/subsystem. Experimental surface only until promoted.",
        compute_assumptions="Local or single-node; data from vertical slice only.",
        risks=[
            "Narrow coverage",
            "Conflict with general model if both active",
        ],
        required_evaluation_before_promotion=[
            "Eval within vertical",
            "No regression on other verticals",
            "Council review for any supported-surface use",
        ],
        default_safety_profile_id=_PROFILE_STRICT,
        production_restrictions_summary="Experimental-only until council. No supported-surface use without council. Vertical slice only.",
    ),
}
