"""
M30E–M30H: Reliability harness and golden-path recovery.
Local-first: golden-path validation, outcome classification, recovery playbooks, reports.
"""

from workflow_dataset.reliability.models import (
    GoldenPathScenario,
    ReliabilityRunResult,
    RecoveryCase,
    DegradedModeProfile,
    FallbackRule,
)
from workflow_dataset.reliability.golden_paths import (
    list_path_ids,
    get_path,
    BUILTIN_GOLDEN_PATHS,
)
from workflow_dataset.reliability.harness import (
    run_golden_path,
    classify_run_result,
)
from workflow_dataset.reliability.store import (
    save_run,
    load_latest_run,
    list_runs,
    get_reliability_dir,
)
from workflow_dataset.reliability.report import format_reliability_report
from workflow_dataset.reliability.recovery_playbooks import (
    RECOVERY_CASES,
    suggest_recovery,
    get_recovery_guide,
    list_recovery_cases,
)
from workflow_dataset.reliability.degraded_profiles import (
    BUILTIN_DEGRADED_PROFILES,
    list_profile_ids,
    get_profile,
    resolve_profile_for_subsystem,
    resolve_profile_for_unavailable_subsystems,
    profile_to_dict,
)
from workflow_dataset.reliability.fallback_matrix import (
    FALLBACK_MATRIX,
    list_subsystems_with_fallback,
    get_fallback_rules,
    build_fallback_matrix_output,
    format_fallback_matrix_text,
)

__all__ = [
    "GoldenPathScenario",
    "ReliabilityRunResult",
    "RecoveryCase",
    "list_path_ids",
    "get_path",
    "BUILTIN_GOLDEN_PATHS",
    "run_golden_path",
    "classify_run_result",
    "save_run",
    "load_latest_run",
    "list_runs",
    "get_reliability_dir",
    "format_reliability_report",
    "RECOVERY_CASES",
    "suggest_recovery",
    "get_recovery_guide",
    "list_recovery_cases",
    "DegradedModeProfile",
    "FallbackRule",
    "BUILTIN_DEGRADED_PROFILES",
    "list_profile_ids",
    "get_profile",
    "resolve_profile_for_subsystem",
    "resolve_profile_for_unavailable_subsystems",
    "profile_to_dict",
    "FALLBACK_MATRIX",
    "list_subsystems_with_fallback",
    "get_fallback_rules",
    "build_fallback_matrix_output",
    "format_fallback_matrix_text",
]
