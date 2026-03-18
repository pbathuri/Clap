"""
M23V/M23P: Macro layer — trusted multi-step work, preview, simulate, checkpointed run, pause/resume, step classification.
"""

from workflow_dataset.macros.schema import Macro, MacroStep
from workflow_dataset.macros.runner import (
    macro_preview,
    macro_run,
    list_macros,
    get_blocked_steps,
    get_macro_steps,
    resume_macro_run,
)
from workflow_dataset.macros.run_state import (
    list_paused_runs,
    list_awaiting_approval_runs,
    list_all_macro_runs,
    load_run_state,
)
from workflow_dataset.macros.step_classifier import classify_step, explain_step_categories

__all__ = [
    "Macro",
    "MacroStep",
    "macro_preview",
    "macro_run",
    "list_macros",
    "get_blocked_steps",
    "get_macro_steps",
    "resume_macro_run",
    "list_paused_runs",
    "list_awaiting_approval_runs",
    "list_all_macro_runs",
    "load_run_state",
    "classify_step",
    "explain_step_categories",
]
