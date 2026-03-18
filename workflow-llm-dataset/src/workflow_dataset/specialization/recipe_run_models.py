"""
M24E: Recipe run model — run id, source recipe, target pack, machine assumptions, approvals, steps, status, reversible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

RECIPE_RUN_STATUSES = ("pending", "running", "completed", "failed", "blocked")


@dataclass
class RecipeRun:
    """A single execution record of a specialization recipe for a target pack."""
    run_id: str
    source_recipe_id: str
    target_domain_pack_id: str = ""
    target_value_pack_id: str = ""
    target_starter_kit_id: str = ""
    machine_assumptions: dict[str, Any] = field(default_factory=dict)  # e.g. runtime_task_class, repo_root
    approvals_required: list[str] = field(default_factory=list)
    steps_planned: list[str] = field(default_factory=list)
    steps_done: list[str] = field(default_factory=list)
    outputs_expected: list[str] = field(default_factory=list)
    outputs_produced: list[str] = field(default_factory=list)
    reversible: bool = True
    status: str = "pending"  # one of RECIPE_RUN_STATUSES
    started_at: str = ""
    finished_at: str = ""
    rollback_notes: str = ""
    error_message: str = ""
    dry_run: bool = False
