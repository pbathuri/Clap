"""
M21X: Thresholds per workflow — floors for relevance, specificity, etc. Used for pass/fail and recommendation.
"""

from __future__ import annotations

from typing import Any

FLOOR_TO_DIMENSION: dict[str, str] = {
    "relevance_floor": "relevance",
    "completeness_floor": "completeness",
    "specificity_floor": "next_step_specificity",
}


def get_thresholds(workflow: str) -> dict[str, float]:
    """Return threshold dict for workflow: relevance_floor, specificity_floor, etc."""
    return {
        "relevance_floor": 0.4,
        "completeness_floor": 0.3,
        "specificity_floor": 0.35,
    }


def check_run_against_thresholds(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Check run cases against workflow floors. Returns passed (bool), by_workflow (workflow -> passed, floors_failed)."""
    by_workflow: dict[str, dict[str, Any]] = {}
    all_passed = True
    for c in cases:
        wf = c.get("workflow", "weekly_status")
        if wf not in by_workflow:
            by_workflow[wf] = {"passed": True, "floors_failed": []}
        th = get_thresholds(wf)
        art_scores = (c.get("scores") or {}).get("artifacts") or {}
        for art_name, scores in art_scores.items():
            for floor_key, dim in FLOOR_TO_DIMENSION.items():
                floor_val = th.get(floor_key, 0)
                val = scores.get(dim, 0)
                if val < floor_val:
                    by_workflow[wf]["passed"] = False
                    all_passed = False
                    if floor_key not in by_workflow[wf]["floors_failed"]:
                        by_workflow[wf]["floors_failed"].append(floor_key)
    return {"passed": all_passed, "by_workflow": by_workflow}
