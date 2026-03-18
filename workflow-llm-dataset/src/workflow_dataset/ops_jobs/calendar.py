"""
M41L.1: Maintenance calendar — weekly/monthly maintenance loops derived from ops job cadence.
"""

from __future__ import annotations

from workflow_dataset.ops_jobs.models import MaintenanceCalendarEntry
from workflow_dataset.ops_jobs.registry import BUILTIN_OPS_JOBS


def get_maintenance_calendar() -> list[MaintenanceCalendarEntry]:
    """
    Build the default maintenance calendar by grouping built-in ops jobs by cadence.
    Rhythms: twice_daily (interval_hours), daily (interval_days=1), weekly (interval_days=7), monthly (interval_days>=28).
    """
    bands: dict[str, list[str]] = {
        "twice_daily": [],
        "daily": [],
        "weekly": [],
        "monthly": [],
    }
    for job in BUILTIN_OPS_JOBS:
        c = job.cadence
        if c.interval_hours > 0 and c.interval_days <= 0:
            bands["twice_daily"].append(job.job_id)
        elif c.interval_days >= 28:
            bands["monthly"].append(job.job_id)
        elif c.interval_days >= 7:
            bands["weekly"].append(job.job_id)
        elif c.interval_days >= 1:
            bands["daily"].append(job.job_id)

    out: list[MaintenanceCalendarEntry] = []
    if bands["twice_daily"]:
        out.append(MaintenanceCalendarEntry(
            rhythm="twice_daily",
            job_ids=bands["twice_daily"],
            label="Twice daily",
            description="Queue and calmness checks; run every 12h.",
        ))
    if bands["daily"]:
        out.append(MaintenanceCalendarEntry(
            rhythm="daily",
            job_ids=bands["daily"],
            label="Daily",
            description="Reliability, triage, production-cut, vertical value, operator audit.",
        ))
    if bands["weekly"]:
        out.append(MaintenanceCalendarEntry(
            rhythm="weekly",
            job_ids=bands["weekly"],
            label="Weekly",
            description="Adaptation audit, supportability and release readiness.",
        ))
    if bands["monthly"]:
        out.append(MaintenanceCalendarEntry(
            rhythm="monthly",
            job_ids=bands["monthly"],
            label="Monthly",
            description="Extended audits and health reviews.",
        ))
    return out
