"""
M24C: First real-user acceptance harness — scenarios, golden journeys, runner, reports.
Validates product readiness for a controlled local first-user rollout. Report mode; no unsafe real actions.
"""

from workflow_dataset.acceptance.scenarios import (
    list_scenarios,
    get_scenario,
    AcceptanceScenario,
)
from workflow_dataset.acceptance.runner import run_scenario, classify_outcome
from workflow_dataset.acceptance.report import format_acceptance_report
from workflow_dataset.acceptance.storage import save_run, load_latest_run, list_runs

__all__ = [
    "list_scenarios",
    "get_scenario",
    "AcceptanceScenario",
    "run_scenario",
    "classify_outcome",
    "format_acceptance_report",
    "save_run",
    "load_latest_run",
    "list_runs",
]
