"""
Local-first observation layer (Tier 1–3).

Captures file, app, browser, terminal, calendar, and manual-teaching events
on-device only. No event data leaves the device unless the user explicitly
enables sync. See docs/OBSERVATION_PHASES.md.
"""

from workflow_dataset.observe.local_events import ObservationEvent, EventSource

__all__ = ["ObservationEvent", "EventSource"]
