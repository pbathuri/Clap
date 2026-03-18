"""
M45A–M45D: Adaptive execution — bounded multi-step plans, loops, progression, stop/escalation.
"""

from __future__ import annotations

from workflow_dataset.adaptive_execution.models import (
    AdaptiveExecutionPlan,
    BoundedExecutionLoop,
    ExecutionStep,
    PlanBranch,
    StepOutcome,
    AdaptationTrigger,
    StopCondition,
    EscalationCondition,
    HumanTakeoverPoint,
    ExecutionProfile,
    LoopTemplate,
)
from workflow_dataset.adaptive_execution.profiles import (
    list_profiles as list_execution_profiles,
    get_profile as get_execution_profile,
    get_profile_why_safe,
    get_profile_when_blocked,
    PROFILE_CONSERVATIVE,
    PROFILE_BALANCED,
    PROFILE_OPERATOR_HEAVY,
    PROFILE_REVIEW_HEAVY,
)
from workflow_dataset.adaptive_execution.templates import (
    list_templates,
    get_template,
    explain_template_safety,
    TEMPLATE_WEEKLY_SUMMARY,
    TEMPLATE_APPROVAL_SWEEP,
    TEMPLATE_RESUME_CONTINUITY,
    TEMPLATE_SINGLE_JOB_RUN,
)
from workflow_dataset.adaptive_execution.explain_safety import explain_loop_safety, format_safety_explanation
from workflow_dataset.adaptive_execution.generator import (
    generate_plan_from_goal,
    create_bounded_loop,
    generate_loop_from_goal,
)
from workflow_dataset.adaptive_execution.store import save_loop, load_loop, list_active_loops
from workflow_dataset.adaptive_execution.progression import (
    advance_step,
    stop_loop,
    escalate_loop,
    record_takeover_decision,
)
from workflow_dataset.adaptive_execution.mission_control import adaptive_execution_slice

__all__ = [
    "AdaptiveExecutionPlan",
    "BoundedExecutionLoop",
    "ExecutionStep",
    "PlanBranch",
    "StepOutcome",
    "AdaptationTrigger",
    "StopCondition",
    "EscalationCondition",
    "HumanTakeoverPoint",
    "ExecutionProfile",
    "LoopTemplate",
    "list_execution_profiles",
    "get_execution_profile",
    "get_profile_why_safe",
    "get_profile_when_blocked",
    "PROFILE_CONSERVATIVE",
    "PROFILE_BALANCED",
    "PROFILE_OPERATOR_HEAVY",
    "PROFILE_REVIEW_HEAVY",
    "list_templates",
    "get_template",
    "explain_template_safety",
    "TEMPLATE_WEEKLY_SUMMARY",
    "TEMPLATE_APPROVAL_SWEEP",
    "TEMPLATE_RESUME_CONTINUITY",
    "TEMPLATE_SINGLE_JOB_RUN",
    "explain_loop_safety",
    "format_safety_explanation",
    "generate_plan_from_goal",
    "create_bounded_loop",
    "generate_loop_from_goal",
    "save_loop",
    "load_loop",
    "list_active_loops",
    "advance_step",
    "stop_loop",
    "escalate_loop",
    "record_takeover_decision",
    "adaptive_execution_slice",
]
