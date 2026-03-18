"""
M21X: Benchmark board — list runs, get run, compare runs, compare latest vs best, board report. Recommendation: promote, hold, refine, revert.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.eval.config import get_eval_root, get_runs_dir
from workflow_dataset.eval.reconciliation import reconcile_run
from workflow_dataset.eval.thresholds import check_run_against_thresholds


def list_runs(limit: int = 20, root: Path | str | None = None) -> list[dict[str, Any]]:
    """List run ids (newest first) from runs dir."""
    runs_dir = get_runs_dir(root)
    if not runs_dir.exists():
        return []
    out: list[dict[str, Any]] = []
    for d in sorted(runs_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if d.is_dir() and (d / "run_manifest.json").exists():
            try:
                m = json.loads((d / "run_manifest.json").read_text(encoding="utf-8"))
                m["run_path"] = str(d)
                out.append(m)
            except Exception:
                pass
            if len(out) >= limit:
                break
    return out


def resolve_run_id(alias: str, root: Path | str | None = None) -> str | None:
    """Resolve 'latest' or 'previous' to a run_id from list_runs; otherwise return alias as-is if it looks like an id."""
    if not alias or alias.strip() == "":
        return None
    alias = alias.strip().lower()
    if alias == "latest":
        runs = list_runs(limit=1, root=root)
        return runs[0].get("run_id") if runs else None
    if alias == "previous":
        runs = list_runs(limit=2, root=root)
        return runs[1].get("run_id") if len(runs) >= 2 else None
    return alias


def get_run(run_id: str, root: Path | str | None = None) -> dict[str, Any] | None:
    """Load run manifest by run_id."""
    runs_dir = get_runs_dir(root)
    run_path = runs_dir / run_id
    if not run_path.exists() or not run_path.is_dir():
        return None
    m = run_path / "run_manifest.json"
    if not m.exists():
        return None
    try:
        data = json.loads(m.read_text(encoding="utf-8"))
        data["run_path"] = str(run_path)
        return data
    except Exception:
        return None


def _run_total_score(manifest: dict[str, Any]) -> float:
    """Aggregate total score from cases (mean of per-case mean artifact scores)."""
    cases = manifest.get("cases") or []
    if not cases:
        return 0.0
    totals: list[float] = []
    for c in cases:
        scores = (c.get("scores") or {}).get("artifacts") or {}
        if not scores:
            totals.append(0.0)
            continue
        vals: list[float] = []
        for art_s in scores.values():
            if isinstance(art_s, dict):
                vals.extend(v for v in art_s.values() if isinstance(v, (int, float)))
        totals.append(sum(vals) / len(vals) if vals else 0.0)
    return sum(totals) / len(totals) if totals else 0.0


def compare_runs(
    run_a: str,
    run_b: str,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Compare two runs: deltas, regressions, improvements, thresholds, recommendation."""
    ma = get_run(run_a, root)
    mb = get_run(run_b, root)
    if not ma:
        return {"error": f"Run not found: {run_a}"}
    if not mb:
        return {"error": f"Run not found: {run_b}"}
    sa = _run_total_score(ma)
    sb = _run_total_score(mb)
    th_a = check_run_against_thresholds(ma.get("cases") or [])
    th_b = check_run_against_thresholds(mb.get("cases") or [])
    regressions: list[str] = []
    improvements: list[str] = []
    for d in ("relevance", "completeness", "next_step_specificity", "blocker_quality", "risk_quality"):
        # Compare per-case dimensions if available
        regressions.append(d) if sb < sa and (th_b.get("by_workflow") or {}).get("weekly_status", {}).get("passed") is False else None
        improvements.append(d) if sb > sa else None
    regressions = [x for x in regressions if x]
    improvements = [x for x in improvements if x]
    if sb < sa:
        regressions = regressions or ["overall_score"]
    if sb > sa:
        improvements = improvements or ["overall_score"]
    recommendation = "promote" if sb > sa and th_b.get("passed", True) else "hold" if sb == sa else "refine" if regressions else "revert"
    return {
        "run_a": run_a,
        "run_b": run_b,
        "run_a_timestamp": ma.get("timestamp"),
        "run_b_timestamp": mb.get("timestamp"),
        "regressions": regressions,
        "improvements": improvements,
        "thresholds_passed": th_b.get("passed", False),
        "recommendation": recommendation,
    }


def compare_latest_vs_best(
    suite_name: str = "",
    limit_runs: int = 20,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Compare latest run vs previous best (by total score). Returns run_b=latest, run_a=best, regressions, improvements, recommendation."""
    runs = list_runs(limit=limit_runs, root=root)
    if not runs:
        return {"error": "No runs found"}
    if suite_name:
        runs = [r for r in runs if r.get("suite") == suite_name]
    if not runs:
        return {"error": "No runs found"}
    best = max(runs, key=lambda r: _run_total_score(r))
    latest = runs[0]
    run_b = latest.get("run_id", "")
    run_a = best.get("run_id", "")
    if run_a == run_b:
        th = check_run_against_thresholds(latest.get("cases") or [])
        return {
            "run_a": run_a,
            "run_b": run_b,
            "run_a_timestamp": best.get("timestamp"),
            "run_b_timestamp": latest.get("timestamp"),
            "comparison_note": "latest_is_best",
            "regressions": [],
            "improvements": [],
            "thresholds_passed": th.get("passed", False),
            "recommendation": "promote" if th.get("passed") else "hold",
        }
    out = compare_runs(run_a, run_b, root=root)
    out["comparison_note"] = "latest_vs_best"
    return out


def board_report(
    suite_name: str = "",
    limit_runs: int = 10,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Benchmark board report: latest run, best run, thresholds, recommendation, reconciliation."""
    runs = list_runs(limit=limit_runs, root=root)
    if suite_name:
        runs = [r for r in runs if r.get("suite") == suite_name]
    report: dict[str, Any] = {
        "suite": suite_name or "all",
        "latest_run_id": None,
        "latest_timestamp": None,
        "best_run_id": None,
        "thresholds_passed": False,
        "recommendation": "hold",
        "comparison_with_previous": None,
        "comparison_with_best": None,
        "reconciliation": None,
    }
    if not runs:
        return report
    latest = runs[0]
    best = max(runs, key=lambda r: _run_total_score(r))
    report["latest_run_id"] = latest.get("run_id")
    report["latest_timestamp"] = latest.get("timestamp")
    report["best_run_id"] = best.get("run_id")
    th = check_run_against_thresholds(latest.get("cases") or [])
    report["thresholds_passed"] = th.get("passed", False)
    comp = compare_latest_vs_best(suite_name=suite_name, limit_runs=limit_runs, root=root)
    report["comparison_with_best"] = comp
    report["recommendation"] = comp.get("recommendation", "hold")
    report["reconciliation"] = reconcile_run(latest, comparison=comp)
    return report


def write_board_report(report: dict[str, Any], path: Path | str, format: str = "json") -> None:
    """Write board report to file (json or md)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if format.lower() == "md":
        lines = [
            "# Benchmark board",
            "",
            f"- **Latest run:** {report.get('latest_run_id')}  {report.get('latest_timestamp')}",
            f"- **Best run:** {report.get('best_run_id')}",
            f"- **Thresholds passed:** {report.get('thresholds_passed')}",
            f"- **Recommendation:** {report.get('recommendation')}",
        ]
        if report.get("reconciliation"):
            r = report["reconciliation"]
            lines.append(f"- **Verdict:** {r.get('verdict')}")
        path.write_text("\n".join(lines), encoding="utf-8")
    else:
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
