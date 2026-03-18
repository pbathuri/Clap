"""
M31I–M31L: Personal adaptation loop — preference/style candidates, evidence, review, apply.
Explicit and inspectable; no silent mutation.
"""

from workflow_dataset.personal_adaptation.models import (
    PreferenceCandidate,
    StylePatternCandidate,
    AcceptedPreferenceUpdate,
    BehaviorDelta,
    PersonalProfilePreset,
    REVIEW_STATUS_PENDING,
    REVIEW_STATUS_ACCEPTED,
    REVIEW_STATUS_DISMISSED,
    AFFECTED_SURFACES,
)
from workflow_dataset.personal_adaptation.candidates import (
    generate_preference_candidates,
    generate_style_candidates,
)
from workflow_dataset.personal_adaptation.store import (
    save_candidate,
    list_candidates,
    accept_candidate,
    list_accepted,
    get_candidate,
    get_adaptation_dir,
    get_presets_dir,
)
from workflow_dataset.personal_adaptation.apply import apply_accepted_preference
from workflow_dataset.personal_adaptation.explain import explain_preference
from workflow_dataset.personal_adaptation.behavior_delta import (
    build_behavior_delta_for_candidate,
    build_behavior_delta_for_preset,
    format_behavior_delta_output,
)
from workflow_dataset.personal_adaptation.presets import (
    save_preset,
    load_preset,
    list_presets,
    create_preset,
)

__all__ = [
    "PreferenceCandidate",
    "StylePatternCandidate",
    "AcceptedPreferenceUpdate",
    "REVIEW_STATUS_PENDING",
    "REVIEW_STATUS_ACCEPTED",
    "REVIEW_STATUS_DISMISSED",
    "AFFECTED_SURFACES",
    "generate_preference_candidates",
    "generate_style_candidates",
    "save_candidate",
    "list_candidates",
    "accept_candidate",
    "list_accepted",
    "get_candidate",
    "get_adaptation_dir",
    "get_presets_dir",
    "apply_accepted_preference",
    "explain_preference",
    "BehaviorDelta",
    "PersonalProfilePreset",
    "build_behavior_delta_for_candidate",
    "build_behavior_delta_for_preset",
    "format_behavior_delta_output",
    "save_preset",
    "load_preset",
    "list_presets",
    "create_preset",
]
