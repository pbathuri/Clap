"""
M47A–M47D + M47D.1: Vertical excellence — first-value compression, path tightening, recommend-next, role-tuned entry, on-ramps.
"""

from workflow_dataset.vertical_excellence.models import (
    AmbiguityPoint,
    CriticalUserJourney,
    ExcellenceTarget,
    FrictionPoint,
    FirstValuePathStage,
    MissingNextStepSignal,
    OnRampPreset,
    RepeatValuePathStage,
    RoleTunedEntryPath,
)
from workflow_dataset.vertical_excellence.path_resolver import (
    build_first_value_path_for_vertical,
    build_repeat_value_path_for_vertical,
    get_chosen_vertical_id,
)
from workflow_dataset.vertical_excellence.compression import (
    assess_first_value_stage,
    list_ambiguity_points,
    list_blocked_first_value_cases,
    list_friction_points,
)
from workflow_dataset.vertical_excellence.recommend_next import recommend_next_for_vertical
from workflow_dataset.vertical_excellence.mission_control import vertical_excellence_slice
from workflow_dataset.vertical_excellence.role_entry_paths import (
    get_role_tuned_entry_path,
    get_role_tuned_entry_path_for_chosen_vertical,
)
from workflow_dataset.vertical_excellence.on_ramp_presets import (
    list_on_ramp_presets,
    get_on_ramp_preset,
    build_path_with_preset,
)

__all__ = [
    "AmbiguityPoint",
    "CriticalUserJourney",
    "ExcellenceTarget",
    "FrictionPoint",
    "FirstValuePathStage",
    "MissingNextStepSignal",
    "OnRampPreset",
    "RepeatValuePathStage",
    "RoleTunedEntryPath",
    "assess_first_value_stage",
    "build_first_value_path_for_vertical",
    "build_path_with_preset",
    "build_repeat_value_path_for_vertical",
    "get_chosen_vertical_id",
    "get_on_ramp_preset",
    "get_role_tuned_entry_path",
    "get_role_tuned_entry_path_for_chosen_vertical",
    "list_ambiguity_points",
    "list_blocked_first_value_cases",
    "list_friction_points",
    "list_on_ramp_presets",
    "recommend_next_for_vertical",
    "vertical_excellence_slice",
]
