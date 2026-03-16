"""
Browser tab/domain observation (Tier 1).

Tab titles, URLs/domains, timing; no page content or form data.
See docs/schemas/LOCAL_OBSERVATION_EVENTS.md — source 'browser'.
"""

from __future__ import annotations

from typing import Any

# TODO: implement when browser extension or native integration is added; no real monitoring yet.


def browser_payload(
    tab_id: str,
    url: str | None,
    title: str | None,
    action: str,
) -> dict[str, Any]:
    """Build payload for a browser event. url may be domain-only for privacy."""
    return {
        "tab_id": tab_id,
        "url": url,
        "title": title,
        "action": action,
    }


def collect_browser_events(since_utc: str | None = None) -> list[dict[str, Any]]:
    """Collect browser tab/domain events since given time. TODO: implement collector."""
    return []
