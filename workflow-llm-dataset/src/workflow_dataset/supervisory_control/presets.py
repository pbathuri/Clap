"""
M45L.1: Default supervision presets (conservative, balanced, operator-heavy) and takeover playbooks.
"""

from __future__ import annotations

from workflow_dataset.supervisory_control.models import SupervisionPreset, TakeoverPlaybook

# ----- Built-in supervision presets -----
PRESET_CONSERVATIVE = "conservative"
PRESET_BALANCED = "balanced"
PRESET_OPERATOR_HEAVY = "operator_heavy"

DEFAULT_SUPERVISION_PRESETS: list[SupervisionPreset] = [
    SupervisionPreset(
        preset_id=PRESET_CONSERVATIVE,
        label="Conservative",
        description="Pause on blocked; require approval before any real execution; escalate when pending queue grows.",
        auto_pause_on_blocked=True,
        require_approval_before_real=True,
        max_pending_before_escalation=3,
        suggest_takeover_on_repeated_failure=True,
        repeated_failure_count=2,
        when_to_continue_hint="Continue when the loop is not blocked, pending count is low, and you have approved the next real step.",
        when_to_intervene_hint="Intervene (pause or redirect) when the loop is blocked, pending queue is large, or a handoff failed.",
        when_to_terminate_hint="Terminate when the goal is obsolete, repeated failures with no progress, or you need to reassign the work.",
    ),
    SupervisionPreset(
        preset_id=PRESET_BALANCED,
        label="Balanced",
        description="Suggest pause on blocked; require approval for real; suggest takeover after several failures.",
        auto_pause_on_blocked=False,
        require_approval_before_real=True,
        max_pending_before_escalation=5,
        suggest_takeover_on_repeated_failure=True,
        repeated_failure_count=3,
        when_to_continue_hint="Continue when the loop is making progress and you are comfortable with the next proposed action.",
        when_to_intervene_hint="Intervene when the loop is stuck, confidence is low, or you want to redirect the next step.",
        when_to_terminate_hint="Terminate when the loop is no longer aligned with current priorities or cannot make progress.",
    ),
    SupervisionPreset(
        preset_id=PRESET_OPERATOR_HEAVY,
        label="Operator-heavy",
        description="Operator drives; minimal auto-continuation; take over early on uncertainty.",
        auto_pause_on_blocked=True,
        require_approval_before_real=True,
        max_pending_before_escalation=1,
        suggest_takeover_on_repeated_failure=True,
        repeated_failure_count=1,
        when_to_continue_hint="Continue only after you have reviewed and approved the next step; prefer explicit handback after takeover.",
        when_to_intervene_hint="Intervene early when in doubt; pause to review or take over to complete manually.",
        when_to_terminate_hint="Terminate when you prefer to handle the goal outside the loop or restart with a different plan.",
    ),
]

# ----- Built-in takeover playbooks -----
PLAYBOOK_BLOCKED_NO_PROGRESS = "blocked_no_progress"
PLAYBOOK_REPEATED_HANDOFF_FAILURE = "repeated_handoff_failure"
PLAYBOOK_PENDING_STALE = "pending_stale"
PLAYBOOK_HIGH_RISK_PENDING = "high_risk_pending"

DEFAULT_TAKEOVER_PLAYBOOKS: list[TakeoverPlaybook] = [
    TakeoverPlaybook(
        playbook_id=PLAYBOOK_BLOCKED_NO_PROGRESS,
        label="Blocked with no progress",
        trigger_condition="blocked_no_progress",
        description="Loop is blocked and not advancing; cycle status blocked or handoff failed.",
        suggested_actions=[
            "Pause and inspect: supervision show --id <loop_id>",
            "Review blocked_reason and next proposed action",
            "Redirect with a different next step, or take over to complete manually",
        ],
        when_to_continue="Continue only if you have unblocked the loop (e.g. by approving a different action or resolving the blocker).",
        when_to_intervene="Intervene now: pause, then redirect or takeover. Do not let the loop retry the same failing step.",
        when_to_terminate="Terminate if the goal cannot be achieved with the current plan or the blocker is permanent.",
    ),
    TakeoverPlaybook(
        playbook_id=PLAYBOOK_REPEATED_HANDOFF_FAILURE,
        label="Repeated handoff failure",
        trigger_condition="repeated_handoff_failure",
        description="Multiple handoffs have failed or produced errors; loop may be stuck.",
        suggested_actions=[
            "Pause the loop: supervision pause --id <loop_id>",
            "Review recent interventions: supervision show --id <loop_id>",
            "Take over to complete the step manually, or redirect to simulate first",
            "Hand back only after verifying the next step is safe",
        ],
        when_to_continue="Continue only after the underlying failure is fixed (e.g. executor or plan corrected) and you have verified one successful step.",
        when_to_intervene="Intervene: pause and consider takeover. Avoid auto-resume until you have reviewed the failure cause.",
        when_to_terminate="Terminate if the same failure persists after redirect or manual fix, or the plan is invalid.",
    ),
    TakeoverPlaybook(
        playbook_id=PLAYBOOK_PENDING_STALE,
        label="Pending queue stale",
        trigger_condition="pending_stale",
        description="Many items in pending queue or pending has been waiting too long without approval.",
        suggested_actions=[
            "Review queue: agent-loop queue (or equivalent)",
            "Approve or reject pending items, or pause and redirect",
            "If overloaded, pause and process in batches",
        ],
        when_to_continue="Continue when the pending queue is manageable and you have approved the next action.",
        when_to_intervene="Intervene when pending count exceeds your comfort level or items have been waiting too long.",
        when_to_terminate="Terminate if the queue is obsolete or you want to clear and restart.",
    ),
    TakeoverPlaybook(
        playbook_id=PLAYBOOK_HIGH_RISK_PENDING,
        label="High-risk pending action",
        trigger_condition="high_risk_pending",
        description="Next proposed action is high risk (e.g. real execution, sensitive path).",
        suggested_actions=[
            "Review the proposed action and risk level",
            "Approve only if you have verified the action is safe, or redirect to simulate",
            "Consider takeover if you prefer to run the step yourself",
        ],
        when_to_continue="Continue only after explicit approval of the high-risk action; do not batch-approve.",
        when_to_intervene="Intervene: do not auto-approve. Pause to review, or redirect to simulate first.",
        when_to_terminate="Terminate if the action is not acceptable and there is no safe alternative.",
    ),
]


def get_default_presets() -> list[SupervisionPreset]:
    return list(DEFAULT_SUPERVISION_PRESETS)


def get_default_playbooks() -> list[TakeoverPlaybook]:
    return list(DEFAULT_TAKEOVER_PLAYBOOKS)


def get_preset_by_id(preset_id: str) -> SupervisionPreset | None:
    for p in DEFAULT_SUPERVISION_PRESETS:
        if p.preset_id == preset_id:
            return p
    return None


def get_playbook_by_id(playbook_id: str) -> TakeoverPlaybook | None:
    for pb in DEFAULT_TAKEOVER_PLAYBOOKS:
        if pb.playbook_id == playbook_id:
            return pb
    return None


def get_playbooks_for_trigger(trigger_condition: str) -> list[TakeoverPlaybook]:
    return [pb for pb in DEFAULT_TAKEOVER_PLAYBOOKS if pb.trigger_condition == trigger_condition]
