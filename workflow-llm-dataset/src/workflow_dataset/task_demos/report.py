"""
M23E-F1: Task manifest / report. List tasks, format one task.
"""

from __future__ import annotations

from workflow_dataset.task_demos.models import TaskDefinition
from workflow_dataset.task_demos.store import list_tasks
from workflow_dataset.desktop_adapters.simulate import SimulateResult


def format_task_manifest(task: TaskDefinition) -> str:
    """Format a single task as a short manifest (id, notes, steps)."""
    lines = [f"# Task: {task.task_id}", ""]
    if task.notes:
        lines.append(task.notes)
        lines.append("")
    lines.append("## Steps")
    for i, s in enumerate(task.steps, 1):
        params = " ".join(f"{k}={v}" for k, v in s.params.items())
        lines.append(f"{i}. {s.adapter_id} {s.action_id} {params}".strip())
        if s.notes:
            lines.append(f"   notes: {s.notes}")
    return "\n".join(lines)


def format_replay_report(task: TaskDefinition, results: list[SimulateResult]) -> str:
    """Format replay output: step index, success, preview snippet."""
    lines = [f"# Replay (simulate): {task.task_id}", ""]
    for i, (step, res) in enumerate(zip(task.steps, results), 1):
        status = "ok" if res.success else "fail"
        lines.append(f"## Step {i}: {step.adapter_id} {step.action_id} — {status}")
        lines.append(res.preview[:300] + ("..." if len(res.preview) > 300 else ""))
        lines.append("")
    if len(results) < len(task.steps):
        lines.append("(fewer results than steps)")
    return "\n".join(lines)
