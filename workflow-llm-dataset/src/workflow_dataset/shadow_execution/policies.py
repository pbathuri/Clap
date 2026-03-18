"""
M45H.1: Confidence policies by loop type; rules for shadow-only vs limited-real promotion;
operator-facing promotion eligibility report.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.shadow_execution.models import ConfidencePolicy, PromotionEligibilityReport

LOOP_TYPES = ("routine", "job", "macro")
RISK_ORDER = ("low", "medium", "high")


def _risk_above(max_allowed: str, actual: str) -> bool:
    """True if actual risk is above max_allowed (e.g. actual=high, max_allowed=medium)."""
    try:
        return RISK_ORDER.index(actual) > RISK_ORDER.index(max_allowed)
    except (ValueError, KeyError):
        return actual == "high"


def _default_policy_for_loop_type(loop_type: str) -> ConfidencePolicy:
    """Built-in default policy for a loop type."""
    return ConfidencePolicy(
        policy_id=f"default_{loop_type}",
        loop_type=loop_type,
        label=f"Default confidence policy for {loop_type}",
        min_loop_confidence_for_bounded_real=0.75,
        max_risk_level_for_bounded_real="medium",
        require_min_step_confidence=0.4,
        allow_high_risk=False,
        operator_summary_shadow_only=f"Loop type '{loop_type}' remains shadow-only: confidence or risk does not meet policy for bounded real execution. Review gate-report and confidence; fix issues or accept shadow-only.",
        operator_summary_eligible=f"Loop type '{loop_type}' meets policy: eligible for bounded real execution (still subject to approval). Use promotion flow if desired.",
    )


BUILTIN_POLICIES: list[ConfidencePolicy] = [
    _default_policy_for_loop_type("routine"),
    _default_policy_for_loop_type("job"),
    _default_policy_for_loop_type("macro"),
]


def get_policy_for_loop_type(
    loop_type: str,
    repo_root: Path | str | None = None,
) -> ConfidencePolicy:
    """Return the confidence policy for this loop type (from store overlay or built-in)."""
    try:
        from workflow_dataset.shadow_execution.policy_store import load_policies
        policies = load_policies(repo_root=repo_root)
        for p in policies:
            if p.get("loop_type") == loop_type:
                return _policy_from_dict(p)
    except Exception:
        pass
    for p in BUILTIN_POLICIES:
        if p.loop_type == loop_type:
            return p
    return _default_policy_for_loop_type(loop_type or "job")


def _policy_from_dict(d: dict[str, Any]) -> ConfidencePolicy:
    return ConfidencePolicy(
        policy_id=d.get("policy_id", ""),
        loop_type=d.get("loop_type", ""),
        label=d.get("label", ""),
        min_loop_confidence_for_bounded_real=float(d.get("min_loop_confidence_for_bounded_real", 0.75)),
        max_risk_level_for_bounded_real=str(d.get("max_risk_level_for_bounded_real", "medium")),
        require_min_step_confidence=float(d.get("require_min_step_confidence", 0.4)),
        allow_high_risk=bool(d.get("allow_high_risk", False)),
        operator_summary_shadow_only=str(d.get("operator_summary_shadow_only", "")),
        operator_summary_eligible=str(d.get("operator_summary_eligible", "")),
    )


def evaluate_promotion_eligibility(
    run_dict: dict[str, Any],
    policy: ConfidencePolicy | None = None,
) -> PromotionEligibilityReport:
    """
    Evaluate whether a shadow run is eligible for bounded real promotion under the given policy.
    Returns operator-facing report with reason_shadow_only / reason_eligible.
    """
    shadow_run_id = run_dict.get("shadow_run_id", "")
    loop_type = run_dict.get("loop_type", "job")
    if policy is None:
        policy = get_policy_for_loop_type(loop_type)

    reason_shadow_only: list[str] = []
    reason_eligible: list[str] = []
    details: dict[str, Any] = {}

    loop_conf = 0.0
    if run_dict.get("confidence_loop"):
        loop_conf = float(run_dict["confidence_loop"].get("score", 0))
    details["loop_confidence"] = loop_conf

    step_scores = [s.get("score", 0) for s in run_dict.get("confidence_step", [])]
    min_step_conf = min(step_scores) if step_scores else 0.0
    details["min_step_confidence"] = min_step_conf

    high_risk = False
    for r in run_dict.get("risk_markers", []):
        if r.get("level") == "high":
            high_risk = True
            break
    details["has_high_risk"] = high_risk

    if run_dict.get("forced_takeover", {}).get("forced"):
        reason_shadow_only.append("Forced takeover is set; run must not be promoted.")
        eligible = False
    else:
        eligible = True
        if loop_conf < policy.min_loop_confidence_for_bounded_real:
            reason_shadow_only.append(
                f"Loop confidence {loop_conf:.2f} is below policy minimum {policy.min_loop_confidence_for_bounded_real} for bounded real."
            )
            eligible = False
        else:
            reason_eligible.append(f"Loop confidence {loop_conf:.2f} meets policy minimum.")

        if min_step_conf < policy.require_min_step_confidence:
            reason_shadow_only.append(
                f"Lowest step confidence {min_step_conf:.2f} is below policy requirement {policy.require_min_step_confidence}."
            )
            eligible = False
        else:
            reason_eligible.append(f"All step confidences meet policy requirement.")

        if high_risk and not policy.allow_high_risk:
            reason_shadow_only.append("High risk marker present; policy does not allow high risk for bounded real.")
            eligible = False
        elif high_risk and policy.allow_high_risk:
            reason_eligible.append("High risk allowed by policy for this loop type.")
        elif not high_risk:
            reason_eligible.append("No high risk; within policy risk limit.")

    if eligible:
        operator_summary = policy.operator_summary_eligible or f"Eligible for bounded real. {', '.join(reason_eligible)}"
    else:
        operator_summary = policy.operator_summary_shadow_only or f"Remains shadow-only. {' '.join(reason_shadow_only)}"

    return PromotionEligibilityReport(
        shadow_run_id=shadow_run_id,
        eligible_for_bounded_real=eligible,
        reason_shadow_only=reason_shadow_only,
        reason_eligible=reason_eligible,
        applied_policy_id=policy.policy_id,
        applied_policy_label=policy.label,
        operator_summary=operator_summary,
        details=details,
    )


def build_promotion_eligibility_report(
    shadow_run_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Load shadow run, get policy for its loop type, evaluate promotion eligibility; return report as dict."""
    from workflow_dataset.shadow_execution.store import load_shadow_run
    run_dict = load_shadow_run(shadow_run_id, repo_root=repo_root)
    if not run_dict:
        return {
            "shadow_run_id": shadow_run_id,
            "error": "Shadow run not found",
            "eligible_for_bounded_real": False,
            "operator_summary": "Run not found.",
        }
    policy = get_policy_for_loop_type(run_dict.get("loop_type", "job"), repo_root=repo_root)
    report = evaluate_promotion_eligibility(run_dict, policy)
    return report.to_dict()
