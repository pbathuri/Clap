"""
M23K: Operator-approved workday copilot. Local, inspectable, approval-driven.
"""

from workflow_dataset.copilot.recommendations import recommend_jobs
from workflow_dataset.copilot.routines import Routine, list_routines, get_routine, save_routine
from workflow_dataset.copilot.plan import build_plan_for_job, build_plan_for_routine, PlanPreview
from workflow_dataset.copilot.run import run_plan, list_plan_runs
from workflow_dataset.copilot.reminders import list_reminders, add_reminder, reminders_due
from workflow_dataset.copilot.report import copilot_report, format_copilot_report

__all__ = [
    "recommend_jobs",
    "Routine",
    "list_routines",
    "get_routine",
    "save_routine",
    "PlanPreview",
    "build_plan_for_job",
    "build_plan_for_routine",
    "run_plan",
    "list_plan_runs",
    "list_reminders",
    "add_reminder",
    "reminders_due",
    "copilot_report",
    "format_copilot_report",
]
