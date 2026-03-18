"""
M45E–M45H: Shadow execution + confidence/intervention gates.
M45H.1: Confidence policies + promotion eligibility report.
"""

from workflow_dataset.shadow_execution.models import (
    ShadowRun,
    ExpectedOutcome,
    ObservedOutcome,
    ConfidenceScore,
    RiskMarker,
    InterventionGate,
    GateFailureReason,
    SafeToContinueState,
    ForcedTakeoverState,
    ConfidencePolicy,
    PromotionEligibilityReport,
)
from workflow_dataset.shadow_execution.runner import create_shadow_run, run_shadow_loop
from workflow_dataset.shadow_execution.store import save_shadow_run, load_shadow_run, list_shadow_runs
from workflow_dataset.shadow_execution.policies import (
    get_policy_for_loop_type,
    evaluate_promotion_eligibility,
    build_promotion_eligibility_report,
)

__all__ = [
    "ShadowRun",
    "ExpectedOutcome",
    "ObservedOutcome",
    "ConfidenceScore",
    "RiskMarker",
    "InterventionGate",
    "GateFailureReason",
    "SafeToContinueState",
    "ForcedTakeoverState",
    "ConfidencePolicy",
    "PromotionEligibilityReport",
    "create_shadow_run",
    "run_shadow_loop",
    "save_shadow_run",
    "load_shadow_run",
    "list_shadow_runs",
    "get_policy_for_loop_type",
    "evaluate_promotion_eligibility",
    "build_promotion_eligibility_report",
]
