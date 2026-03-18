"""
M34E–M34H: Bounded background runner — models for background run, trigger, queued job, execution mode, approval, artifact, failure/retry, summary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RunSourceTrigger(str, Enum):
    """How this background run was triggered."""
    RECURRING_MATCH = "recurring_match"
    MANUAL = "manual"
    CRON = "cron"
    REMINDER_DUE = "reminder_due"
    UNKNOWN = "unknown"


class ExecutionMode(str, Enum):
    """Execution mode for the run."""
    SIMULATE = "simulate"
    REAL = "real"
    SIMULATE_THEN_REAL = "simulate_then_real"
    DEGRADED_SIMULATE = "degraded_simulate"


class ApprovalState(str, Enum):
    """Approval state for background execution."""
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"


@dataclass
class QueuedRecurringJob:
    """One recurring workflow queued for background execution (contract from Pane 1)."""
    automation_id: str = ""
    plan_source: str = ""   # routine | job
    plan_ref: str = ""      # routine_id or job_pack_id
    trigger_type: str = ""  # schedule | reminder_due | manual
    schedule_or_trigger_ref: str = ""
    allowed_modes: list[str] = field(default_factory=list)  # ["simulate"] or ["simulate", "real"]
    require_approval_before_real: bool = True
    label: str = ""
    created_at: str = ""
    last_queued_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "automation_id": self.automation_id,
            "plan_source": self.plan_source,
            "plan_ref": self.plan_ref,
            "trigger_type": self.trigger_type,
            "schedule_or_trigger_ref": self.schedule_or_trigger_ref,
            "allowed_modes": list(self.allowed_modes),
            "require_approval_before_real": self.require_approval_before_real,
            "label": self.label,
            "created_at": self.created_at,
            "last_queued_at": self.last_queued_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "QueuedRecurringJob":
        return cls(
            automation_id=d.get("automation_id", ""),
            plan_source=d.get("plan_source", ""),
            plan_ref=d.get("plan_ref", ""),
            trigger_type=d.get("trigger_type", ""),
            schedule_or_trigger_ref=d.get("schedule_or_trigger_ref", ""),
            allowed_modes=list(d.get("allowed_modes", [])),
            require_approval_before_real=bool(d.get("require_approval_before_real", True)),
            label=d.get("label", ""),
            created_at=d.get("created_at", ""),
            last_queued_at=d.get("last_queued_at", ""),
        )


@dataclass
class BackgroundArtifact:
    """Output/artifact produced by a background run."""
    path: str = ""
    kind: str = ""   # file | log | report
    run_id: str = ""
    step_index: int = 0


@dataclass
class FailureRetryState:
    """Failure and retry state for a run."""
    failed: bool = False
    failure_reason: str = ""
    failure_code: str = ""   # blocked | policy_suppressed | transient | degraded
    retry_count: int = 0
    max_retries: int = 3
    defer_until: str = ""
    handoff_to_review: bool = False


@dataclass
class BackgroundRun:
    """One background run record: intent, policy result, execution state, outcomes."""
    run_id: str = ""
    automation_id: str = ""
    source_trigger: str = ""   # RunSourceTrigger value
    plan_source: str = ""
    plan_ref: str = ""
    execution_mode: str = ""   # ExecutionMode value
    approval_state: str = ""   # ApprovalState value
    status: str = ""           # queued | running | completed | blocked | failed | cancelled | suppressed
    executor_run_id: str = ""
    timestamp_start: str = ""
    timestamp_end: str = ""
    artifacts: list[BackgroundArtifact] = field(default_factory=list)
    failure_retry: FailureRetryState = field(default_factory=FailureRetryState)
    policy_notes: list[str] = field(default_factory=list)
    run_path: str = ""
    outcome_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "automation_id": self.automation_id,
            "source_trigger": self.source_trigger,
            "plan_source": self.plan_source,
            "plan_ref": self.plan_ref,
            "execution_mode": self.execution_mode,
            "approval_state": self.approval_state,
            "status": self.status,
            "executor_run_id": self.executor_run_id,
            "timestamp_start": self.timestamp_start,
            "timestamp_end": self.timestamp_end,
            "artifacts": [
                {"path": a.path, "kind": a.kind, "run_id": a.run_id, "step_index": a.step_index}
                for a in self.artifacts
            ],
            "failure_retry": {
                "failed": self.failure_retry.failed,
                "failure_reason": self.failure_retry.failure_reason,
                "failure_code": self.failure_retry.failure_code,
                "retry_count": self.failure_retry.retry_count,
                "max_retries": self.failure_retry.max_retries,
                "defer_until": self.failure_retry.defer_until,
                "handoff_to_review": self.failure_retry.handoff_to_review,
            },
            "policy_notes": list(self.policy_notes),
            "run_path": self.run_path,
            "outcome_summary": self.outcome_summary,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "BackgroundRun":
        fr = d.get("failure_retry", {})
        failure_retry = FailureRetryState(
            failed=bool(fr.get("failed", False)),
            failure_reason=fr.get("failure_reason", ""),
            failure_code=fr.get("failure_code", ""),
            retry_count=int(fr.get("retry_count", 0)),
            max_retries=int(fr.get("max_retries", 3)),
            defer_until=fr.get("defer_until", ""),
            handoff_to_review=bool(fr.get("handoff_to_review", False)),
        )
        artifacts = [
            BackgroundArtifact(
                path=a.get("path", ""),
                kind=a.get("kind", ""),
                run_id=a.get("run_id", ""),
                step_index=int(a.get("step_index", 0)),
            )
            for a in d.get("artifacts", [])
        ]
        return cls(
            run_id=d.get("run_id", ""),
            automation_id=d.get("automation_id", ""),
            source_trigger=d.get("source_trigger", ""),
            plan_source=d.get("plan_source", ""),
            plan_ref=d.get("plan_ref", ""),
            execution_mode=d.get("execution_mode", ""),
            approval_state=d.get("approval_state", ""),
            status=d.get("status", ""),
            executor_run_id=d.get("executor_run_id", ""),
            timestamp_start=d.get("timestamp_start", ""),
            timestamp_end=d.get("timestamp_end", ""),
            artifacts=artifacts,
            failure_retry=failure_retry,
            policy_notes=list(d.get("policy_notes", [])),
            run_path=d.get("run_path", ""),
            outcome_summary=d.get("outcome_summary", ""),
        )


@dataclass
class RunSummary:
    """Summary of background runner state for reports."""
    active_run_ids: list[str] = field(default_factory=list)
    blocked_run_ids: list[str] = field(default_factory=list)
    retryable_run_ids: list[str] = field(default_factory=list)
    next_automation_id: str = ""
    next_plan_ref: str = ""
    recent_outcomes: list[dict[str, Any]] = field(default_factory=list)
    needs_review_automation_ids: list[str] = field(default_factory=list)
    queue_length: int = 0


# ----- M34H.1 Retry policies + async degraded fallbacks -----


class BackoffStrategy(str, Enum):
    """Backoff strategy for retries."""
    FIXED = "fixed"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"


@dataclass
class RetryPolicy:
    """Retry policy: max retries, backoff, suppression and handoff thresholds."""
    policy_id: str = ""
    max_retries: int = 3
    backoff_strategy: str = BackoffStrategy.EXPONENTIAL.value
    backoff_base_seconds: int = 60
    suppress_after_failures: int = 0   # 0 = do not auto-suppress
    handoff_after_failures: int = 0   # 0 = do not auto-handoff to review
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "max_retries": self.max_retries,
            "backoff_strategy": self.backoff_strategy,
            "backoff_base_seconds": self.backoff_base_seconds,
            "suppress_after_failures": self.suppress_after_failures,
            "handoff_after_failures": self.handoff_after_failures,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RetryPolicy":
        return cls(
            policy_id=d.get("policy_id", ""),
            max_retries=int(d.get("max_retries", 3)),
            backoff_strategy=d.get("backoff_strategy", BackoffStrategy.EXPONENTIAL.value),
            backoff_base_seconds=int(d.get("backoff_base_seconds", 60)),
            suppress_after_failures=int(d.get("suppress_after_failures", 0)),
            handoff_after_failures=int(d.get("handoff_after_failures", 0)),
            label=d.get("label", ""),
        )


@dataclass
class AsyncDegradedFallbackProfile:
    """When to use a degraded fallback for async background runs and what the operator should know."""
    profile_id: str = ""
    name: str = ""
    when_to_use: str = ""   # transient | degraded | approval_blocked | ...
    fallback_mode: str = ""  # degraded_simulate | skip | handoff
    operator_explanation: str = ""
    still_works: list[str] = field(default_factory=list)
    disabled_flows: list[str] = field(default_factory=list)
