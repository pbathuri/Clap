"""
M24F: Guided rollout manager — demos, golden journey launcher, rollout tracker,
support bundle, issue report. Local operator rollout discipline; no cloud/telemetry.
"""

from workflow_dataset.rollout.demos import list_demos, get_demo, GuidedDemo
from workflow_dataset.rollout.launcher import launch_golden_journey
from workflow_dataset.rollout.tracker import (
    load_rollout_state,
    save_rollout_state,
    update_rollout_from_acceptance,
)
from workflow_dataset.rollout.support_bundle import build_support_bundle
from workflow_dataset.rollout.issues import format_issues_report
from workflow_dataset.rollout.readiness import build_rollout_readiness_report, format_rollout_readiness_report
from workflow_dataset.rollout.runbooks import list_runbooks, get_runbook_path, get_runbook_content

__all__ = [
    "list_demos",
    "get_demo",
    "GuidedDemo",
    "launch_golden_journey",
    "load_rollout_state",
    "save_rollout_state",
    "update_rollout_from_acceptance",
    "build_support_bundle",
    "format_issues_report",
    "build_rollout_readiness_report",
    "format_rollout_readiness_report",
    "list_runbooks",
    "get_runbook_path",
    "get_runbook_content",
]
