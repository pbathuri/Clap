"""
UI models and screen identifiers for the operator console.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class Screen(str, Enum):
    """Named screens in the console flow."""

    HOME = "home"
    SETUP = "setup"
    PROJECT = "project"
    SUGGESTIONS = "suggestions"
    DRAFTS = "drafts"
    MATERIALIZE = "materialize"
    APPLY = "apply"
    ROLLBACK = "rollback"
    CHAT = "chat"
    GENERATION = "generation"
    EXIT = "exit"


class ActionIntent(str, Enum):
    """User intent for safety labeling."""

    INSPECT = "inspect"  # read-only
    SANDBOX = "sandbox"  # materialize to workspace only
    APPLY_PLAN = "apply_plan"  # preview / plan only
    APPLY_CONFIRM = "apply_confirm"  # pending user confirmation
    APPLY_EXECUTED = "apply_executed"  # already executed
    ROLLBACK_CONFIRM = "rollback_confirm"  # pending rollback confirmation
    ROLLBACK_EXECUTED = "rollback_executed"


def evidence_snippet(items: list[Any], max_items: int = 5, sep: str = "; ") -> str:
    """Format a short evidence list for display."""
    if not items:
        return "(none)"
    out = sep.join(str(x)[:60] for x in items[:max_items])
    if len(items) > max_items:
        out += f" … +{len(items) - max_items}"
    return out
