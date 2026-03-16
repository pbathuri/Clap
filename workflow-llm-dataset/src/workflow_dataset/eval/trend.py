"""
M21X: Benchmark trend — trend over runs, best/worst workflows, top regression risk, top improvement opportunity.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.eval.board import compare_latest_vs_best, get_run, list_runs
from workflow_dataset.eval.config import get_runs_dir


def _aggregate_by_workflow(cases: list[dict[str, Any]]) -> dict[str, float]:
    """Per-workflow mean score from cases (mean of artifact dimension values)."""
    by_wf: dict[str, list[float]] = {}
    for c in cases:
        wf = c.get("workflow", "weekly_status")
        scores = (c.get("scores") or {}).get("artifacts") or {}
        vals: list[float] = []
        for art_s in scores.values():
            if isinstance(art_s, dict):
                vals.extend(v for v in art_s.values() if isinstance(v, (int, float)))
        if wf not in by_wf:
            by_wf[wf] = []
        if vals:
            by_wf[wf].append(sum(vals) / len(vals))
    return {wf: sum(v) / len(v) if v else 0.0 for wf, v in by_wf.items()}


def trend_report(
    suite_name: str = "",
    limit_runs: int = 10,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Trend report: trend_over_runs, recent_run_ids, best/worst workflows, top regression/improvement."""
    runs = list_runs(limit=limit_runs, root=root)
    if suite_name:
        runs = [r for r in runs if r.get("suite") == suite_name]
    out: dict[str, Any] = {
        "suite": suite_name or "all",
        "trend_over_runs": "no_runs",
        "recent_run_ids": [],
        "run_scores": [],
        "best_workflows": [],
        "worst_workflows": [],
        "top_regression_risk": None,
        "top_improvement_opportunity": None,
        "comparison": None,
        "latest_run_id": None,
        "latest_timestamp": None,
    }
    if not runs:
        return out
    run_scores: list[dict[str, Any]] = []
    for r in runs:
        total = 0.0
        cases = r.get("cases") or []
        for c in cases:
            arts = (c.get("scores") or {}).get("artifacts") or {}
            for art_s in arts.values():
                if isinstance(art_s, dict):
                    total += sum(v for v in art_s.values() if isinstance(v, (int, float))) / max(len(art_s), 1)
        run_scores.append({
            "run_id": r.get("run_id"),
            "timestamp": r.get("timestamp"),
            "mean_score": total / len(cases) if cases else 0.0,
        })
    out["recent_run_ids"] = [r.get("run_id") for r in runs]
    out["run_scores"] = run_scores
    out["latest_run_id"] = runs[0].get("run_id")
    out["latest_timestamp"] = runs[0].get("timestamp")
    if len(runs) == 1:
        out["trend_over_runs"] = "stable"
        by_wf = _aggregate_by_workflow(runs[0].get("cases") or [])
        sorted_wf = sorted(by_wf.items(), key=lambda x: x[1], reverse=True)
        out["best_workflows"] = [{"workflow": w, "mean_score": s, "run_id": runs[0].get("run_id")} for w, s in sorted_wf[:5]]
        out["worst_workflows"] = [{"workflow": w, "mean_score": s, "run_id": runs[0].get("run_id")} for w, s in sorted_wf[-5:]]
        return out
    comp = compare_latest_vs_best(suite_name=suite_name, limit_runs=limit_runs, root=root)
    out["comparison"] = comp
    if comp.get("regressions"):
        out["trend_over_runs"] = "declining"
        out["top_regression_risk"] = {"type": "dimension", "name": comp["regressions"][0], "delta": -0.1, "run_a": comp.get("run_a"), "run_b": comp.get("run_b")}
    elif comp.get("improvements"):
        out["trend_over_runs"] = "improving"
        out["top_improvement_opportunity"] = {"type": "dimension", "name": comp["improvements"][0], "delta": 0.1, "run_a": comp.get("run_a"), "run_b": comp.get("run_b")}
    else:
        out["trend_over_runs"] = "stable"
    latest = runs[0]
    by_wf = _aggregate_by_workflow(latest.get("cases") or [])
    sorted_wf = sorted(by_wf.items(), key=lambda x: x[1], reverse=True)
    out["best_workflows"] = [{"workflow": w, "mean_score": s, "run_id": latest.get("run_id")} for w, s in sorted_wf[:5]]
    out["worst_workflows"] = [{"workflow": w, "mean_score": s, "run_id": latest.get("run_id")} for w, s in sorted_wf[-5:]]
    return out


def write_trend_report(report: dict[str, Any], path: Path | str, format: str = "json") -> None:
    """Write trend report to file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if format.lower() == "md":
        lines = [
            "# Benchmark trend",
            "",
            f"- **Trend:** {report.get('trend_over_runs')}",
            f"- **Latest run:** {report.get('latest_run_id')}  {report.get('latest_timestamp')}",
            "",
            "## Best workflows (latest run)",
            "",
        ]
        for w in report.get("best_workflows") or []:
            lines.append(f"- {w.get('workflow')}: {w.get('mean_score')}")
        lines.extend(["", "## Worst workflows (latest run)", ""])
        for w in report.get("worst_workflows") or []:
            lines.append(f"- {w.get('workflow')}: {w.get('mean_score')}")
        lines.extend(["", "## Top regression risk", ""])
        rr = report.get("top_regression_risk")
        lines.append(str(rr) if rr else "—")
        lines.extend(["", "## Top improvement opportunity", ""])
        io_ = report.get("top_improvement_opportunity")
        lines.append(str(io_) if io_ else "—")
        path.write_text("\n".join(lines), encoding="utf-8")
    else:
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
