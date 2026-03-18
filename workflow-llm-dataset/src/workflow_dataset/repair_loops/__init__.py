"""
M46E–M46H: Reliability repair loops — bounded maintenance control from drift/degradation signals.
"""

from workflow_dataset.repair_loops.models import (
    RepairLoop,
    RepairLoopStatus,
    BoundedRepairPlan,
    MaintenanceAction,
    RepairResult,
    PostRepairVerification,
    RollbackOnFailedRepair,
    RequiredReviewGate,
    ReviewGateKind,
    RepairGuidance,
    RepairGuidanceKind,
    RepairTargetSubsystem,
    Precondition,
)
from workflow_dataset.repair_loops.patterns import (
    get_known_pattern,
    list_known_pattern_ids,
)
from workflow_dataset.repair_loops.signal_to_repair import (
    propose_plan_from_signal,
    propose_plan_and_pattern_from_signal,
    propose_plan_from_reliability_run,
    propose_plan_from_drift,
    list_signal_mappings,
)
from workflow_dataset.repair_loops.profiles import (
    MaintenanceProfile,
    get_maintenance_profile,
    list_maintenance_profile_ids,
)
from workflow_dataset.repair_loops.bundles import (
    SafeRepairBundle,
    get_safe_repair_bundle,
    list_safe_repair_bundle_ids,
    bundle_first_plan,
)
from workflow_dataset.repair_loops.flow import (
    propose_repair_plan,
    review_repair_plan,
    approve_bounded_repair,
    execute_bounded_repair,
    verify_repair,
    escalate_if_failed,
    rollback_if_needed,
)
from workflow_dataset.repair_loops.store import (
    save_repair_loop,
    load_repair_loop,
    list_repair_loops,
    get_repair_loops_dir,
)

__all__ = [
    "RepairLoop",
    "RepairLoopStatus",
    "BoundedRepairPlan",
    "MaintenanceAction",
    "RepairResult",
    "PostRepairVerification",
    "RollbackOnFailedRepair",
    "RequiredReviewGate",
    "ReviewGateKind",
    "RepairGuidance",
    "RepairGuidanceKind",
    "RepairTargetSubsystem",
    "Precondition",
    "get_known_pattern",
    "list_known_pattern_ids",
    "propose_plan_from_signal",
    "propose_plan_from_reliability_run",
    "propose_plan_from_drift",
    "list_signal_mappings",
    "propose_repair_plan",
    "review_repair_plan",
    "approve_bounded_repair",
    "execute_bounded_repair",
    "verify_repair",
    "escalate_if_failed",
    "rollback_if_needed",
    "save_repair_loop",
    "load_repair_loop",
    "list_repair_loops",
    "get_repair_loops_dir",
    "MaintenanceProfile",
    "get_maintenance_profile",
    "list_maintenance_profile_ids",
    "SafeRepairBundle",
    "get_safe_repair_bundle",
    "list_safe_repair_bundle_ids",
    "bundle_first_plan",
]
