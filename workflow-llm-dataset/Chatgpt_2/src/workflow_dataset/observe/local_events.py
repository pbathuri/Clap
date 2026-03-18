"""
Local observation event envelope and source types.

Events are device-local only; see docs/schemas/LOCAL_OBSERVATION_EVENTS.md.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class EventSource(str, Enum):
    FILE = "file"
    APP = "app"
    BROWSER = "browser"
    TERMINAL = "terminal"
    CALENDAR = "calendar"
    TEACHING = "teaching"


# Normalized event stream payload keys (M31B). Optional; collectors may set these.
ACTIVITY_TYPE_KEY = "activity_type"
PROJECT_HINT_KEY = "project_hint"
SESSION_HINT_KEY = "session_hint"
REDACTION_MARKER_KEY = "redaction_marker"
PROVENANCE_KEY = "provenance"


class ObservationEvent(BaseModel):
    """Single observation event; immutable, device-local."""

    event_id: str = Field(..., description="Stable unique ID (e.g. evt_*)")
    source: EventSource
    timestamp_utc: str = Field(..., description="ISO 8601")
    device_id: str = Field(default="", description="Device that produced the event")
    tier: int = Field(default=1, ge=1, le=3, description="Observation tier 1–3")
    payload: dict[str, Any] = Field(default_factory=dict, description="Source-specific payload")

    model_config = {"frozen": True}

    def to_json_line(self) -> str:
        """Serialize to a single JSON line for JSONL."""
        d = self.model_dump()
        d["source"] = self.source.value
        return json.dumps(d, ensure_ascii=False) + "\n"

    @classmethod
    def from_json_line(cls, line: str) -> ObservationEvent:
        """Deserialize one event from a JSONL line."""
        d = json.loads(line.strip())
        d["source"] = EventSource(d["source"]) if isinstance(d.get("source"), str) else d["source"]
        return cls.model_validate(d)

    def normalized_view(self) -> dict[str, Any]:
        """
        Return a compact normalized view for streams/reports: event_id, source, timestamp,
        coarse activity_type, bounded metadata (payload), project_hint, session_hint,
        redaction_marker, provenance. No raw over-collection.
        """
        p = self.payload
        return {
            "event_id": self.event_id,
            "source": self.source.value,
            "timestamp_utc": self.timestamp_utc,
            "activity_type": p.get(ACTIVITY_TYPE_KEY) or _default_activity_type(self.source),
            "payload": p,
            "project_hint": p.get(PROJECT_HINT_KEY),
            "session_hint": p.get(SESSION_HINT_KEY),
            "redaction_marker": p.get(REDACTION_MARKER_KEY),
            "provenance": p.get(PROVENANCE_KEY),
        }


def _default_activity_type(source: EventSource) -> str:
    """Default coarse activity type when not set in payload."""
    return f"{source.value}_event"


def normalized_payload_extra(
    activity_type: str,
    project_hint: str | None = None,
    session_hint: str | None = None,
    redaction_marker: str | None = None,
    provenance: str | None = None,
) -> dict[str, Any]:
    """
    Build optional payload fields for the normalized stream. Merge into payload when
    creating events. Prefer compact structured events; do not over-collect.
    """
    out: dict[str, Any] = {ACTIVITY_TYPE_KEY: activity_type}
    if project_hint is not None:
        out[PROJECT_HINT_KEY] = project_hint
    if session_hint is not None:
        out[SESSION_HINT_KEY] = session_hint
    if redaction_marker is not None:
        out[REDACTION_MARKER_KEY] = redaction_marker
    if provenance is not None:
        out[PROVENANCE_KEY] = provenance
    return out


def create_event_id(prefix: str = "evt", *parts: str) -> str:
    """Generate a stable event ID from parts."""
    from workflow_dataset.utils.hashes import stable_id
    return stable_id(*parts, prefix=prefix)


def _event_log_filename(date_str: str | None = None) -> str:
    """Deterministic log file name by date (YYYY-MM-DD)."""
    if date_str:
        return f"events_{date_str.replace('-', '')}.jsonl"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"events_{today.replace('-', '')}.jsonl"


def append_events(
    log_dir: Path,
    events: list[ObservationEvent],
    date_str: str | None = None,
) -> Path:
    """
    Append events to the local event log. One file per day (YYYYMMDD).
    Creates log_dir if needed. Returns path to the file written.
    """
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / _event_log_filename(date_str)
    with open(path, "a", encoding="utf-8") as f:
        for evt in events:
            f.write(evt.to_json_line())
    return path


def load_events(
    log_dir: Path,
    date_str: str | None = None,
    source_filter: str | None = None,
    limit: int = 0,
) -> list[ObservationEvent]:
    """
    Load events from the local event log. If date_str is None, loads from the most recent file.
    source_filter: only events with this source value (e.g. "file").
    limit: max events to return (0 = all).
    """
    log_dir = Path(log_dir)
    if not log_dir.exists():
        return []
    if date_str:
        name = _event_log_filename(date_str)
        path = log_dir / name
    else:
        candidates = sorted(log_dir.glob("events_*.jsonl"), reverse=True)
        path = candidates[0] if candidates else None
    if path is None or not path.exists():
        return []
    out: list[ObservationEvent] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                evt = ObservationEvent.from_json_line(line)
            except (json.JSONDecodeError, Exception):
                continue
            if source_filter and evt.source.value != source_filter:
                continue
            out.append(evt)
            if limit and len(out) >= limit:
                break
    return out


def load_all_events(
    log_dir: Path,
    source_filter: str | None = None,
    max_events: int = 0,
) -> list[ObservationEvent]:
    """
    Load events from all event log files (events_*.jsonl), newest first.
    source_filter: only events with this source value (e.g. "file").
    max_events: cap total events (0 = all).
    """
    log_dir = Path(log_dir)
    if not log_dir.exists():
        return []
    candidates = sorted(log_dir.glob("events_*.jsonl"), reverse=True)
    out: list[ObservationEvent] = []
    for path in candidates:
        if max_events and len(out) >= max_events:
            break
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        evt = ObservationEvent.from_json_line(line)
                    except (json.JSONDecodeError, Exception):
                        continue
                    if source_filter and evt.source.value != source_filter:
                        continue
                    out.append(evt)
                    if max_events and len(out) >= max_events:
                        break
        except OSError:
            continue
    return out
