"""
M23E-F1: Replay task in simulation mode only. No real execution.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.desktop_adapters import run_simulate
from workflow_dataset.desktop_adapters.simulate import SimulateResult

from workflow_dataset.task_demos.models import TaskDefinition
from workflow_dataset.task_demos.store import get_task


def replay_task_simulate(
    task_id: str,
    repo_root: Path | str | None = None,
) -> tuple[TaskDefinition | None, list[SimulateResult]]:
    """
    Replay a task in simulate mode only. Each step runs run_simulate; no run_execute.
    Returns (task_definition_or_none, list of SimulateResult per step).
    """
    task = get_task(task_id, repo_root)
    if not task:
        return None, []
    results: list[SimulateResult] = []
    for step in task.steps:
        r = run_simulate(step.adapter_id, step.action_id, step.params)
        results.append(r)
    return task, results
