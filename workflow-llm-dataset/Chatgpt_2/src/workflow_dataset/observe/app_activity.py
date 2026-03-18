"""
App usage observation (Tier 1).

Foreground app, switch events, duration; no in-app content.
See docs/schemas/LOCAL_OBSERVATION_EVENTS.md — source 'app'.
"""

from __future__ import annotations

from typing import Any

# TODO: implement when OS-specific collectors are added (e.g. macOS NSWorkspace, Windows, Linux).


def app_payload(
    app_id: str,
    app_name: str,
    action: str,
    duration_seconds: float | None = None,
) -> dict[str, Any]:
    """Build payload for an app event."""
    return {
        "app_id": app_id,
        "app_name": app_name,
        "action": action,
        "duration_seconds": duration_seconds,
    }


def collect_app_events(since_utc: str | None = None) -> list[dict[str, Any]]:
    """Collect app usage events since given time. TODO: implement collector."""
    return []
