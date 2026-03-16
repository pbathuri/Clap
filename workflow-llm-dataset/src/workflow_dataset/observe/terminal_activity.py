"""
Terminal command observation (Tier 1).

Commands run in configured shells; optional redaction of secrets.
See docs/schemas/LOCAL_OBSERVATION_EVENTS.md — source 'terminal'.
"""

from __future__ import annotations

from typing import Any

# TODO: implement when shell integration is added (e.g. hook into shell history); user can exclude paths or disable.


def terminal_payload(
    session_id: str,
    command: str,
    cwd: str | None = None,
    exit_code: int | None = None,
) -> dict[str, Any]:
    """Build payload for a terminal event. command/cwd may be redacted."""
    return {
        "session_id": session_id,
        "command": command,
        "cwd": cwd,
        "exit_code": exit_code,
    }


def collect_terminal_events(since_utc: str | None = None) -> list[dict[str, Any]]:
    """Collect terminal command events since given time. TODO: implement collector."""
    return []
