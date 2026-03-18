"""
M26A–M26D: Goal-to-plan compiler. Explicit planning layer on top of session, jobs, macros, demos, packs.
No auto-execution; plans are inspectable and preview-only.
"""

from workflow_dataset.planner.schema import (
    GoalRequest,
    Plan,
    PlanStep,
    DependencyEdge,
    Checkpoint,
    ExpectedArtifact,
    BlockedCondition,
    ProvenanceSource,
    STEP_CLASS_REASONING,
    STEP_CLASS_LOCAL_INSPECT,
    STEP_CLASS_SANDBOX_WRITE,
    STEP_CLASS_TRUSTED_REAL_CANDIDATE,
    STEP_CLASS_HUMAN_REQUIRED,
    STEP_CLASS_BLOCKED,
)
from workflow_dataset.planner.compile import compile_goal_to_plan
from workflow_dataset.planner.explain import explain_plan
from workflow_dataset.planner.preview import format_plan_preview, format_plan_graph
from workflow_dataset.planner.store import (
    save_current_goal,
    load_current_goal,
    save_latest_plan,
    load_latest_plan,
)

__all__ = [
    "GoalRequest",
    "Plan",
    "PlanStep",
    "DependencyEdge",
    "Checkpoint",
    "ExpectedArtifact",
    "BlockedCondition",
    "ProvenanceSource",
    "STEP_CLASS_REASONING",
    "STEP_CLASS_LOCAL_INSPECT",
    "STEP_CLASS_SANDBOX_WRITE",
    "STEP_CLASS_TRUSTED_REAL_CANDIDATE",
    "STEP_CLASS_HUMAN_REQUIRED",
    "STEP_CLASS_BLOCKED",
    "compile_goal_to_plan",
    "explain_plan",
    "format_plan_preview",
    "format_plan_graph",
    "save_current_goal",
    "load_current_goal",
    "save_latest_plan",
    "load_latest_plan",
]
