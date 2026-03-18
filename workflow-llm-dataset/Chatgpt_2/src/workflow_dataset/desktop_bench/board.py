"""
M23I: Benchmark board and reports for desktop automation trust.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.desktop_bench.config import get_runs_dir
from workflow_dataset.desktop_bench.scoring import score_run, compute_trust_status


def list_runs(limit: int = 20, root: Path | str | None = None) -> list[dict[str, Any]]:
    """List desktop benchmark run ids (newest first)."""
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


def compare_runs(
    run_a_id: str,
    run_b_id: str,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Compare two runs: outcome, trust_status, regressions (b worse than a)."""
    ma = get_run(run_a_id, root)
    mb = get_run(run_b_id, root)
    if not ma:
        return {"error": f"Run not found: {run_a_id}"}
    if not mb:
        return {"error": f"Run not found: {run_b_id}"}
    outcome_a = ma.get("outcome", "fail")
    outcome_b = mb.get("outcome", "fail")
    status_a = ma.get("trust_status") or compute_trust_status(ma, ma.get("scores"))
    status_b = mb.get("trust_status") or compute_trust_status(mb, mb.get("scores"))
    regression = outcome_a == "pass" and outcome_b == "fail"
    return {
        "run_a": run_a_id,
        "run_b": run_b_id,
        "outcome_a": outcome_a,
        "outcome_b": outcome_b,
        "trust_status_a": status_a,
        "trust_status_b": status_b,
        "regression_detected": regression,
        "recommendation": "investigate" if regression else "ok",
    }


def board_report(
    suite_name: str = "",
    limit_runs: int = 10,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Desktop benchmark board: latest run(s), pass/fail, simulate-only coverage,
    trusted real-action coverage, missing approval blockers, regressions, recommended next action.
    """
    runs = list_runs(limit=limit_runs, root=root)
    if suite_name:
        runs = [r for r in runs if r.get("suite") == suite_name]
    report: dict[str, Any] = {
        "suite": suite_name or "all",
        "latest_run_id": None,
        "latest_timestamp": None,
        "latest_outcome": None,
        "latest_trust_status": None,
        "simulate_only_coverage": 0,
        "trusted_real_coverage": 0,
        "missing_approval_blockers": [],
        "regressions": [],
        "top_safe_adapters": [],
        "top_risky_adapters": [],
        "recommended_next_action": "run desktop-bench run-suite --suite desktop_bridge_core --mode simulate",
    }
    if not runs:
        return report

    latest = runs[0]
    run_path = latest.get("run_path") or (get_runs_dir(root) / latest.get("run_id", ""))
    if Path(run_path).exists():
        scored = score_run(run_path)
        if scored:
            latest = scored
    report["latest_run_id"] = latest.get("run_id")
    report["latest_timestamp"] = latest.get("timestamp")
    report["latest_outcome"] = latest.get("outcome")
    report["latest_trust_status"] = latest.get("trust_status") or compute_trust_status(latest, latest.get("scores"))

    pass_count = sum(1 for r in runs if r.get("outcome") == "pass")
    report["simulate_only_coverage"] = pass_count / len(runs) if runs else 0
    real_runs = [r for r in runs if r.get("mode") == "real"]
    real_pass = sum(1 for r in real_runs if r.get("outcome") == "pass")
    report["trusted_real_coverage"] = real_pass / len(real_runs) if real_runs else 0

    if latest.get("mode") == "real" and not (latest.get("approvals_checked") or {}).get("registry_exists"):
        report["missing_approval_blockers"].append("approval registry missing")

    if len(runs) >= 2:
        comp = compare_runs(runs[1].get("run_id", ""), runs[0].get("run_id", ""), root)
        if comp.get("regression_detected"):
            report["regressions"].append(f"{comp['run_b']} vs {comp['run_a']}")

    report["top_safe_adapters"] = ["file_ops", "notes_document"]
    report["top_risky_adapters"] = ["browser_open", "app_launch"]

    if report["latest_trust_status"] == "approval_missing":
        report["recommended_next_action"] = "Create data/local/capability_discovery/approvals.yaml and add approved_action_scopes for real mode."
    elif report["latest_outcome"] != "pass":
        report["recommended_next_action"] = "Run desktop-bench run --id <case> --mode simulate to verify; check errors in run_manifest.json."
    return report


def format_board_report(report: dict[str, Any]) -> str:
    """Format board report as human-readable text."""
    lines = [
        "=== Desktop benchmark board (M23I) ===",
        "",
        f"Latest run: {report.get('latest_run_id')}  {report.get('latest_timestamp')}",
        f"Outcome: {report.get('latest_outcome')}  Trust status: {report.get('latest_trust_status')}",
        f"Simulate-only coverage: {report.get('simulate_only_coverage')}  Trusted real coverage: {report.get('trusted_real_coverage')}",
        "",
    ]
    if report.get("missing_approval_blockers"):
        lines.append("Missing approval blockers: " + ", ".join(report["missing_approval_blockers"]))
    if report.get("regressions"):
        lines.append("Regressions: " + ", ".join(report["regressions"]))
    lines.append("Recommended next action: " + str(report.get("recommended_next_action", "")))
    return "\n".join(lines)
