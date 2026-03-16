"""
M23K: Copilot reporting. Recommendations, routine usage, blocked, plan-run mix, stale reminders.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.copilot.recommendations import recommend_jobs
from workflow_dataset.copilot.routines import list_routines
from workflow_dataset.copilot.run import list_plan_runs
from workflow_dataset.copilot.reminders import list_reminders


def copilot_report(repo_root: Path | str | None = None, limit_runs: int = 20) -> dict[str, Any]:
    """Aggregate copilot state for dashboard and reporting."""
    root = Path(repo_root).resolve() if repo_root else None
    recs = recommend_jobs(root, limit=30)
    routines = list_routines(root)
    runs = list_plan_runs(limit=limit_runs, repo_root=root)
    reminders = list_reminders(root)

    recommended_jobs = [r["job_pack_id"] for r in recs]
    blocked = [r for r in recs if r.get("blocking_issues")]
    simulate_only_recs = [r for r in recs if r.get("mode_allowed") == "simulate_only"]
    trusted_recs = [r for r in recs if r.get("mode_allowed") == "trusted_real_eligible"]

    return {
        "recommendations_count": len(recs),
        "recommended_job_ids": recommended_jobs[:15],
        "blocked_recommendations_count": len(blocked),
        "simulate_only_recommendations_count": len(simulate_only_recs),
        "trusted_real_recommendations_count": len(trusted_recs),
        "routines_count": len(routines),
        "routine_ids": routines,
        "plan_runs_count": len(runs),
        "recent_plan_runs": runs[:5],
        "reminders_count": len(reminders),
        "upcoming_reminders": reminders[:10],
        "stale_reminders_count": 0,  # optional: could mark reminders past due_at
    }


def format_copilot_report(report: dict[str, Any]) -> str:
    """Human-readable copilot report."""
    lines = [
        "=== Copilot report (M23K) ===",
        "",
        f"Recommendations: {report.get('recommendations_count', 0)}  (blocked: {report.get('blocked_recommendations_count', 0)}  simulate_only: {report.get('simulate_only_recommendations_count', 0)}  trusted_real: {report.get('trusted_real_recommendations_count', 0)})",
        f"Routines: {report.get('routines_count', 0)}  {report.get('routine_ids', [])}",
        f"Plan runs (recent): {report.get('plan_runs_count', 0)}",
        f"Reminders: {report.get('reminders_count', 0)}",
        "",
    ]
    if report.get("recommended_job_ids"):
        lines.append("Recommended jobs: " + ", ".join(report["recommended_job_ids"][:10]))
    if report.get("upcoming_reminders"):
        lines.append("Upcoming reminders:")
        for r in report["upcoming_reminders"][:5]:
            lines.append(f"  {r.get('title')} due={r.get('due_at')} routine={r.get('routine_id')} job={r.get('job_pack_id')}")
    return "\n".join(lines)
