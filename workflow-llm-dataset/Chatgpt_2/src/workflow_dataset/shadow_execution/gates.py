"""
M45E–M45H Phase C: Intervention gates — must review, must stop, shadow only, bounded real, downgrade, handoff.
"""

from __future__ import annotations

from workflow_dataset.shadow_execution.models import (
    GateType,
    InterventionGate,
    GateFailureReason,
    SafeToContinueState,
    ForcedTakeoverState,
    ShadowRun,
    ConfidenceScore,
    RiskMarker,
)

CONFIDENCE_GATE_THRESHOLD = 0.4
RISK_GATE_HIGH = "high"


def evaluate_gates_for_run(run: ShadowRun) -> list[InterventionGate]:
    """Evaluate all intervention gates for a shadow run; append to run.gates (caller can assign)."""
    gates: list[InterventionGate] = []
    loop_conf = run.confidence_loop.score if run.confidence_loop else 0.0
    step_confs = [c.score for c in run.confidence_step]
    min_step_conf = min(step_confs) if step_confs else 0.0
    high_risk = any(r.level == RISK_GATE_HIGH for r in run.risk_markers)

    # must_review_next_step: lowest step confidence below threshold
    if step_confs and min_step_conf < CONFIDENCE_GATE_THRESHOLD:
        gates.append(InterventionGate(
            gate_type=GateType.MUST_REVIEW_NEXT_STEP.value,
            passed=False,
            failure_reason=GateFailureReason(
                gate_type=GateType.MUST_REVIEW_NEXT_STEP.value,
                reason="Step confidence below threshold",
                threshold_crossed="confidence",
            ),
            recommended_action="Review next step before continuing.",
        ))
    else:
        gates.append(InterventionGate(
            gate_type=GateType.MUST_REVIEW_NEXT_STEP.value,
            passed=True,
            recommended_action="Continue.",
        ))

    # must_stop_loop: loop confidence too low or high risk
    if loop_conf < CONFIDENCE_GATE_THRESHOLD or high_risk:
        gates.append(InterventionGate(
            gate_type=GateType.MUST_STOP_LOOP.value,
            passed=False,
            failure_reason=GateFailureReason(
                gate_type=GateType.MUST_STOP_LOOP.value,
                reason="Loop confidence low or high risk",
                threshold_crossed="confidence_or_risk",
            ),
            recommended_action="Stop loop; do not continue without review.",
        ))
    else:
        gates.append(InterventionGate(
            gate_type=GateType.MUST_STOP_LOOP.value,
            passed=True,
            recommended_action="Loop may continue in allowed mode.",
        ))

    # may_continue_shadow_only: always pass (shadow run is already shadow)
    gates.append(InterventionGate(
        gate_type=GateType.MAY_CONTINUE_SHADOW_ONLY.value,
        passed=True,
        recommended_action="Continue in shadow only.",
    ))

    # may_continue_bounded_real: pass only if loop confidence high and no high risk
    if loop_conf >= 0.75 and not high_risk:
        gates.append(InterventionGate(
            gate_type=GateType.MAY_CONTINUE_BOUNDED_REAL.value,
            passed=True,
            recommended_action="May promote to bounded real (still subject to approval).",
        ))
    else:
        gates.append(InterventionGate(
            gate_type=GateType.MAY_CONTINUE_BOUNDED_REAL.value,
            passed=False,
            failure_reason=GateFailureReason(
                gate_type=GateType.MAY_CONTINUE_BOUNDED_REAL.value,
                reason="Loop confidence or risk does not allow bounded real",
                threshold_crossed="confidence_or_risk",
            ),
            recommended_action="Do not promote to real without review.",
        ))

    # must_downgrade_profile: when degraded or low confidence
    if loop_conf < 0.5:
        gates.append(InterventionGate(
            gate_type=GateType.MUST_DOWNGRADE_PROFILE.value,
            passed=False,
            failure_reason=GateFailureReason(
                gate_type=GateType.MUST_DOWNGRADE_PROFILE.value,
                reason="Confidence too low for current profile",
                threshold_crossed="confidence",
            ),
            recommended_action="Use safer execution profile (e.g. simulate only).",
        ))
    else:
        gates.append(InterventionGate(
            gate_type=GateType.MUST_DOWNGRADE_PROFILE.value,
            passed=True,
            recommended_action="No downgrade required.",
        ))

    # must_handoff_human: when forced takeover
    if high_risk and loop_conf < CONFIDENCE_GATE_THRESHOLD:
        gates.append(InterventionGate(
            gate_type=GateType.MUST_HANDOFF_HUMAN.value,
            passed=False,
            failure_reason=GateFailureReason(
                gate_type=GateType.MUST_HANDOFF_HUMAN.value,
                reason="High risk and low confidence; hand off to human",
                threshold_crossed="risk_and_confidence",
            ),
            recommended_action="Hand off to human immediately.",
        ))
    else:
        gates.append(InterventionGate(
            gate_type=GateType.MUST_HANDOFF_HUMAN.value,
            passed=True,
            recommended_action="No handoff required.",
        ))

    return gates


def next_intervention_gate(run: ShadowRun) -> InterventionGate | None:
    """Return the next (first failed) intervention gate that requires action."""
    for g in run.gates:
        if not g.passed:
            return g
    return None


def should_force_takeover(run: ShadowRun) -> bool:
    """True when MUST_HANDOFF_HUMAN gate failed."""
    for g in run.gates:
        if g.gate_type == GateType.MUST_HANDOFF_HUMAN.value and not g.passed:
            return True
    return False


def compute_safe_to_continue(run: ShadowRun) -> SafeToContinueState:
    """Compute safe-to-continue state from gates."""
    next_gate = next_intervention_gate(run)
    if should_force_takeover(run):
        return SafeToContinueState(
            may_continue=False,
            mode_allowed="",
            next_gate_type=GateType.MUST_HANDOFF_HUMAN.value,
            conditions=["Takeover required"],
        )
    if next_gate and next_gate.gate_type == GateType.MUST_STOP_LOOP.value:
        return SafeToContinueState(
            may_continue=False,
            mode_allowed="shadow_only",
            next_gate_type=next_gate.gate_type,
            conditions=["Stop loop gate failed"],
        )
    mode = "shadow_only"
    for g in run.gates:
        if g.gate_type == GateType.MAY_CONTINUE_BOUNDED_REAL.value and g.passed:
            mode = "bounded_real"
            break
    return SafeToContinueState(
        may_continue=True,
        mode_allowed=mode,
        next_gate_type=next_gate.gate_type if next_gate else "",
        conditions=[],
    )


def compute_forced_takeover(run: ShadowRun) -> ForcedTakeoverState:
    """Compute forced-takeover state from gates."""
    if not should_force_takeover(run):
        return ForcedTakeoverState(forced=False)
    g = next(g for g in run.gates if g.gate_type == GateType.MUST_HANDOFF_HUMAN.value and not g.passed)
    reason = g.failure_reason.reason if g.failure_reason else "Handoff gate failed"
    return ForcedTakeoverState(
        forced=True,
        reason=reason,
        failed_gate_type=GateType.MUST_HANDOFF_HUMAN.value,
        handoff_summary=f"Shadow run {run.shadow_run_id}: {reason}. Review gate-report and resolve before continuing.",
    )
