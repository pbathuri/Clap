"""
M26E–M26H: Safe action runtime — execution envelope and run state models.
Explicit, inspectable; no bypass of trust/approval.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ActionEnvelope:
    """Explicit execution envelope for one step: id, type, mode, approvals, capability, artifact, reversible, checkpoint, blocked reason."""

    step_id: str = ""
    step_index: int = 0
    action_type: str = ""  # job_run | adapter_action | macro_step
    action_ref: str = ""  # job_pack_id, adapter_id:action_id, macro_id
    mode: str = ""  # simulate | trusted_real_candidate
    approvals_required: list[str] = field(default_factory=list)
    capability_required: str = ""
    expected_artifact: str = ""
    reversible: bool = False
    checkpoint_required: bool = False
    blocked_reason: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    label: str = ""


@dataclass
class CheckpointDecision:
    """Human checkpoint decision: proceed / cancel / defer."""

    run_id: str = ""
    step_index: int = 0
    decision: str = ""  # proceed | cancel | defer
    timestamp: str = ""
    note: str = ""


@dataclass
class BlockedStepRecovery:
    """M26H.1: Human-in-the-loop recovery for a blocked step: retry, skip, substitute, or record_correction."""

    step_index: int = 0
    decision: str = ""  # retry | skip | substitute | record_correction
    substitute_bundle_id: str = ""   # when decision=substitute
    substitute_action_ref: str = ""  # job_pack_id or adapter_id:action_id when decision=substitute (single step)
    note: str = ""
    timestamp: str = ""


@dataclass
class ExecutionRun:
    """One execution run: plan ref, mode, status, steps, executed, blocked, artifacts, checkpoints."""

    run_id: str = ""
    plan_id: str = ""
    plan_source: str = ""  # routine | job | plan_file
    plan_ref: str = ""  # macro_id, job_pack_id, or path
    mode: str = ""
    status: str = ""  # running | paused | awaiting_approval | blocked | completed | cancelled
    current_step_index: int = 0
    envelopes: list[ActionEnvelope] = field(default_factory=list)
    executed: list[dict[str, Any]] = field(default_factory=list)
    blocked: list[dict[str, Any]] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    checkpoint_decisions: list[CheckpointDecision] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    run_path: str = ""
    timestamp_start: str = ""
    timestamp_end: str = ""
    approval_required_before_step: int | None = None
    recovery_decisions: list[BlockedStepRecovery] = field(default_factory=list)  # M26H.1

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "plan_id": self.plan_id,
            "plan_source": self.plan_source,
            "plan_ref": self.plan_ref,
            "mode": self.mode,
            "status": self.status,
            "current_step_index": self.current_step_index,
            "envelopes": [
                {
                    "step_id": e.step_id,
                    "step_index": e.step_index,
                    "action_type": e.action_type,
                    "action_ref": e.action_ref,
                    "mode": e.mode,
                    "approvals_required": list(e.approvals_required),
                    "checkpoint_required": e.checkpoint_required,
                    "blocked_reason": e.blocked_reason,
                    "label": e.label,
                }
                for e in self.envelopes
            ],
            "executed": list(self.executed),
            "blocked": list(self.blocked),
            "artifacts": list(self.artifacts),
            "checkpoint_decisions": [
                {"step_index": c.step_index, "decision": c.decision, "timestamp": c.timestamp}
                for c in self.checkpoint_decisions
            ],
            "errors": list(self.errors),
            "run_path": self.run_path,
            "timestamp_start": self.timestamp_start,
            "timestamp_end": self.timestamp_end,
            "approval_required_before_step": self.approval_required_before_step,
            "recovery_decisions": [
                {
                    "step_index": r.step_index,
                    "decision": r.decision,
                    "substitute_bundle_id": r.substitute_bundle_id,
                    "substitute_action_ref": r.substitute_action_ref,
                    "note": r.note,
                    "timestamp": r.timestamp,
                }
                for r in self.recovery_decisions
            ],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ExecutionRun":
        envelopes = []
        for e in d.get("envelopes", []):
            envelopes.append(ActionEnvelope(
                step_id=e.get("step_id", ""),
                step_index=int(e.get("step_index", 0)),
                action_type=e.get("action_type", ""),
                action_ref=e.get("action_ref", ""),
                mode=e.get("mode", ""),
                approvals_required=list(e.get("approvals_required", [])),
                checkpoint_required=bool(e.get("checkpoint_required", False)),
                blocked_reason=e.get("blocked_reason", ""),
                label=e.get("label", ""),
            ))
        decisions = []
        for c in d.get("checkpoint_decisions", []):
            decisions.append(CheckpointDecision(
                step_index=int(c.get("step_index", 0)),
                decision=c.get("decision", ""),
                timestamp=c.get("timestamp", ""),
            ))
        recoveries = []
        for r in d.get("recovery_decisions", []):
            recoveries.append(BlockedStepRecovery(
                step_index=int(r.get("step_index", 0)),
                decision=r.get("decision", ""),
                substitute_bundle_id=r.get("substitute_bundle_id", ""),
                substitute_action_ref=r.get("substitute_action_ref", ""),
                note=r.get("note", ""),
                timestamp=r.get("timestamp", ""),
            ))
        return cls(
            run_id=d.get("run_id", ""),
            plan_id=d.get("plan_id", ""),
            plan_source=d.get("plan_source", ""),
            plan_ref=d.get("plan_ref", ""),
            mode=d.get("mode", ""),
            status=d.get("status", ""),
            current_step_index=int(d.get("current_step_index", 0)),
            envelopes=envelopes,
            executed=list(d.get("executed", [])),
            blocked=list(d.get("blocked", [])),
            artifacts=list(d.get("artifacts", [])),
            checkpoint_decisions=decisions,
            errors=list(d.get("errors", [])),
            run_path=d.get("run_path", ""),
            timestamp_start=d.get("timestamp_start", ""),
            timestamp_end=d.get("timestamp_end", ""),
            approval_required_before_step=d.get("approval_required_before_step"),
            recovery_decisions=recoveries,
        )
