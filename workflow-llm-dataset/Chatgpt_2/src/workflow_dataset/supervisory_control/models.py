"""
M45I–M45L Phase A: Supervisory control models — loop view, intervention, pause, redirect, takeover, handback, rationale, audit note.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Loop view status (supervisory layer)
LOOP_VIEW_ACTIVE = "active"
LOOP_VIEW_PAUSED = "paused"
LOOP_VIEW_TAKEN_OVER = "taken_over"
LOOP_VIEW_AWAITING_CONTINUATION = "awaiting_continuation"
LOOP_VIEW_STOPPED = "stopped"

# Intervention kinds
INTERVENTION_PAUSE = "pause"
INTERVENTION_STOP = "stop"
INTERVENTION_TAKEOVER = "takeover"
INTERVENTION_REDIRECT = "redirect"
INTERVENTION_APPROVE_CONTINUATION = "approve_continuation"
INTERVENTION_HANDBACK = "handback"


@dataclass
class SupervisedLoopView:
    """Unified view of a supervised loop for the control panel."""
    loop_id: str = ""
    label: str = ""
    status: str = LOOP_VIEW_ACTIVE  # active | paused | taken_over | awaiting_continuation | stopped
    project_slug: str = ""
    goal_text: str = ""
    cycle_id: str = ""  # ref to supervised_loop AgentCycle
    pending_count: int = 0
    last_activity_utc: str = ""
    created_at_utc: str = ""
    updated_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "loop_id": self.loop_id,
            "label": self.label,
            "status": self.status,
            "project_slug": self.project_slug,
            "goal_text": self.goal_text,
            "cycle_id": self.cycle_id,
            "pending_count": self.pending_count,
            "last_activity_utc": self.last_activity_utc,
            "created_at_utc": self.created_at_utc,
            "updated_at_utc": self.updated_at_utc,
        }


@dataclass
class OperatorIntervention:
    """Record of one operator intervention on a loop."""
    intervention_id: str = ""
    loop_id: str = ""
    kind: str = ""  # pause | stop | takeover | redirect | approve_continuation | handback
    created_at_utc: str = ""
    operator_id: str = ""
    rationale_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)  # reason, next_step_hint, etc.

    def to_dict(self) -> dict[str, Any]:
        return {
            "intervention_id": self.intervention_id,
            "loop_id": self.loop_id,
            "kind": self.kind,
            "created_at_utc": self.created_at_utc,
            "operator_id": self.operator_id,
            "rationale_id": self.rationale_id,
            "payload": dict(self.payload),
        }


@dataclass
class PauseState:
    """Loop-level pause: this loop is paused until resumed."""
    loop_id: str = ""
    paused_at_utc: str = ""
    reason: str = ""
    resumed_at_utc: str = ""  # set when resumed

    def to_dict(self) -> dict[str, Any]:
        return {
            "loop_id": self.loop_id,
            "paused_at_utc": self.paused_at_utc,
            "reason": self.reason,
            "resumed_at_utc": self.resumed_at_utc,
        }


@dataclass
class RedirectState:
    """Redirect next step for the loop (advisory)."""
    loop_id: str = ""
    redirect_at_utc: str = ""
    next_step_hint: str = ""
    applied: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "loop_id": self.loop_id,
            "redirect_at_utc": self.redirect_at_utc,
            "next_step_hint": self.next_step_hint,
            "applied": self.applied,
        }


@dataclass
class TakeoverState:
    """Loop is under manual operator control."""
    loop_id: str = ""
    taken_over_at_utc: str = ""
    operator_note: str = ""
    returned_at_utc: str = ""  # empty if still taken over

    def to_dict(self) -> dict[str, Any]:
        return {
            "loop_id": self.loop_id,
            "taken_over_at_utc": self.taken_over_at_utc,
            "operator_note": self.operator_note,
            "returned_at_utc": self.returned_at_utc,
        }


@dataclass
class HandbackState:
    """Record of returning loop to supervised mode."""
    loop_id: str = ""
    handback_at_utc: str = ""
    handback_note: str = ""
    safe_to_resume: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "loop_id": self.loop_id,
            "handback_at_utc": self.handback_at_utc,
            "handback_note": self.handback_note,
            "safe_to_resume": self.safe_to_resume,
        }


@dataclass
class OperatorRationale:
    """Operator-provided reason attached to an intervention or loop."""
    rationale_id: str = ""
    text: str = ""
    created_at_utc: str = ""
    attached_to_intervention_id: str = ""
    attached_to_loop_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "rationale_id": self.rationale_id,
            "text": self.text,
            "created_at_utc": self.created_at_utc,
            "attached_to_intervention_id": self.attached_to_intervention_id,
            "attached_to_loop_id": self.attached_to_loop_id,
        }


@dataclass
class LoopControlAuditNote:
    """Immutable audit note for a loop or intervention."""
    note_id: str = ""
    loop_id: str = ""
    intervention_id: str = ""
    created_at_utc: str = ""
    note_text: str = ""
    kind: str = ""  # rationale | audit | gate_status

    def to_dict(self) -> dict[str, Any]:
        return {
            "note_id": self.note_id,
            "loop_id": self.loop_id,
            "intervention_id": self.intervention_id,
            "created_at_utc": self.created_at_utc,
            "note_text": self.note_text,
            "kind": self.kind,
        }


# ----- M45L.1: Supervision presets + takeover playbooks -----


@dataclass
class SupervisionPreset:
    """Preset for supervisory stance: conservative, balanced, operator-heavy."""
    preset_id: str = ""
    label: str = ""
    description: str = ""
    auto_pause_on_blocked: bool = False  # pause loop when cycle is blocked
    require_approval_before_real: bool = True  # always require approval before real execution
    max_pending_before_escalation: int = 0  # 0 = no auto-escalation; >0 suggest review when pending >= N
    suggest_takeover_on_repeated_failure: bool = False  # after N handoff failures suggest takeover
    repeated_failure_count: int = 3
    when_to_continue_hint: str = ""  # operator-facing: when it's safe to let the loop continue
    when_to_intervene_hint: str = ""  # when to pause/redirect/takeover
    when_to_terminate_hint: str = ""  # when to stop the loop

    def to_dict(self) -> dict[str, Any]:
        return {
            "preset_id": self.preset_id,
            "label": self.label,
            "description": self.description,
            "auto_pause_on_blocked": self.auto_pause_on_blocked,
            "require_approval_before_real": self.require_approval_before_real,
            "max_pending_before_escalation": self.max_pending_before_escalation,
            "suggest_takeover_on_repeated_failure": self.suggest_takeover_on_repeated_failure,
            "repeated_failure_count": self.repeated_failure_count,
            "when_to_continue_hint": self.when_to_continue_hint,
            "when_to_intervene_hint": self.when_to_intervene_hint,
            "when_to_terminate_hint": self.when_to_terminate_hint,
        }


@dataclass
class TakeoverPlaybook:
    """Playbook for common loop failures: trigger condition and suggested actions."""
    playbook_id: str = ""
    label: str = ""
    trigger_condition: str = ""  # e.g. blocked_no_progress | repeated_handoff_failure | pending_stale | high_risk_pending
    description: str = ""
    suggested_actions: list[str] = field(default_factory=list)  # e.g. "Pause and review queue", "Redirect to simulate"
    when_to_continue: str = ""  # operator-facing: when continuing is appropriate
    when_to_intervene: str = ""  # when to use this playbook (intervene)
    when_to_terminate: str = ""  # when to stop instead of retry

    def to_dict(self) -> dict[str, Any]:
        return {
            "playbook_id": self.playbook_id,
            "label": self.label,
            "trigger_condition": self.trigger_condition,
            "description": self.description,
            "suggested_actions": list(self.suggested_actions),
            "when_to_continue": self.when_to_continue,
            "when_to_intervene": self.when_to_intervene,
            "when_to_terminate": self.when_to_terminate,
        }


@dataclass
class OperatorLoopSummary:
    """Operator-facing summary: when to continue, intervene, or terminate; suggested playbook."""
    loop_id: str = ""
    continue_recommendation: str = ""
    intervene_recommendation: str = ""
    terminate_recommendation: str = ""
    suggested_playbook_id: str = ""
    suggested_playbook_label: str = ""
    preset_id: str = ""
    created_at_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "loop_id": self.loop_id,
            "continue_recommendation": self.continue_recommendation,
            "intervene_recommendation": self.intervene_recommendation,
            "terminate_recommendation": self.terminate_recommendation,
            "suggested_playbook_id": self.suggested_playbook_id,
            "suggested_playbook_label": self.suggested_playbook_label,
            "preset_id": self.preset_id,
            "created_at_utc": self.created_at_utc,
        }
