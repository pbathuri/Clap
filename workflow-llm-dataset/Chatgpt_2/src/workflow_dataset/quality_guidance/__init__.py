"""
M47I–M47L: Quality signals + delightful operator guidance — sharper guidance, clarity, confidence, ready-to-act.
"""

from workflow_dataset.quality_guidance.models import (
    QualitySignal,
    ClarityScore,
    ConfidenceWithEvidence,
    AmbiguityWarning,
    ReadyToActSignal,
    NeedsReviewSignal,
    StrongNextStepSignal,
    WeakGuidanceWarning,
    GuidanceItem,
    GuidanceKind,
    GuidancePreset,
    GuidancePresetKind,
    RecoveryGuidancePack,
    OperatorFacingSummary,
)
from workflow_dataset.quality_guidance.guidance import (
    next_best_action_guidance,
    review_needed_guidance,
    blocked_state_guidance,
    resume_guidance,
    operator_routine_guidance,
    support_recovery_guidance,
)
from workflow_dataset.quality_guidance.signals import build_quality_signals
from workflow_dataset.quality_guidance.surfaces import (
    ready_now_states,
    not_safe_yet_states,
    ambiguity_report,
    weak_guidance_report,
)
from workflow_dataset.quality_guidance.presets import (
    load_active_preset,
    save_active_preset,
    apply_preset_to_guidance,
    get_default_presets,
    get_preset_for,
)
from workflow_dataset.quality_guidance.recovery_packs import (
    get_default_recovery_packs,
    get_recovery_pack_for_failure_pattern,
    get_recovery_pack_for_vertical,
)
from workflow_dataset.quality_guidance.operator_summary import build_operator_summary

__all__ = [
    "QualitySignal",
    "ClarityScore",
    "ConfidenceWithEvidence",
    "AmbiguityWarning",
    "ReadyToActSignal",
    "NeedsReviewSignal",
    "StrongNextStepSignal",
    "WeakGuidanceWarning",
    "GuidanceItem",
    "next_best_action_guidance",
    "review_needed_guidance",
    "blocked_state_guidance",
    "resume_guidance",
    "operator_routine_guidance",
    "support_recovery_guidance",
    "build_quality_signals",
    "ready_now_states",
    "not_safe_yet_states",
    "ambiguity_report",
    "weak_guidance_report",
    "GuidanceKind",
    "GuidancePreset",
    "GuidancePresetKind",
    "RecoveryGuidancePack",
    "OperatorFacingSummary",
    "load_active_preset",
    "save_active_preset",
    "apply_preset_to_guidance",
    "get_default_presets",
    "get_preset_for",
    "get_default_recovery_packs",
    "get_recovery_pack_for_failure_pattern",
    "get_recovery_pack_for_vertical",
    "build_operator_summary",
]
