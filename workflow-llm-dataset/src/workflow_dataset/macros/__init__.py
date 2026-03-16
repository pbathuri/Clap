"""
M23V: Macro layer — trusted multi-step work with preview, simulate, checkpointed run, blocked-step reporting.
"""

from workflow_dataset.macros.schema import Macro
from workflow_dataset.macros.runner import macro_preview, macro_run, list_macros, get_blocked_steps

__all__ = ["Macro", "macro_preview", "macro_run", "list_macros", "get_blocked_steps"]
