"""
Assist escalation tiers for real-time workflow (M33G).

Bounded tiers: hint → action-card → draft → planner prefill → simulated handoff → review.
All explicit and supervised; no auto-escalation without user/policy.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.live_workflow.models import (
    EscalationTier,
    LiveStepSuggestion,
    SupervisedLiveWorkflow,
    EscalationExplanation,
)


# Ordered escalation tiers (low to high friction)
_ESCALATION_ORDER: list[EscalationTier] = [
    EscalationTier.HINT_ONLY,
    EscalationTier.ACTION_CARD_SUGGESTION,
    EscalationTier.DRAFT_HANDOFF_PREP,
    EscalationTier.PLANNER_GOAL_PREFILL,
    EscalationTier.SIMULATED_EXECUTION_HANDOFF,
    EscalationTier.REVIEW_APPROVAL_ROUTING,
]


def get_escalation_tiers() -> list[EscalationTier]:
    """Return ordered list of escalation tiers (hint → … → review)."""
    return list(_ESCALATION_ORDER)


def next_escalation_tier(current: EscalationTier) -> EscalationTier | None:
    """Return the next tier after current, or None if at top."""
    try:
        i = _ESCALATION_ORDER.index(current)
        if i + 1 < len(_ESCALATION_ORDER):
            return _ESCALATION_ORDER[i + 1]
    except ValueError:
        return _ESCALATION_ORDER[0] if _ESCALATION_ORDER else None
    return None


def build_handoff_for_tier(
    tier: EscalationTier,
    step: LiveStepSuggestion,
    run: SupervisedLiveWorkflow,
) -> dict[str, Any]:
    """
    Build handoff params for the given tier, step, and run. Aligned with
    HandoffTarget and execute_handoff. Keys: handoff_target (str), handoff_params (dict).
    """
    goal = run.goal_text or run.plan_ref
    plan_ref = run.plan_ref
    plan_source = run.plan_source or "goal"
    label = step.label or f"Step {step.step_index}"
    hint = step.hint_text or label

    if tier == EscalationTier.HINT_ONLY:
        return {
            "handoff_target": "",
            "handoff_params": {"hint": hint, "step_index": step.step_index},
        }
    if tier == EscalationTier.ACTION_CARD_SUGGESTION:
        return {
            "handoff_target": "prefill_command",
            "handoff_params": {
                "command": f"workflow-dataset live-workflow steps --latest",
                "goal": goal,
                "hint": hint,
                "step_label": label,
                "run_id": run.run_id,
            },
        }
    if tier == EscalationTier.DRAFT_HANDOFF_PREP:
        return {
            "handoff_target": "create_draft",
            "handoff_params": {
                "label": label,
                "plan_ref": plan_ref,
                "step_index": step.step_index,
                "run_id": run.run_id,
                "expected_artifact": (step.expected_handoff.label if step.expected_handoff else "") or "",
            },
        }
    if tier == EscalationTier.PLANNER_GOAL_PREFILL:
        return {
            "handoff_target": "compile_plan",
            "handoff_params": {
                "goal": goal,
                "plan_ref": plan_ref,
                "mode": "simulate",
                "step_label": label,
                "run_id": run.run_id,
            },
        }
    if tier == EscalationTier.SIMULATED_EXECUTION_HANDOFF:
        return {
            "handoff_target": "queue_simulated",
            "handoff_params": {
                "plan_ref": plan_ref,
                "plan_source": plan_source,
                "run_id": run.run_id,
                "step_index": step.step_index,
                "label": label,
            },
        }
    if tier == EscalationTier.REVIEW_APPROVAL_ROUTING:
        return {
            "handoff_target": "approval_studio",
            "handoff_params": {
                "run_id": run.run_id,
                "step_index": step.step_index,
                "label": label,
                "reason": "live_workflow_escalation",
            },
        }
    return {
        "handoff_target": "",
        "handoff_params": {"hint": hint, "step_index": step.step_index},
    }


def build_escalation_explanation(
    from_tier: EscalationTier,
    to_tier: EscalationTier,
    reason_code: str = "user_requested",
    step_label: str = "",
    run_id: str = "",
    context: dict[str, Any] | None = None,
) -> EscalationExplanation:
    """
    Build operator-facing explanation of why escalation happened.
    reason_code: user_requested | stall_detected | blocked_step | repeated_hint_dismissed
    """
    context = context or {}
    messages = {
        "user_requested": "You asked for stronger help than a hint.",
        "stall_detected": "No progress was detected for a while; escalating can unblock you with an action or plan.",
        "blocked_step": "This step is blocked (e.g. by policy); escalation routes you to approval or planner.",
        "repeated_hint_dismissed": "Hints were dismissed; escalation offers a concrete action or handoff.",
    }
    operator_message = messages.get(reason_code) or f"Escalating from {from_tier.value} to {to_tier.value}."
    if step_label:
        operator_message = f"Step: {step_label}. {operator_message}"

    suggested = {
        EscalationTier.ACTION_CARD_SUGGESTION: "Review the suggested action card and run or dismiss it.",
        EscalationTier.DRAFT_HANDOFF_PREP: "A draft or handoff can be prepared for this step.",
        EscalationTier.PLANNER_GOAL_PREFILL: "Planner will open with the current goal; you can edit and recompile.",
        EscalationTier.SIMULATED_EXECUTION_HANDOFF: "A simulated run can be queued; approve in agent-loop to run.",
        EscalationTier.REVIEW_APPROVAL_ROUTING: "You'll be routed to approval studio to resolve blocks or approve.",
    }
    suggested_action = suggested.get(to_tier) or f"Use the {to_tier.value} handoff as shown."

    return EscalationExplanation(
        from_tier=from_tier.value,
        to_tier=to_tier.value,
        reason_code=reason_code,
        operator_message=operator_message,
        suggested_action=suggested_action,
    )


def explain_escalation(
    from_tier: EscalationTier,
    to_tier: EscalationTier,
    reason_code: str = "user_requested",
    step_label: str = "",
    run_id: str = "",
) -> EscalationExplanation:
    """
    Return operator-facing explanation of why escalation happened.
    reason_code: user_requested | stall_detected | blocked_step | repeated_hint_dismissed
    """
    return build_escalation_explanation(
        from_tier=from_tier,
        to_tier=to_tier,
        reason_code=reason_code,
        step_label=step_label,
        run_id=run_id,
    )
