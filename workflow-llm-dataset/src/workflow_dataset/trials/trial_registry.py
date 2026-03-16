"""
M17: Registry of workflow trials. Register scenarios and look up by id or domain.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.trials.trial_models import WorkflowTrial


_trials: dict[str, WorkflowTrial] = {}


def register_trial(trial: WorkflowTrial) -> None:
    """Register a workflow trial. Overwrites if trial_id exists."""
    _trials[trial.trial_id] = trial


def get_trial(trial_id: str) -> WorkflowTrial | None:
    """Return trial by id or None."""
    return _trials.get(trial_id)


def list_trials(
    domain: str | None = None,
    scenario_id: str | None = None,
) -> list[WorkflowTrial]:
    """List registered trials, optionally filtered by domain or scenario_id."""
    out = list(_trials.values())
    if domain:
        out = [t for t in out if (t.domain or "").lower() == domain.lower()]
    if scenario_id:
        out = [t for t in out if (t.scenario_id or "").lower() == scenario_id.lower()]
    return sorted(out, key=lambda t: (t.domain or "", t.trial_id or ""))


def clear_registry() -> None:
    """Clear all registered trials (for tests)."""
    _trials.clear()
