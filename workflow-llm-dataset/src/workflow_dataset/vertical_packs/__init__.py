"""
M39E–M39H: Curated vertical workflow packs — opinionated packs, guided value paths, first-value milestones.
"""

from workflow_dataset.vertical_packs.models import (
    CuratedVerticalPack,
    CoreWorkflowPath,
    FirstValuePath,
    FirstValuePathStep,
    TrustReviewPosture,
    RecommendedWorkdayProfile,
    RecommendedQueueProfile,
    RequiredSurfaces,
    SuccessMilestone,
    CommonFailurePoint,
)
from workflow_dataset.vertical_packs.registry import (
    get_curated_pack,
    list_curated_pack_ids,
    get_curated_pack_for_value_pack,
    BUILTIN_CURATED_PACKS,
)
from workflow_dataset.vertical_packs.paths import build_path_for_pack
from workflow_dataset.vertical_packs.defaults import apply_vertical_defaults, get_recommended_commands_for_pack
from workflow_dataset.vertical_packs.store import (
    get_active_pack,
    set_active_pack,
    clear_active_pack,
    get_path_progress,
    set_path_progress,
    set_milestone_reached,
)
from workflow_dataset.vertical_packs.progress import (
    get_next_vertical_milestone,
    get_blocked_vertical_onboarding_step,
    build_milestone_progress_output,
)
from workflow_dataset.vertical_packs.playbooks import (
    get_playbook_for_vertical,
    get_recovery_path_for_failure,
    get_operator_guidance_when_stalled,
    list_vertical_playbook_ids,
    BUILTIN_VERTICAL_PLAYBOOKS,
)

__all__ = [
    "CuratedVerticalPack",
    "CoreWorkflowPath",
    "FirstValuePath",
    "FirstValuePathStep",
    "TrustReviewPosture",
    "RecommendedWorkdayProfile",
    "RecommendedQueueProfile",
    "RequiredSurfaces",
    "SuccessMilestone",
    "CommonFailurePoint",
    "get_curated_pack",
    "list_curated_pack_ids",
    "get_curated_pack_for_value_pack",
    "BUILTIN_CURATED_PACKS",
    "build_path_for_pack",
    "apply_vertical_defaults",
    "get_recommended_commands_for_pack",
    "get_active_pack",
    "set_active_pack",
    "clear_active_pack",
    "get_path_progress",
    "set_path_progress",
    "set_milestone_reached",
    "get_next_vertical_milestone",
    "get_blocked_vertical_onboarding_step",
    "build_milestone_progress_output",
    "get_playbook_for_vertical",
    "get_recovery_path_for_failure",
    "get_operator_guidance_when_stalled",
    "list_vertical_playbook_ids",
    "BUILTIN_VERTICAL_PLAYBOOKS",
]
