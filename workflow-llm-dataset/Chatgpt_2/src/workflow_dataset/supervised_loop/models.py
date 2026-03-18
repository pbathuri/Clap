"""
M27E–M27H: Supervised agent loop — explicit models for cycle, queue, handoff.
Human-in-the-loop; no hidden autonomy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Cycle status: visible states for operator
LOOP_STATUS_PROPOSING = "proposing"
LOOP_STATUS_AWAITING_APPROVAL = "awaiting_approval"
LOOP_STATUS_EXECUTING = "executing"
LOOP_STATUS_COMPLETED = "completed"
LOOP_STATUS_BLOCKED = "blocked"
LOOP_STATUS_IDLE = "idle"


@dataclass
class BlockedCycleReason:
    """Reason a cycle cannot advance (no plan, no next step, policy, etc.)."""
    reason: str
    detail: str = ""
    step_index: int | None = None
    approval_scope: str = ""


@dataclass
class QueuedAction:
    """One proposed action that can be approved/rejected/deferred."""
    action_id: str = ""
    label: str = ""
    action_type: str = ""  # executor_run | planner_compile | executor_resume
    plan_ref: str = ""    # routine_id | job_pack_id for executor
    plan_source: str = "" # routine | job
    mode: str = ""        # simulate | real
    step_index: int | None = None
    why: str = ""
    risk_level: str = ""  # low | medium | high
    trust_mode: str = ""   # simulate | trusted_real_candidate
    created_at: str = ""


@dataclass
class ApprovalQueueItem:
    """Queue entry: proposed action + status (pending | approved | rejected | deferred)."""
    queue_id: str = ""
    action: QueuedAction = field(default_factory=QueuedAction)
    status: str = "pending"  # pending | approved | rejected | deferred
    decided_at: str = ""
    decision_note: str = ""
    cycle_id: str = ""
    # M27H.1: safer deferral — reason and optional revisit hint (ISO date or ""); only when status=deferred
    defer_reason: str = ""
    revisit_after: str = ""


@dataclass
class ExecutionHandoff:
    """Record of handing an approved action to executor/planner and result."""
    handoff_id: str = ""
    queue_id: str = ""
    cycle_id: str = ""
    action_type: str = ""
    plan_ref: str = ""
    plan_source: str = ""
    mode: str = ""
    run_id: str = ""       # executor run_id if applicable
    status: str = ""       # running | completed | blocked | error
    outcome_summary: str = ""
    artifact_paths: list[str] = field(default_factory=list)
    error: str = ""
    started_at: str = ""
    ended_at: str = ""


@dataclass
class AgentCycle:
    """One supervised agent cycle: project/goal, status, proposed/approved/result."""
    cycle_id: str = ""
    project_slug: str = ""   # e.g. founder_case_alpha; maps to goal/session
    goal_text: str = ""
    session_id: str = ""
    plan_id: str = ""
    status: str = LOOP_STATUS_IDLE
    blocked_reason: BlockedCycleReason | None = None
    created_at: str = ""
    updated_at: str = ""
    last_handoff_id: str = ""
    last_run_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "project_slug": self.project_slug,
            "goal_text": self.goal_text,
            "session_id": self.session_id,
            "plan_id": self.plan_id,
            "status": self.status,
            "blocked_reason": {
                "reason": self.blocked_reason.reason,
                "detail": self.blocked_reason.detail,
                "step_index": self.blocked_reason.step_index,
                "approval_scope": self.blocked_reason.approval_scope,
            } if self.blocked_reason else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_handoff_id": self.last_handoff_id,
            "last_run_id": self.last_run_id,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AgentCycle":
        br = d.get("blocked_reason")
        blocked = BlockedCycleReason(
            reason=br.get("reason", ""),
            detail=br.get("detail", ""),
            step_index=br.get("step_index"),
            approval_scope=br.get("approval_scope", ""),
        ) if br else None
        return cls(
            cycle_id=d.get("cycle_id", ""),
            project_slug=d.get("project_slug", ""),
            goal_text=d.get("goal_text", ""),
            session_id=d.get("session_id", ""),
            plan_id=d.get("plan_id", ""),
            status=d.get("status", LOOP_STATUS_IDLE),
            blocked_reason=blocked,
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            last_handoff_id=d.get("last_handoff_id", ""),
            last_run_id=d.get("last_run_id", ""),
        )


@dataclass
class CycleSummary:
    """Summary of current cycle for CLI and mission control."""
    cycle_id: str = ""
    project_slug: str = ""
    goal_text: str = ""
    status: str = ""
    blocked_reason: str = ""
    pending_queue_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    deferred_count: int = 0
    last_handoff_status: str = ""
    last_run_id: str = ""
    next_proposed_action_label: str = ""
    next_proposed_action_id: str = ""


# M27H.1: Operator policies — what can be batch-approved vs always manually reviewed
RISK_ORDER = ("low", "medium", "high")  # index = severity for comparison


@dataclass
class OperatorPolicy:
    """
    Operator policy: batch approval limits, auto-queue vs always manual review.
    Explicit, operator-readable; no hidden auto-execution.
    """
    # Batch approval: only approve pending items with risk_level <= this (in RISK_ORDER)
    batch_approve_max_risk: str = "low"  # "low" | "medium" (never "high" by default)
    # Action types that may be auto-queued without extra gate (e.g. planner_compile in simulate)
    auto_queue_action_types: list[str] = field(default_factory=lambda: ["planner_compile"])
    # Action types that always require manual review (never batch-approved)
    always_manual_review_action_types: list[str] = field(default_factory=lambda: ["executor_resume"])
    # Risk levels that always require manual review
    always_manual_review_risk_levels: list[str] = field(default_factory=lambda: ["high"])
    # Mode that always requires manual review (e.g. real)
    always_manual_review_modes: list[str] = field(default_factory=lambda: ["real"])
    # Deferral: max revisit_after days from now (0 = no revisit hint)
    defer_revisit_max_days: int = 7

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch_approve_max_risk": self.batch_approve_max_risk,
            "auto_queue_action_types": list(self.auto_queue_action_types),
            "always_manual_review_action_types": list(self.always_manual_review_action_types),
            "always_manual_review_risk_levels": list(self.always_manual_review_risk_levels),
            "always_manual_review_modes": list(self.always_manual_review_modes),
            "defer_revisit_max_days": self.defer_revisit_max_days,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> "OperatorPolicy":
        if not d:
            return cls()
        return cls(
            batch_approve_max_risk=d.get("batch_approve_max_risk", "low"),
            auto_queue_action_types=list(d.get("auto_queue_action_types", ["planner_compile"])),
            always_manual_review_action_types=list(d.get("always_manual_review_action_types", ["executor_resume"])),
            always_manual_review_risk_levels=list(d.get("always_manual_review_risk_levels", ["high"])),
            always_manual_review_modes=list(d.get("always_manual_review_modes", ["real"])),
            defer_revisit_max_days=int(d.get("defer_revisit_max_days", 7)),
        )

    def requires_manual_review(self, action: QueuedAction) -> bool:
        """True if this action must not be batch-approved."""
        if action.action_type in self.always_manual_review_action_types:
            return True
        if action.risk_level in self.always_manual_review_risk_levels:
            return True
        if action.mode in self.always_manual_review_modes:
            return True
        return False

    def risk_within_batch_limit(self, risk_level: str) -> bool:
        """True if risk_level is <= batch_approve_max_risk in RISK_ORDER."""
        try:
            idx_risk = RISK_ORDER.index(risk_level) if risk_level in RISK_ORDER else 1
        except ValueError:
            idx_risk = 1
        idx_max = RISK_ORDER.index(self.batch_approve_max_risk) if self.batch_approve_max_risk in RISK_ORDER else 0
        return idx_risk <= idx_max
