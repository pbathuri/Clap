"""
E4: Benchmark board trend view + top-risk workflow summary.

Trend over recent runs, best/worst workflows, top regression risk,
top improvement opportunity. Inspectable and operator-friendly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.eval.board import (
    list_runs,
    get_run,
    _aggregate_scores,
    compare_runs,
    score_run,
)
from workflow_dataset.eval.scoring import SCORE_DIMENSIONS


TREND_THRESHOLD = 0.05  # delta above/below this to call improving/declining


def _aggregate_by_workflow(cases: list[dict[str, Any]]) -> dict[str, float]:
    """Per-workflow mean score (0-1) over all dimensions and artifacts for that workflow."""
    by_workflow: dict[str, list[float]] = {}
    for c in cases:
        wf = c.get("workflow") or "unknown"
        if wf not in by_workflow:
            by_workflow[wf] = []
        scores = c.get("scores", {}).get("artifacts", {})
        for _kind, dims in scores.items():
            for d, v in dims.items():
                if d in SCORE_DIMENSIONS:
                    by_workflow[wf].append(v)
    return {
        wf: round(sum(vals) / len(vals), 4) if vals else 0.0
        for wf, vals in by_workflow.items()
    }


def trend_report(
    limit_runs: int = 10,
    suite_name: str = "",
    root: Path | str | None = None,
) -> dict[str, Any]:
    """
    E4: Trend-oriented benchmark summary.

    Returns:
        trend_over_runs: "improving" | "declining" | "stable"
        recent_run_ids: list of run_id (newest first)
        run_scores: [ { run_id, timestamp, mean_score } ] for trend
        best_workflows: [ { workflow, mean_score, run_id } ] from latest run
        worst_workflows: [ { workflow, mean_score, run_id } ] from latest run
        top_regression_risk: { type, name, delta, run_a, run_b } or None
        top_improvement_opportunity: { type, name, delta, run_a, run_b } or None
        comparison: latest vs previous compare result (for inspectability)
    """
    runs = list_runs(limit=limit_runs, root=root)
    if suite_name:
        runs = [r for r in runs if r.get("suite") == suite_name]
    if not runs:
        return {
            "suite": suite_name or "all",
            "trend_over_runs": "no_runs",
            "recent_run_ids": [],
            "run_scores": [],
            "best_workflows": [],
            "worst_workflows": [],
            "top_regression_risk": None,
            "top_improvement_opportunity": None,
            "comparison": None,
        }
    # Ensure scored
    for r in runs:
        if not r.get("scored") and r.get("run_path"):
            score_run(Path(r["run_path"]))
    runs = [get_run(r["run_id"], root) or r for r in runs]

    # Run scores (newest first); for trend we compare oldest vs newest in window
    run_scores: list[dict[str, Any]] = []
    for r in runs:
        cases = r.get("cases", [])
        agg = _aggregate_scores(cases)
        mean_score = sum(agg.values()) / len(agg) if agg else 0.0
        run_scores.append({
            "run_id": r.get("run_id"),
            "timestamp": r.get("timestamp"),
            "mean_score": round(mean_score, 4),
        })
    # trend: oldest (last in run_scores) vs newest (first)
    trend_over_runs = "stable"
    if len(run_scores) >= 2:
        newest_mean = run_scores[0]["mean_score"]
        oldest_mean = run_scores[-1]["mean_score"]
        delta = newest_mean - oldest_mean
        if delta > TREND_THRESHOLD:
            trend_over_runs = "improving"
        elif delta < -TREND_THRESHOLD:
            trend_over_runs = "declining"

    # Best/worst workflows from latest run
    latest = runs[0]
    latest_cases = latest.get("cases", [])
    by_workflow = _aggregate_by_workflow(latest_cases)
    workflow_list = [
        {"workflow": wf, "mean_score": score, "run_id": latest.get("run_id")}
        for wf, score in by_workflow.items()
    ]
    workflow_list.sort(key=lambda x: x["mean_score"], reverse=True)
    best_workflows = workflow_list[:5]
    worst_workflows = workflow_list[-5:] if len(workflow_list) >= 2 else []
    worst_workflows.reverse()  # lowest first for readability

    # Top regression risk and improvement opportunity from latest vs previous
    comparison = None
    top_regression_risk: dict[str, Any] | None = None
    top_improvement_opportunity: dict[str, Any] | None = None
    if len(runs) >= 2:
        prev_id = runs[1]["run_id"]
        latest_id = runs[0]["run_id"]
        comparison = compare_runs(prev_id, latest_id, root=root)
        deltas = comparison.get("deltas") or {}
        if deltas:
            worst_dim = min(deltas.items(), key=lambda x: x[1])
            best_dim = max(deltas.items(), key=lambda x: x[1])
            if worst_dim[1] < -0.01:
                top_regression_risk = {
                    "type": "dimension",
                    "name": worst_dim[0],
                    "delta": round(worst_dim[1], 3),
                    "run_a": prev_id,
                    "run_b": latest_id,
                }
            if best_dim[1] > 0.01:
                top_improvement_opportunity = {
                    "type": "dimension",
                    "name": best_dim[0],
                    "delta": round(best_dim[1], 3),
                    "run_a": prev_id,
                    "run_b": latest_id,
                }

    return {
        "suite": suite_name or "all",
        "trend_over_runs": trend_over_runs,
        "recent_run_ids": [r["run_id"] for r in runs],
        "run_scores": run_scores,
        "best_workflows": best_workflows,
        "worst_workflows": worst_workflows,
        "top_regression_risk": top_regression_risk,
        "top_improvement_opportunity": top_improvement_opportunity,
        "comparison": comparison,
        "latest_run_id": runs[0].get("run_id"),
        "latest_timestamp": runs[0].get("timestamp"),
    }


def write_trend_report(
    report: dict[str, Any],
    path: Path | str,
    format: str = "json",
) -> Path:
    """Write E4 trend report to file. format: json or md."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if format == "md":
        lines = [
            "# Benchmark trend (E4)",
            "",
            f"- **Suite:** {report.get('suite')}",
            f"- **Trend over recent runs:** {report.get('trend_over_runs')}",
            f"- **Latest run:** {report.get('latest_run_id')}  {report.get('latest_timestamp')}",
            "",
            "## Run scores (newest first)",
            "",
        ]
        for rs in report.get("run_scores", [])[:15]:
            lines.append(f"- {rs.get('run_id')}  {rs.get('timestamp')}  mean={rs.get('mean_score')}")
        lines.extend(["", "## Best workflows (latest run)", ""])
        for w in report.get("best_workflows", []):
            lines.append(f"- **{w.get('workflow')}**  {w.get('mean_score')}")
        lines.extend(["", "## Worst workflows (latest run)", ""])
        for w in report.get("worst_workflows", []):
            lines.append(f"- **{w.get('workflow')}**  {w.get('mean_score')}")
        lines.extend(["", "## Top regression risk", ""])
        rr = report.get("top_regression_risk")
        if rr:
            lines.append(f"- **{rr.get('name')}**  delta={rr.get('delta')}  (vs {rr.get('run_a')})")
        else:
            lines.append("- None identified (or only one run)")
        lines.extend(["", "## Top improvement opportunity", ""])
        io_ = report.get("top_improvement_opportunity")
        if io_:
            lines.append(f"- **{io_.get('name')}**  delta={io_.get('delta')}  (vs {io_.get('run_a')})")
        else:
            lines.append("- None identified (or only one run)")
        p.write_text("\n".join(lines), encoding="utf-8")
    else:
        # JSON: omit large comparison payload by default for readability
        out = {k: v for k, v in report.items() if k != "comparison" or v is not None}
        if report.get("comparison") is not None:
            c = report["comparison"]
            out["comparison_summary"] = {
                "run_a": c.get("run_a"),
                "run_b": c.get("run_b"),
                "regressions": c.get("regressions"),
                "improvements": c.get("improvements"),
                "recommendation": c.get("recommendation"),
            }
        p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return p
