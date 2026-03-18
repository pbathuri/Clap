"""
M51E–M51H: Investor-demo first-run onboarding + bounded memory bootstrap.
"""

from workflow_dataset.demo_onboarding.models import (
    DemoOnboardingSession,
    RolePreset,
    DemoWorkspaceSource,
    MemoryBootstrapPlan,
    OnboardingCompletionState,
    ReadyToAssistState,
    TrustPostureSelection,
    BootstrapConfidence,
    SampleWorkspacePack,
    DemoUserPreset,
)
from workflow_dataset.demo_onboarding.presets import (
    get_role_preset,
    list_role_preset_ids,
    get_default_role_preset,
    DEFAULT_DEMO_PRESET_ID,
    ROLE_PRESETS,
)
from workflow_dataset.demo_onboarding.flow import (
    demo_onboarding_start,
    demo_onboarding_select_role,
    demo_onboarding_apply_user_preset,
    demo_onboarding_bootstrap_memory,
    build_completion_state,
    build_ready_to_assist_state,
    build_demo_sequence,
)
from workflow_dataset.demo_onboarding.workspace_packs import (
    get_workspace_pack,
    list_workspace_pack_ids,
    resolve_workspace_pack_path,
    SAMPLE_WORKSPACE_PACKS,
)
from workflow_dataset.demo_onboarding.user_presets import (
    get_demo_user_preset,
    list_demo_user_preset_ids,
    get_default_demo_user_preset,
    DEMO_USER_PRESETS,
    DEFAULT_DEMO_USER_PRESET_ID,
)
from workflow_dataset.demo_onboarding.staging_guide import (
    build_operator_staging_guide,
    format_staging_guide_text,
)
from workflow_dataset.demo_onboarding.memory_bootstrap import (
    run_bounded_memory_bootstrap,
    default_bundled_sample_path,
)

__all__ = [
    "DemoOnboardingSession",
    "RolePreset",
    "DemoWorkspaceSource",
    "MemoryBootstrapPlan",
    "OnboardingCompletionState",
    "ReadyToAssistState",
    "TrustPostureSelection",
    "BootstrapConfidence",
    "get_role_preset",
    "list_role_preset_ids",
    "get_default_role_preset",
    "DEFAULT_DEMO_PRESET_ID",
    "ROLE_PRESETS",
    "demo_onboarding_start",
    "demo_onboarding_select_role",
    "demo_onboarding_apply_user_preset",
    "demo_onboarding_bootstrap_memory",
    "build_completion_state",
    "build_ready_to_assist_state",
    "build_demo_sequence",
    "run_bounded_memory_bootstrap",
    "default_bundled_sample_path",
    "get_workspace_pack",
    "list_workspace_pack_ids",
    "resolve_workspace_pack_path",
    "SAMPLE_WORKSPACE_PACKS",
    "get_demo_user_preset",
    "list_demo_user_preset_ids",
    "get_default_demo_user_preset",
    "DEMO_USER_PRESETS",
    "DEFAULT_DEMO_USER_PRESET_ID",
    "build_operator_staging_guide",
    "format_staging_guide_text",
]
