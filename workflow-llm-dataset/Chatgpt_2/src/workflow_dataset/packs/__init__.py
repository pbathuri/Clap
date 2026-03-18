"""
M22: Capability-pack installer, resolver, and runtime integration. Local-first.
"""

from __future__ import annotations

from workflow_dataset.packs.pack_models import PackManifest, validate_pack_manifest
from workflow_dataset.packs.pack_registry import (
    list_installed_packs,
    get_installed_pack,
    get_installed_manifest,
)
from workflow_dataset.packs.pack_installer import install_pack, uninstall_pack
from workflow_dataset.packs.pack_resolver import resolve_active_capabilities, ActiveCapabilities
from workflow_dataset.packs.pack_resolution_graph import resolve_with_priority, ResolutionExplanation
from workflow_dataset.packs.pack_conflicts import detect_conflicts, PackConflict, ConflictClass
from workflow_dataset.packs.registry_index import (
    RegistryEntry,
    load_local_registry,
    get_registry_entry,
    list_registry_entries,
)
from workflow_dataset.packs.registry_policy import (
    load_registry_policy,
    check_channel_policy,
    get_registry_policy_path,
)
from workflow_dataset.packs.verify import verify_pack
from workflow_dataset.packs.pack_history import (
    append_install_record,
    get_pack_history,
    get_previous_version,
    get_previous_manifest_path,
)
from workflow_dataset.packs.install_flows import (
    install_pack_from_registry,
    update_pack,
    remove_pack,
    rollback_pack,
    list_installed_with_updates,
)
from workflow_dataset.packs.scaffold import scaffold_pack
from workflow_dataset.packs.authoring_validation import validate_pack_structure, validate_pack_full
from workflow_dataset.packs.certification import run_certification
from workflow_dataset.packs.scorecard import build_pack_scorecard, format_pack_scorecard
from workflow_dataset.packs.gallery import (
    build_gallery_entry,
    build_gallery,
    format_showcase,
    format_gallery_report,
)
from workflow_dataset.packs.behavior_resolver import resolve_behavior_for_task, get_active_behavior_summary
from workflow_dataset.packs.behavior_assets import get_prompt_assets_from_manifest, get_task_defaults_from_manifest
from workflow_dataset.packs.behavior_runtime import (
    get_resolved_behavior_for_job,
    merge_pack_prompts_into_instruction,
    get_behavior_summary_for_job,
)
from workflow_dataset.packs.behavior_models import (
    PackPromptAsset,
    PackTaskDefaults,
    PackRetrievalProfilePreset,
    PackOutputProfilePreset,
    ParserOutputHint,
    ResolvedBehavior,
    BehaviorResolutionResult,
)

__all__ = [
    "PackManifest",
    "validate_pack_manifest",
    "list_installed_packs",
    "get_installed_pack",
    "get_installed_manifest",
    "install_pack",
    "uninstall_pack",
    "resolve_active_capabilities",
    "ActiveCapabilities",
    "resolve_with_priority",
    "ResolutionExplanation",
    "detect_conflicts",
    "PackConflict",
    "ConflictClass",
    "RegistryEntry",
    "load_local_registry",
    "get_registry_entry",
    "list_registry_entries",
    "load_registry_policy",
    "check_channel_policy",
    "get_registry_policy_path",
    "verify_pack",
    "append_install_record",
    "get_pack_history",
    "get_previous_version",
    "get_previous_manifest_path",
    "install_pack_from_registry",
    "update_pack",
    "remove_pack",
    "rollback_pack",
    "list_installed_with_updates",
    "scaffold_pack",
    "validate_pack_structure",
    "validate_pack_full",
    "run_certification",
    "build_pack_scorecard",
    "format_pack_scorecard",
    "build_gallery_entry",
    "build_gallery",
    "format_showcase",
    "format_gallery_report",
    "resolve_behavior_for_task",
    "get_active_behavior_summary",
    "get_resolved_behavior_for_job",
    "merge_pack_prompts_into_instruction",
    "get_behavior_summary_for_job",
    "get_prompt_assets_from_manifest",
    "get_task_defaults_from_manifest",
    "PackPromptAsset",
    "PackTaskDefaults",
    "PackRetrievalProfilePreset",
    "PackOutputProfilePreset",
    "ParserOutputHint",
    "ResolvedBehavior",
    "BehaviorResolutionResult",
]
