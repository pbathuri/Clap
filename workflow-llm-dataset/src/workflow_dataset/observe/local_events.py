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
