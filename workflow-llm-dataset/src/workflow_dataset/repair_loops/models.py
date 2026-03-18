"""
M46E–M46H: Repair loop and maintenance control models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RepairLoopStatus(str, Enum):
    """Lifecycle of a repair loop."""
    proposed = "proposed"
    under_review = "under_review"
    approved = "approved"
    executing = "executing"
    verifying = "verifying"
    verified = "verified"
    failed = "failed"
    rolled_back = "rolled_back"
    escalated = "escalated"
    cancelled = "cancelled"


class ReviewGateKind(str, Enum):
    """Kind of required review before execute."""
    operator_approval = "operator_approval"
    council_review = "council_review"
    trust_policy = "trust_policy"


class RepairGuidanceKind(str, Enum):
    """M46H.1: Operator-facing guidance — do now vs schedule later."""
    do_now = "do_now"
    schedule_later = "schedule_later"


@dataclass
class RepairGuidance:
    """M46H.1: Operator-facing repair guidance (do now vs schedule later)."""
    kind: RepairGuidanceKind
    reason: str = ""
    suggested_schedule: str = ""  # e.g. "next_ops_window", "next_downtime"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "reason": self.reason,
            "suggested_schedule": self.suggested_schedule,
        }


@dataclass
class RepairTargetSubsystem:
    """Subsystem or area targeted by repair (e.g. queue, memory, runtime, operator_mode)."""
    subsystem_id: str
    name: str
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"subsystem_id": self.subsystem_id, "name": self.name, "description": self.description}


@dataclass
class Precondition:
    """Condition that must hold before a repair step or the whole plan can run."""
    precondition_id: str
    description: str
    check_command: str = ""  # optional CLI to verify
    required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "precondition_id": self.precondition_id,
            "description": self.description,
            "check_command": self.check_command,
            "required": self.required,
        }


@dataclass
class MaintenanceAction:
    """Single bounded maintenance action (e.g. run a command, trigger an ops job)."""
    action_id: str
    name: str
    description: str = ""
    run_command: str = ""  # e.g. "queue_summary", "reliability_run"
    run_command_args: list[str] = field(default_factory=list)
    preconditions: list[Precondition] = field(default_factory=list)
    rollback_command: str = ""  # optional; used on failed repair
    rollback_args: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "name": self.name,
            "description": self.description,
            "run_command": self.run_command,
            "run_command_args": self.run_command_args,
            "preconditions": [p.to_dict() for p in self.preconditions],
            "rollback_command": self.rollback_command,
            "rollback_args": self.rollback_args,
        }


@dataclass
class RequiredReviewGate:
    """Gate that must be passed before execute."""
    gate_id: str
    kind: ReviewGateKind
    description: str
    passed: bool = False
    passed_at: str = ""
    passed_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "kind": self.kind.value,
            "description": self.description,
            "passed": self.passed,
            "passed_at": self.passed_at,
            "passed_by": self.passed_by,
        }


@dataclass
class BoundedRepairPlan:
    """Ordered set of maintenance actions with preconditions and review gate."""
    plan_id: str
    name: str
    description: str = ""
    target_subsystem: RepairTargetSubsystem | None = None
    actions: list[MaintenanceAction] = field(default_factory=list)
    preconditions: list[Precondition] = field(default_factory=list)
    required_review_gate: RequiredReviewGate | None = None
    verification_command: str = ""  # e.g. reliability run to re-check
    verification_args: list[str] = field(default_factory=list)
    rollback_on_failed_repair: bool = True
    escalation_target: str = ""  # e.g. "reliability", "support", "council"

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "name": self.name,
            "description": self.description,
            "target_subsystem": self.target_subsystem.to_dict() if self.target_subsystem else None,
            "actions": [a.to_dict() for a in self.actions],
            "preconditions": [p.to_dict() for p in self.preconditions],
            "required_review_gate": self.required_review_gate.to_dict() if self.required_review_gate else None,
            "verification_command": self.verification_command,
            "verification_args": self.verification_args,
            "rollback_on_failed_repair": self.rollback_on_failed_repair,
            "escalation_target": self.escalation_target,
        }


@dataclass
class PostRepairVerification:
    """Result of post-repair verification step."""
    verification_id: str
    plan_id: str
    passed: bool
    details: str = ""
    run_command: str = ""
    run_output: str = ""
    timestamp: str = ""


@dataclass
class RollbackOnFailedRepair:
    """Record of rollback performed after failed repair."""
    rollback_id: str
    plan_id: str
    actions_rolled_back: list[str] = field(default_factory=list)
    success: bool = False
    details: str = ""
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "rollback_id": self.rollback_id,
            "plan_id": self.plan_id,
            "actions_rolled_back": self.actions_rolled_back,
            "success": self.success,
            "details": self.details,
            "timestamp": self.timestamp,
        }


@dataclass
class RepairResult:
    """Outcome of executing a bounded repair (or a single action)."""
    result_id: str
    plan_id: str
    action_id: str
    success: bool
    details: str = ""
    output: str = ""
    duration_seconds: float = 0.0
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "plan_id": self.plan_id,
            "action_id": self.action_id,
            "success": self.success,
            "details": self.details,
            "output": self.output,
            "duration_seconds": self.duration_seconds,
            "timestamp": self.timestamp,
        }


@dataclass
class RepairLoop:
    """Full repair loop: plan, status, results, verification, rollback."""
    repair_loop_id: str
    plan: BoundedRepairPlan
    status: RepairLoopStatus = RepairLoopStatus.proposed
    source_signal_id: str = ""  # e.g. drift_123, run_abc
    source_signal_type: str = ""  # drift, reliability_run, etc.
    created_at: str = ""
    updated_at: str = ""
    approved_at: str = ""
    approved_by: str = ""
    executed_at: str = ""
    results: list[RepairResult] = field(default_factory=list)
    verification: PostRepairVerification | None = None
    rollback: RollbackOnFailedRepair | None = None
    escalation_reason: str = ""
    # M46H.1: Maintenance profile and bundle context + operator guidance
    maintenance_profile_id: str = ""
    repair_bundle_id: str = ""
    operator_guidance: RepairGuidance | None = None

    def to_dict(self) -> dict[str, Any]:
        def _serialize(obj: Any) -> Any:
            if hasattr(obj, "to_dict"):
                return obj.to_dict()
            if hasattr(obj, "value"):
                return obj.value
            if isinstance(obj, list):
                return [_serialize(x) for x in obj]
            if isinstance(obj, dict):
                return {k: _serialize(v) for k, v in obj.items()}
            return obj

        return {
            "repair_loop_id": self.repair_loop_id,
            "plan_id": self.plan.plan_id,
            "plan_name": self.plan.name,
            "status": self.status.value,
            "source_signal_id": self.source_signal_id,
            "source_signal_type": self.source_signal_type,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "approved_at": self.approved_at,
            "approved_by": self.approved_by,
            "executed_at": self.executed_at,
            "results": [_serialize(r) for r in self.results],
            "verification": _serialize(self.verification) if self.verification else None,
            "rollback": _serialize(self.rollback) if self.rollback else None,
            "escalation_reason": self.escalation_reason,
            "maintenance_profile_id": self.maintenance_profile_id,
            "repair_bundle_id": self.repair_bundle_id,
            "operator_guidance": _serialize(self.operator_guidance) if self.operator_guidance else None,
            "plan": _serialize(self.plan),
        }
