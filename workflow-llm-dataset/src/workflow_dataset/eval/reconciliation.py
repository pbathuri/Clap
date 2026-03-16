"""
M21X: Reconciliation — heuristic + operator (+ optional model-judge) into verdict: promote, hold, refine, revert.
"""

from __future__ import annotations

from typing import Any


def get_run_scores_breakdown(manifest: dict[str, Any]) -> dict[str, Any]:
    """Breakdown: heuristic_score, operator_score, model_judge_score, per_case list."""
    cases = manifest.get("cases") or []
    heuristic_sum = 0.0
    operator_sum = 0.0
    operator_count = 0
    per_case: list[dict[str, Any]] = []
    for c in cases:
        scores = c.get("scores") or {}
        arts = scores.get("artifacts") or {}
        h_vals: list[float] = []
        for art_s in arts.values():
            if isinstance(art_s, dict):
                h_vals.extend(v for v in art_s.values() if isinstance(v, (int, float)))
        h_mean = sum(h_vals) / len(h_vals) if h_vals else 0.0
        heuristic_sum += h_mean
        op_rating = scores.get("operator_rating")
        op_score = None
        if op_rating and isinstance(op_rating, dict) and "overall" in op_rating:
            o = op_rating["overall"]
            if isinstance(o, (int, float)):
                op_score = (o - 1) / 4.0 if o else 0.0  # 1-5 -> 0-1
                operator_sum += op_score
                operator_count += 1
        per_case.append({
            "case_id": c.get("case_id"),
            "heuristic_score": h_mean,
            "operator_score": op_score,
        })
    n = len(cases) or 1
    return {
        "heuristic_score": round(heuristic_sum / n, 4),
        "operator_score": round(operator_sum / operator_count, 4) if operator_count else None,
        "model_judge_score": None,
        "per_case": per_case,
    }


def reconcile_run(
    manifest: dict[str, Any],
    comparison: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Reconcile run: verdict (promote|hold|refine|revert), reasons, separated scores."""
    breakdown = get_run_scores_breakdown(manifest)
    verdict = "hold"
    reasons: list[str] = []
    h = breakdown.get("heuristic_score") or 0
    o = breakdown.get("operator_score")
    if comparison:
        reg = comparison.get("regressions") or []
        imp = comparison.get("improvements") or []
        if reg:
            verdict = "refine" if "revert" not in str(comparison.get("recommendation", "")) else "revert"
            reasons.append(f"Regressions: {reg}")
        elif imp:
            verdict = "promote" if (comparison.get("thresholds_passed") or False) else "hold"
            reasons.append(f"Improvements: {imp}")
        reasons.append(f"Recommendation from comparison: {comparison.get('recommendation', 'hold')}")
    if h >= 0.5 and (o is None or o >= 0.5):
        if verdict == "hold":
            verdict = "promote" if h >= 0.6 else "hold"
        reasons.append(f"Heuristic score: {h:.2f}")
    else:
        if verdict == "promote":
            verdict = "hold"
        reasons.append(f"Heuristic score: {h:.2f} (below 0.6)")
    if o is not None:
        reasons.append(f"Operator score: {o:.2f}")
    reasons.append(f"Verdict: {verdict}")
    return {
        "run_id": manifest.get("run_id"),
        "verdict": verdict,
        "reasons": reasons,
        "heuristic_score": breakdown.get("heuristic_score"),
        "operator_score": breakdown.get("operator_score"),
        "model_judge_score": breakdown.get("model_judge_score"),
    }
