"""
M42I–M42L: Build promotion-ready scorecard from comparison result; record disagreements.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from workflow_dataset.benchmark_board.models import (
    Scorecard,
    ComparisonDimension,
    BenchmarkDisagreementNote,
    PromotionRecommendation,
    RollbackRecommendation,
    DEFAULT_COMPARISON_DIMENSIONS,
    DIMENSION_TASK_SUCCESS,
)
from workflow_dataset.utils.hashes import stable_id


def build_scorecard(
    comparison_result: dict[str, Any],
    baseline_id: str = "",
    candidate_id: str = "",
    slice_ids: list[str] | None = None,
    memory_slice_ids: list[str] | None = None,
    scorecard_id: str = "",
) -> Scorecard:
    """
    Build compact promotion-ready scorecard from eval compare_runs result.
    Maps regressions/improvements/recommendation to dimensions and promotion/rollback recommendations.
    """
    baseline_id = baseline_id or comparison_result.get("baseline_id", "")
    candidate_id = candidate_id or comparison_result.get("candidate_id", "")
    slice_ids = slice_ids or comparison_result.get("slice_ids", [])
    memory_slice_ids = memory_slice_ids or comparison_result.get("memory_slice_ids", [])
    rec = comparison_result.get("recommendation", "hold")
    th_pass = comparison_result.get("thresholds_passed", False)
    regressions = list(comparison_result.get("regressions", []))
    improvements = list(comparison_result.get("improvements", []))
    run_a_ts = comparison_result.get("run_a_timestamp", "")
    run_b_ts = comparison_result.get("run_b_timestamp", "")

    # Task success from overall score comparison (eval uses run total score)
    sa = comparison_result.get("run_a_score")
    sb = comparison_result.get("run_b_score")
    if sa is None or sb is None:
        sa = 0.0
        sb = 0.0
    task_score = (sb - sa + 1.0) / 2.0 if (sa != sb) else 0.5
    task_score = max(0.0, min(1.0, task_score))

    dimensions: list[ComparisonDimension] = []
    for dim_id in DEFAULT_COMPARISON_DIMENSIONS:
        if dim_id == DIMENSION_TASK_SUCCESS:
            dimensions.append(ComparisonDimension(
                dimension_id=dim_id,
                score=task_score,
                pass_threshold=th_pass and rec in ("promote", "hold"),
                detail=f"baseline vs candidate score delta",
                baseline_value=sa,
                candidate_value=sb,
            ))
        else:
            # Placeholder for other dimensions (council or future eval fields)
            dimensions.append(ComparisonDimension(
                dimension_id=dim_id,
                score=0.5,
                pass_threshold=True,
                detail="Not yet measured in this comparison",
            ))

    disagreement_notes: list[BenchmarkDisagreementNote] = []
    if regressions and rec in ("revert", "refine"):
        disagreement_notes.append(BenchmarkDisagreementNote(
            note_id="regressions",
            description=f"Regressions: {', '.join(regressions)}",
            dimension_ids=[DIMENSION_TASK_SUCCESS],
            severity="high" if rec == "revert" else "medium",
        ))
    if th_pass is False and rec == "promote":
        disagreement_notes.append(BenchmarkDisagreementNote(
            note_id="thresholds_fail",
            description="Recommendation promote but thresholds not passed",
            dimension_ids=[],
            severity="medium",
        ))

    promotion_rec: PromotionRecommendation | None = None
    if rec == "promote" and th_pass:
        scope = "production_safe" if not regressions else "limited_cohort"
        promotion_rec = PromotionRecommendation(recommend=True, scope=scope, reason="Comparison passed thresholds; no regressions.")
    elif rec == "hold":
        promotion_rec = PromotionRecommendation(recommend=False, scope="experimental_only", reason="Hold; no clear improvement.")
    else:
        promotion_rec = PromotionRecommendation(recommend=False, scope="experimental_only", reason=f"Recommendation: {rec}.")

    rollback_rec: RollbackRecommendation | None = None
    if rec == "revert" and regressions:
        rollback_rec = RollbackRecommendation(recommend=True, prior_id=baseline_id, reason="Regressions detected; roll back to baseline.")

    if not scorecard_id:
        scorecard_id = stable_id("sc", baseline_id, candidate_id, comparison_result.get("at_iso", ""), prefix="sc_")[:20]

    return Scorecard(
        scorecard_id=scorecard_id,
        baseline_id=baseline_id,
        candidate_id=candidate_id,
        slice_ids=slice_ids,
        memory_slice_ids=memory_slice_ids,
        dimensions=dimensions,
        disagreement_notes=disagreement_notes,
        promotion_recommendation=promotion_rec,
        rollback_recommendation=rollback_rec,
        recommendation=rec,
        thresholds_passed=th_pass,
        regressions=regressions,
        improvements=improvements,
        at_iso=comparison_result.get("at_iso", datetime.now(timezone.utc).isoformat()[:19] + "Z"),
    )
