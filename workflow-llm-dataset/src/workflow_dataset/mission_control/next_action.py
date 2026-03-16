"""
M22B: Next-action recommendation from current state. Grounded in local evidence; no auto-execute.
"""

from __future__ import annotations

from typing import Any

ACTIONS = ("build", "benchmark", "cohort_test", "promote", "hold", "rollback")


def recommend_next_action(state: dict[str, Any]) -> dict[str, Any]:
    """
    Return recommended next action: build | benchmark | cohort_test | promote | hold | rollback.
    rationale: one-line reason. detail: optional extra context.
    """
    product = state.get("product_state", {})
    evaluation = state.get("evaluation_state", {})
    development = state.get("development_state", {})
    incubator = state.get("incubator_state", {})

    # Rollback: eval recommends revert
    rec = evaluation.get("recommendation")
    if rec == "revert":
        return {
            "action": "rollback",
            "rationale": "Benchmark recommendation is revert; address regressions before proceeding.",
            "detail": f"Latest run: {evaluation.get('latest_run_id')}",
        }

    # Proposal queue: pending proposals need review (before promote)
    pending = development.get("pending_proposals", 0)
    if pending > 0:
        return {
            "action": "build",
            "rationale": "Pending patch proposals need operator review; apply or reject.",
            "detail": f"Pending: {pending}. Use devlab show-proposal and review-proposal.",
        }

    # Promote: incubator has candidates with no promoted yet
    inc_candidates = incubator.get("candidates_total", 0)
    if inc_candidates > 0:
        promoted = incubator.get("promoted_count", 0)
        if promoted == 0:
            return {
                "action": "promote",
                "rationale": "Incubator has candidates; run incubator evaluate then promote if gates pass.",
                "detail": f"Candidates: {inc_candidates}; promoted: {promoted}",
            }

    # Benchmark: run eval if no recent run or recommendation is refine/hold
    runs_count = evaluation.get("runs_count", 0)
    if runs_count == 0 or rec in ("hold", "refine"):
        return {
            "action": "benchmark",
            "rationale": "Run or re-run benchmark suite to refresh evaluation state.",
            "detail": "eval run-suite ops_reporting_core; then eval board.",
        }

    # Cohort test: pilot/cohort signal
    cohort_rec = product.get("cohort_recommendation") or ""
    if "expand" in cohort_rec.lower() or "test" in cohort_rec.lower():
        return {
            "action": "cohort_test",
            "rationale": "Cohort recommendation suggests expanding or testing; run pilot/cohort.",
            "detail": cohort_rec,
        }

    # Unreviewed workspaces
    unreviewed = (product.get("review_package") or {}).get("unreviewed_count", 0)
    if unreviewed > 0:
        return {
            "action": "build",
            "rationale": "Workspaces need review and package.",
            "detail": f"Unreviewed: {unreviewed}",
        }

    # Default: hold and review
    return {
        "action": "hold",
        "rationale": "No urgent signal; review mission-control state and choose next step.",
        "detail": "Consider: planner recommend-next, incubator list, or eval board.",
    }
