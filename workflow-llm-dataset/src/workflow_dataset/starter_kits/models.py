"""
M23Y: Starter kit and first-value flow models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FirstValueFlow:
    """What the user runs first, what they get back, why useful, what to do next."""
    first_run_command: str = ""       # e.g. "workflow-dataset macro run --id morning_ops --mode simulate"
    what_user_gets_back: str = ""     # e.g. "A preview of your morning routine steps and outputs"
    why_useful: str = ""              # e.g. "Confirms the pipeline works without writing anything"
    what_to_do_next: str = ""         # e.g. "Run with real mode after adding approvals, or run inbox"


@dataclass
class StarterKit:
    """Starter kit for a user type: domain pack, jobs, routines, runtime, first-value flow."""
    kit_id: str
    name: str
    description: str = ""
    target_field: str = ""            # e.g. operations, founder
    target_job_family: str = ""        # e.g. founder, analyst, developer
    # Domain / runtime
    domain_pack_id: str = ""
    recommended_profile_defaults: dict[str, Any] = field(default_factory=dict)  # field, job_family, etc.
    recommended_runtime_task_class: str = ""   # desktop_copilot, inbox, codebase_task, etc.
    recommended_model_class: str = ""         # from runtime or domain pack
    recommended_domain_pack_ids: list[str] = field(default_factory=list)
    # Jobs and routines (IDs; may not exist yet)
    recommended_job_ids: list[str] = field(default_factory=list)
    recommended_routine_ids: list[str] = field(default_factory=list)
    # First-value
    first_simulate_only_workflow: str = ""    # routine_id or job_pack_id to run first in simulate
    first_value_flow: FirstValueFlow | None = None
    # Trust / approvals
    trusted_real_eligibility_notes: str = ""
    expected_outputs: list[str] = field(default_factory=list)
    approvals_likely_needed: list[str] = field(default_factory=list)
