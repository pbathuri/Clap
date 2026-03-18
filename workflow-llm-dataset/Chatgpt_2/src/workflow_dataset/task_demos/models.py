"""
M23E-F1: Task demonstration schema. Task id, step sequence, adapter/action refs, params, notes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TaskStep:
    """One step in a demonstrated task: adapter, action, params, optional notes."""
    adapter_id: str
    action_id: str
    params: dict[str, str] = field(default_factory=dict)
    notes: str = ""


@dataclass
class TaskDefinition:
    """A captured task: id, ordered steps, optional task-level notes."""
    task_id: str
    steps: list[TaskStep] = field(default_factory=list)
    notes: str = ""
