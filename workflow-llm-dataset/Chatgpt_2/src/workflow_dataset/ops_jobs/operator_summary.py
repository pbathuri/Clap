"""
M41L.1: Operator-facing maintenance summary — what to run and review to keep the product healthy.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.ops_jobs.cadence import list_due
from workflow_dataset.ops_jobs.calendar import get_maintenance_calendar
from workflow_dataset.ops_jobs.registry import get_ops_job
from workflow_dataset.ops_jobs.report import build_ops_maintenance_report
from workflow_dataset.ops_jobs.rhythm_packs import get_rhythm_pack


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_operator_maintenance_summary(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Operator-facing summary: what must be run and reviewed this week/month to keep the product healthy.
    Returns weekly/monthly blocks (job_ids, review_checklist), summary_text, and link to ops report.
    """
    root = _repo_root(repo_root)
    report = build_ops_maintenance_report(repo_root=root)
    due = list_due(repo_root=root)
    due_job_ids = {d["job_id"] for d in due}
    calendar = get_maintenance_calendar()

    weekly_job_ids: list[str] = []
    monthly_job_ids: list[str] = []
    weekly_pack = get_rhythm_pack("weekly_production")
    monthly_pack = get_rhythm_pack("monthly_production")
    if weekly_pack:
        weekly_job_ids = list(weekly_pack.job_ids)
    if monthly_pack:
        monthly_job_ids = list(monthly_pack.job_ids)

    weekly_due = [jid for jid in weekly_job_ids if jid in due_job_ids]
    monthly_due = [jid for jid in monthly_job_ids if jid in due_job_ids]
    weekly_review = weekly_pack.review_checklist if weekly_pack else []
    monthly_review = monthly_pack.review_checklist if monthly_pack else []

    summary_parts: list[str] = []
    if weekly_due or weekly_review:
        run_names = [get_ops_job(jid) for jid in weekly_due]
        run_names = [j.name if j else jid for jid, j in zip(weekly_due, run_names)]
        if run_names:
            summary_parts.append("This week run: " + ", ".join(run_names) + ".")
        if weekly_review:
            summary_parts.append("This week review: " + "; ".join(weekly_review[:2]) + ".")
    if monthly_due or monthly_review:
        run_names = [get_ops_job(jid) for jid in monthly_due]
        run_names = [j.name if j else jid for jid, j in zip(monthly_due, run_names)]
        if run_names:
            summary_parts.append("This month run: " + ", ".join(run_names) + ".")
        if monthly_review:
            summary_parts.append("This month review: " + "; ".join(monthly_review[:2]) + ".")
    if report.get("blocked_job_id"):
        summary_parts.append("Blocked: " + report["blocked_job_id"] + " — run recommended_action first.")
    if not summary_parts:
        summary_parts.append("No weekly/monthly jobs due now. Check: workflow-dataset ops-jobs due.")

    summary_text = " ".join(summary_parts)

    return {
        "weekly": {
            "job_ids": weekly_job_ids,
            "due_now": weekly_due,
            "review_checklist": weekly_review,
        },
        "monthly": {
            "job_ids": monthly_job_ids,
            "due_now": monthly_due,
            "review_checklist": monthly_review,
        },
        "calendar_rhythms": [e.to_dict() for e in calendar],
        "summary_text": summary_text,
        "recommended_action": report.get("recommended_action", ""),
        "next_due_job_id": report.get("next_due_job_id", ""),
    }
