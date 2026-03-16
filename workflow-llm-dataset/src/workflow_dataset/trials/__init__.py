"""
M17: Workflow task trials — real workflow evaluation across baseline / adapter / retrieval modes.

Local-first; connects to context, generation, review, and adoption flows.
"""

from __future__ import annotations

from workflow_dataset.trials.trial_models import (
    WorkflowTrial,
    WorkflowTrialResult,
    WorkflowTrialBundle,
    TrialMode,
)
from workflow_dataset.trials.trial_registry import (
    register_trial,
    get_trial,
    list_trials,
)
from workflow_dataset.trials.trial_runner import run_trial
from workflow_dataset.trials.trial_report import write_trial_report, load_trial_results

__all__ = [
    "WorkflowTrial",
    "WorkflowTrialResult",
    "WorkflowTrialBundle",
    "TrialMode",
    "register_trial",
    "get_trial",
    "list_trials",
    "run_trial",
    "write_trial_report",
    "load_trial_results",
]
