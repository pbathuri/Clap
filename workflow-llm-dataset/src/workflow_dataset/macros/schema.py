"""
M23V/M23P: Macro schema. M23V: macro wraps routine 1:1. M23P: steps, checkpoints, stop conditions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# M23P: step types for classification (safe_inspect | sandbox_write | trusted_real | blocked | human_checkpoint)
STEP_TYPE_SAFE_INSPECT = "safe_inspect"
STEP_TYPE_SANDBOX_WRITE = "sandbox_write"
STEP_TYPE_TRUSTED_REAL = "trusted_real"
STEP_TYPE_BLOCKED = "blocked"
STEP_TYPE_HUMAN_CHECKPOINT = "human_checkpoint"


@dataclass
class MacroStep:
    """M23P: Single step in a macro with trust/approval/checkpoint metadata."""
    job_pack_id: str
    step_type: str = ""  # Filled by step_classifier; safe_inspect | sandbox_write | trusted_real | blocked | human_checkpoint
    trust_requirement: str = ""  # From job.trust_level
    approval_requirement: bool = False  # From job.required_approvals
    simulate_eligible: bool = True
    real_mode_eligible: bool = False
    checkpoint_before: bool = False  # If True, runner pauses before executing this step
    expected_outputs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_pack_id": self.job_pack_id,
            "step_type": self.step_type,
            "trust_requirement": self.trust_requirement,
            "approval_requirement": self.approval_requirement,
            "simulate_eligible": self.simulate_eligible,
            "real_mode_eligible": self.real_mode_eligible,
            "checkpoint_before": self.checkpoint_before,
            "expected_outputs": list(self.expected_outputs),
        }


@dataclass
class Macro:
    """Macro: named multi-step flow with optional routine binding. M23P: checkpoint markers, stop conditions."""
    macro_id: str
    title: str
    description: str = ""
    routine_id: str = ""  # When set, steps = get_ordered_job_ids(routine)
    job_pack_ids: list[str] = None  # When routine_id empty, explicit list
    steps: list[MacroStep] = None  # M23P: optional explicit steps (else derived from routine/job_pack_ids)
    mode: str = "simulate"  # simulate | real
    stop_on_first_blocked: bool = True
    required_approvals: list[str] = None
    simulate_only: bool = True
    # M23P: checkpoint and stop behavior
    checkpoint_after_step_indices: list[int] = None  # After running step at this index, pause for approval
    stop_conditions: list[str] = None  # Human-readable conditions that stop the macro (e.g. "user cancelled")
    expected_outputs: list[str] = None  # Macro-level expected outputs

    def __post_init__(self) -> None:
        if self.job_pack_ids is None:
            self.job_pack_ids = []
        if self.required_approvals is None:
            self.required_approvals = []
        if self.steps is None:
            self.steps = []
        if self.checkpoint_after_step_indices is None:
            self.checkpoint_after_step_indices = []
        if self.stop_conditions is None:
            self.stop_conditions = []
        if self.expected_outputs is None:
            self.expected_outputs = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "macro_id": self.macro_id,
            "title": self.title,
            "description": self.description,
            "routine_id": self.routine_id,
            "job_pack_ids": list(self.job_pack_ids),
            "steps": [s.to_dict() for s in self.steps],
            "mode": self.mode,
            "stop_on_first_blocked": self.stop_on_first_blocked,
            "required_approvals": list(self.required_approvals),
            "simulate_only": self.simulate_only,
            "checkpoint_after_step_indices": list(self.checkpoint_after_step_indices),
            "stop_conditions": list(self.stop_conditions),
            "expected_outputs": list(self.expected_outputs),
        }
