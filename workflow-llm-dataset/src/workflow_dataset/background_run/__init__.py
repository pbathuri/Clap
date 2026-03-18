"""
M34E–M34H: Bounded background runner — policy-aware async execution for approved recurring workflows.
Local, simulate-first, no hidden daemon. Uses executor, policy, and trust layers.
"""

from workflow_dataset.background_run.models import (
    BackgroundRun,
    BackgroundArtifact,
    FailureRetryState,
    QueuedRecurringJob,
    RunSourceTrigger,
    ExecutionMode,
    ApprovalState,
    RunSummary,
    BackoffStrategy,
    RetryPolicy,
    AsyncDegradedFallbackProfile,
)
from workflow_dataset.background_run.store import (
    get_background_root,
    get_runs_dir,
    load_queue,
    save_queue,
    load_run,
    save_run,
    list_runs,
    load_history,
    append_history_entry,
    load_retry_policies,
    save_retry_policies,
)
from workflow_dataset.background_run.retry_policies import (
    get_policy_for_automation,
    compute_defer_until,
    DEFAULT_RETRY_POLICY,
)
from workflow_dataset.background_run.degraded_fallback import (
    build_degraded_fallback_report,
    get_fallback_for_failure,
    ASYNC_DEGRADED_FALLBACK_PROFILES,
)
from workflow_dataset.background_run.explain import (
    build_failure_explanation,
    build_fallback_explanation,
)
from workflow_dataset.background_run.gating import evaluate_background_policy, GatingResult
from workflow_dataset.background_run.runner import (
    pick_eligible_job,
    run_one_background,
    build_run_summary,
)
from workflow_dataset.background_run.recovery import (
    classify_failure,
    retry_run,
    defer_run,
    handoff_to_review,
    suppress_run,
)

__all__ = [
    "BackgroundRun",
    "BackgroundArtifact",
    "FailureRetryState",
    "QueuedRecurringJob",
    "RunSourceTrigger",
    "ExecutionMode",
    "ApprovalState",
    "RunSummary",
    "BackoffStrategy",
    "RetryPolicy",
    "AsyncDegradedFallbackProfile",
    "get_background_root",
    "get_runs_dir",
    "load_queue",
    "save_queue",
    "load_run",
    "save_run",
    "list_runs",
    "load_history",
    "append_history_entry",
    "load_retry_policies",
    "save_retry_policies",
    "get_policy_for_automation",
    "compute_defer_until",
    "DEFAULT_RETRY_POLICY",
    "build_degraded_fallback_report",
    "get_fallback_for_failure",
    "ASYNC_DEGRADED_FALLBACK_PROFILES",
    "build_failure_explanation",
    "build_fallback_explanation",
    "evaluate_background_policy",
    "GatingResult",
    "pick_eligible_job",
    "run_one_background",
    "build_run_summary",
    "classify_failure",
    "retry_run",
    "defer_run",
    "handoff_to_review",
    "suppress_run",
]
