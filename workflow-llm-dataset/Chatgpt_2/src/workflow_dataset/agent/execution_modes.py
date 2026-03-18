"""
Execution modes: observe, simulate, assist, automate.

Default is simulate. See docs/schemas/EXECUTION_MODES.md.
"""

from __future__ import annotations

from enum import Enum


class ExecutionMode(str, Enum):
    OBSERVE = "observe"
    SIMULATE = "simulate"
    ASSIST = "assist"
    AUTOMATE = "automate"
    # DELEGATE = "delegate"  # future, not v1


DEFAULT_EXECUTION_MODE = ExecutionMode.SIMULATE


def is_safe_default(mode: ExecutionMode) -> bool:
    """True if mode does not allow unapproved local changes."""
    return mode in (ExecutionMode.OBSERVE, ExecutionMode.SIMULATE)
