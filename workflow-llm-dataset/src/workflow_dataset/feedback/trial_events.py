"""
M19: Lightweight local trial event capture for narrow-release path.
No remote telemetry; events stored under data/local/trials/events.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _events_dir(store_path: Path | str | None) -> Path:
    base = Path(store_path) if store_path else Path("data/local/trials")
    events = base / "events"
    events.mkdir(parents=True, exist_ok=True)
    return events


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_trial_event(
    event_type: str,
    payload: dict[str, Any] | None = None,
    store_path: Path | str | None = None,
) -> Path:
    """
    Append a single trial event to the local events log.
    event_type: e.g. release_command_used, task_selected, generation_succeeded,
                bundle_created, adoption_candidate_created, apply_preview_reached, apply_confirmed.
    """
    events_dir = _events_dir(store_path)
    event_id = uuid.uuid4().hex[:12]
    record = {
        "event_id": event_id,
        "event_type": event_type,
        "payload": payload or {},
        "created_utc": _ts(),
    }
    path = events_dir / f"evt_{event_id}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return path


def load_trial_events(store_path: Path | str | None = None) -> list[dict[str, Any]]:
    """Load all trial events (for summaries); returns list of event dicts."""
    events_dir = _events_dir(store_path)
    if not events_dir.exists():
        return []
    out = []
    for path in sorted(events_dir.glob("evt_*.json")):
        try:
            out.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return out
