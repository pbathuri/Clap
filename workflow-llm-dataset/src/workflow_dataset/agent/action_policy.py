"""
Policy: whether an action is allowed in the current execution mode and approval boundaries.

Default: no local system changes unless mode is assist/automate and within boundaries.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.agent.execution_modes import ExecutionMode


def may_propose(mode: ExecutionMode) -> bool:
    """Agent may propose suggestions (e.g. in simulate/assist/automate)."""
    return mode in (ExecutionMode.SIMULATE, ExecutionMode.ASSIST, ExecutionMode.AUTOMATE)


def may_execute_locally(mode: ExecutionMode) -> bool:
    """Agent may execute on the real local system (assist with approval, or automate within boundaries)."""
    return mode in (ExecutionMode.ASSIST, ExecutionMode.AUTOMATE)


def check_boundary(
    mode: ExecutionMode,
    action_type: str,
    target: dict[str, Any],
    approval_boundaries: dict[str, Any] | None,
) -> tuple[bool, str]:
    """
    Check if action is within approval boundaries.
    Returns (allowed, reason).
    TODO: implement boundary rules (path prefix, app allowlist, etc.).
    """
    if not may_execute_locally(mode):
        return False, "execution_mode does not allow local execution"
    if not approval_boundaries:
        return False, "no approval boundaries configured"
    return False, "not implemented"
