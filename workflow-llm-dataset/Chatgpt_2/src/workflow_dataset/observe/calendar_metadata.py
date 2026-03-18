"""
Calendar metadata observation (Tier 1).

Event titles, times, attendees; no body/description.
See docs/schemas/LOCAL_OBSERVATION_EVENTS.md — source 'calendar'.
"""

from __future__ import annotations

from typing import Any

# TODO: implement when CalDAV or local calendar API integration is added.


def calendar_payload(
    event_id: str,
    title: str,
    start_utc: str,
    end_utc: str,
    attendees: list[str] | None = None,
) -> dict[str, Any]:
    """Build payload for a calendar event."""
    return {
        "event_id": event_id,
        "title": title,
        "start_utc": start_utc,
        "end_utc": end_utc,
        "attendees": attendees or [],
    }


def collect_calendar_events(since_utc: str | None = None) -> list[dict[str, Any]]:
    """Collect calendar metadata events since given time. TODO: implement collector."""
    return []
