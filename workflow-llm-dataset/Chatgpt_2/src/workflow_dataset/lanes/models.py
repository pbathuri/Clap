"""
M28E–M28H: Bounded worker lane and delegated subplan models.
Explicit, inspectable; no uncontrolled autonomy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Lane status: visible to operator
LANE_STATUS_OPEN = "open"
LANE_STATUS_RUNNING = "running"
LANE_STATUS_BLOCKED = "blocked"
LANE_STATUS_COMPLETED = "completed"
LANE_STATUS_CLOSED = "closed"

# Lane permissions
LANE_PERMISSION_SIMULATE_ONLY = "simulate_only"
LANE_PERMISSION_TRUSTED_REAL_IF_APPROVED = "trusted_real_if_approved"

# Trust/approval mode for subplan
TRUST_MODE_SIMULATE = "simulate"
TRUST_MODE_TRUSTED_REAL_IF_APPROVED = "trusted_real_if_approved"


@dataclass
class LaneScope:
    """Narrow scope for a worker lane (e.g. extract_only, summarize_only)."""
    scope_id: str
    label: str = ""
    description: str = ""
    allowed_step_classes: list[str] = field(default_factory=list)  # empty = all allowed within permissions

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope_id": self.scope_id,
            "label": self.label,
            "description": self.description,
            "allowed_step_classes": list(self.allowed_step_classes),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LaneScope:
        return cls(
            scope_id=d.get("scope_id", ""),
            label=d.get("label", ""),
            description=d.get("description", ""),
            allowed_step_classes=list(d.get("allowed_step_classes", [])),
        )


@dataclass
class LanePermissions:
    """What the lane is allowed to do: simulate only or trusted real if approved."""
    permission: str = LANE_PERMISSION_SIMULATE_ONLY  # simulate_only | trusted_real_if_approved
    approval_required_before_real: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "permission": self.permission,
            "approval_required_before_real": self.approval_required_before_real,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LanePermissions:
        return cls(
            permission=d.get("permission", LANE_PERMISSION_SIMULATE_ONLY),
            approval_required_before_real=bool(d.get("approval_required_before_real", True)),
        )


@dataclass
class LaneArtifact:
    """Artifact or result produced by a lane step."""
    label: str
    path_or_type: str = ""
    step_index: int | None = None
    produced_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "path_or_type": self.path_or_type,
            "step_index": self.step_index,
            "produced_at": self.produced_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LaneArtifact:
        return cls(
            label=d.get("label", ""),
            path_or_type=d.get("path_or_type", ""),
            step_index=d.get("step_index"),
            produced_at=d.get("produced_at", ""),
        )


@dataclass
class LaneFailure:
    """Lane-level failure or blocked reason."""
    reason: str
    step_index: int | None = None
    approval_scope: str = ""
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "reason": self.reason,
            "step_index": self.step_index,
            "approval_scope": self.approval_scope,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LaneFailure:
        return cls(
            reason=d.get("reason", ""),
            step_index=d.get("step_index"),
            approval_scope=d.get("approval_scope", ""),
            timestamp=d.get("timestamp", ""),
        )


# Handoff approval: M28H.1 operator approval before accepting into project
HANDOFF_STATUS_DELIVERED = "delivered"
HANDOFF_STATUS_APPROVED = "approved"
HANDOFF_STATUS_REJECTED = "rejected"
HANDOFF_STATUS_ACCEPTED = "accepted"  # approved + results accepted into project


@dataclass
class LaneHandoff:
    """Record of handing lane results back to parent project/loop. M28H.1: delivered → approved/rejected → accepted."""
    handoff_id: str = ""
    lane_id: str = ""
    project_id: str = ""
    goal_id: str = ""
    status: str = ""  # delivered | approved | rejected | accepted
    artifact_paths: list[str] = field(default_factory=list)
    summary: str = ""
    delivered_at: str = ""
    acknowledged_at: str = ""
    approved_at: str = ""
    approved_by: str = ""
    rejection_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "handoff_id": self.handoff_id,
            "lane_id": self.lane_id,
            "project_id": self.project_id,
            "goal_id": self.goal_id,
            "status": self.status,
            "artifact_paths": list(self.artifact_paths),
            "summary": self.summary,
            "delivered_at": self.delivered_at,
            "acknowledged_at": self.acknowledged_at,
            "approved_at": self.approved_at,
            "approved_by": self.approved_by,
            "rejection_reason": self.rejection_reason,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LaneHandoff:
        return cls(
            handoff_id=d.get("handoff_id", ""),
            lane_id=d.get("lane_id", ""),
            project_id=d.get("project_id", ""),
            goal_id=d.get("goal_id", ""),
            status=d.get("status", ""),
            artifact_paths=list(d.get("artifact_paths", [])),
            summary=d.get("summary", ""),
            delivered_at=d.get("delivered_at", ""),
            acknowledged_at=d.get("acknowledged_at", ""),
            approved_at=d.get("approved_at", ""),
            approved_by=d.get("approved_by", ""),
            rejection_reason=d.get("rejection_reason", ""),
        )


@dataclass
class DelegatedSubplanStep:
    """Single step in a delegated subplan (subset of plan steps)."""
    step_index: int
    label: str
    step_class: str = ""
    trust_level: str = ""
    approval_required: bool = False
    expected_outputs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "label": self.label,
            "step_class": self.step_class,
            "trust_level": self.trust_level,
            "approval_required": self.approval_required,
            "expected_outputs": list(self.expected_outputs),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DelegatedSubplanStep:
        return cls(
            step_index=int(d.get("step_index", 0)),
            label=d.get("label", ""),
            step_class=d.get("step_class", ""),
            trust_level=d.get("trust_level", ""),
            approval_required=bool(d.get("approval_required", False)),
            expected_outputs=list(d.get("expected_outputs", [])),
        )


@dataclass
class DelegatedSubplan:
    """Bounded subplan delegated to a worker lane: explicit scope, outputs, trust mode, stop conditions."""
    subplan_id: str
    scope: LaneScope
    steps: list[DelegatedSubplanStep] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    trust_mode: str = TRUST_MODE_SIMULATE
    approval_mode: str = "checkpoint_before_real"  # checkpoint_before_real | no_checkpoint
    stop_conditions: list[str] = field(default_factory=list)  # e.g. ["max_steps:5", "on_blocked"]
    parent_plan_id: str = ""
    parent_goal_id: str = ""
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "subplan_id": self.subplan_id,
            "scope": self.scope.to_dict(),
            "steps": [s.to_dict() for s in self.steps],
            "expected_outputs": list(self.expected_outputs),
            "trust_mode": self.trust_mode,
            "approval_mode": self.approval_mode,
            "stop_conditions": list(self.stop_conditions),
            "parent_plan_id": self.parent_plan_id,
            "parent_goal_id": self.parent_goal_id,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DelegatedSubplan:
        scope_d = d.get("scope", {})
        scope = LaneScope.from_dict(scope_d) if scope_d else LaneScope(scope_id="default")
        steps = [DelegatedSubplanStep.from_dict(s) for s in d.get("steps", [])]
        return cls(
            subplan_id=d.get("subplan_id", ""),
            scope=scope,
            steps=steps,
            expected_outputs=list(d.get("expected_outputs", [])),
            trust_mode=d.get("trust_mode", TRUST_MODE_SIMULATE),
            approval_mode=d.get("approval_mode", "checkpoint_before_real"),
            stop_conditions=list(d.get("stop_conditions", [])),
            parent_plan_id=d.get("parent_plan_id", ""),
            parent_goal_id=d.get("parent_goal_id", ""),
            created_at=d.get("created_at", ""),
        )


# Lane trust/readiness: M28H.1 reporting
READINESS_READY = "ready"
READINESS_NOT_READY = "not_ready"


@dataclass
class WorkerLane:
    """Bounded worker lane: project/goal, scope, permissions, status, subplan, artifacts, handoff. M28H.1: trust_summary, readiness."""
    lane_id: str
    project_id: str = ""
    goal_id: str = ""
    scope: LaneScope = field(default_factory=lambda: LaneScope(scope_id="default"))
    permissions: LanePermissions = field(default_factory=LanePermissions)
    status: str = LANE_STATUS_OPEN
    subplan: DelegatedSubplan | None = None
    artifacts: list[LaneArtifact] = field(default_factory=list)
    failure: LaneFailure | None = None
    handoff: LaneHandoff | None = None
    run_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    closed_at: str = ""
    # M28H.1: lane-level trust/readiness reporting (optional; can be computed if blank)
    trust_summary: str = ""
    readiness_status: str = ""
    readiness_reason: str = ""
    bundle_id: str = ""  # optional: lane created from this bundle

    def to_dict(self) -> dict[str, Any]:
        return {
            "lane_id": self.lane_id,
            "project_id": self.project_id,
            "goal_id": self.goal_id,
            "scope": self.scope.to_dict(),
            "permissions": self.permissions.to_dict(),
            "status": self.status,
            "subplan": self.subplan.to_dict() if self.subplan else None,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "failure": self.failure.to_dict() if self.failure else None,
            "handoff": self.handoff.to_dict() if self.handoff else None,
            "run_id": self.run_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "closed_at": self.closed_at,
            "trust_summary": self.trust_summary,
            "readiness_status": self.readiness_status,
            "readiness_reason": self.readiness_reason,
            "bundle_id": self.bundle_id,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> WorkerLane:
        scope_d = d.get("scope", {})
        scope = LaneScope.from_dict(scope_d) if scope_d else LaneScope(scope_id="default")
        perms_d = d.get("permissions", {})
        perms = LanePermissions.from_dict(perms_d) if perms_d else LanePermissions()
        subplan_d = d.get("subplan")
        subplan = DelegatedSubplan.from_dict(subplan_d) if subplan_d else None
        artifacts = [LaneArtifact.from_dict(a) for a in d.get("artifacts", [])]
        failure_d = d.get("failure")
        failure = LaneFailure.from_dict(failure_d) if failure_d else None
        handoff_d = d.get("handoff")
        handoff = LaneHandoff.from_dict(handoff_d) if handoff_d else None
        return cls(
            lane_id=d.get("lane_id", ""),
            project_id=d.get("project_id", ""),
            goal_id=d.get("goal_id", ""),
            scope=scope,
            permissions=perms,
            status=d.get("status", LANE_STATUS_OPEN),
            subplan=subplan,
            artifacts=artifacts,
            failure=failure,
            handoff=handoff,
            run_id=d.get("run_id", ""),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            closed_at=d.get("closed_at", ""),
            trust_summary=d.get("trust_summary", ""),
            readiness_status=d.get("readiness_status", ""),
            readiness_reason=d.get("readiness_reason", ""),
            bundle_id=d.get("bundle_id", ""),
        )
