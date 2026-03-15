"""
Sandbox/virtual environment for simulate mode.

Agent runs proposed actions here; no changes to the real local system.
TODO: implement when execution layer is built (e.g. temp dir, mock FS, or container).
"""

from __future__ import annotations

from typing import Any


class SandboxResult:
    """Result of running an action in the sandbox."""

    def __init__(
        self,
        success: bool,
        output: str | None = None,
        error: str | None = None,
        diff_summary: str | None = None,
    ):
        self.success = success
        self.output = output
        self.error = error
        self.diff_summary = diff_summary


def run_in_sandbox(
    action_type: str,
    target: dict[str, Any],
    intent: str,
) -> SandboxResult:
    """Execute action in sandbox only; no side effects on real system. TODO: implement."""
    return SandboxResult(
        success=False,
        error="sandbox not implemented",
    )
