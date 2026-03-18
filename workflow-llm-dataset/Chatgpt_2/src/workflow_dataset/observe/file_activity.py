"""
File and folder metadata observation (Tier 1).

Captures path, name, extension, size, mtime, ctime, is_dir; event kind "snapshot".
No file content is read. See docs/schemas/LOCAL_OBSERVATION_EVENTS.md — source 'file'.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.observe.local_events import (
    EventSource,
    ObservationEvent,
    create_event_id,
    normalized_payload_extra,
)


# Default exclusions for safe scanning (edge-feasible)
DEFAULT_EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", ".venv", ".tox", "venv"}


def file_snapshot_payload(
    path: Path,
    stat_result: os.stat_result | None,
    timestamp_utc: str,
) -> dict[str, Any]:
    """Build payload for a file snapshot event. Metadata only; no content."""
    name = path.name
    try:
        is_dir = path.is_dir()
    except OSError:
        is_dir = False
    if stat_result is None:
        try:
            stat_result = path.stat()
        except OSError:
            stat_result = None

    mtime_utc: str | None = None
    ctime_utc: str | None = None
    size: int | None = None
    if stat_result is not None:
        try:
            from datetime import datetime, timezone
            mtime_utc = datetime.fromtimestamp(stat_result.st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            ctime_utc = datetime.fromtimestamp(stat_result.st_ctime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            size = stat_result.st_size if not is_dir else 0
        except (OSError, OverflowError):
            pass

    suffix = path.suffix if not is_dir else ""
    return {
        "path": str(path.resolve()),
        "filename": name,
        "extension": suffix.lstrip(".") if suffix else "",
        "size": size,
        "modified_time_utc": mtime_utc,
        "created_time_utc": ctime_utc,
        "is_dir": is_dir,
        "event_kind": "snapshot",
    }


def collect_file_events(
    root_paths: list[Path],
    timestamp_utc: str | None = None,
    max_files_per_scan: int = 10_000,
    exclude_dirs: set[str] | None = None,
    allowed_extensions: set[str] | None = None,
    device_id: str = "",
    tier: int = 1,
) -> list[ObservationEvent]:
    """
    Scan root_paths and emit one snapshot event per file/directory.
    Metadata only; no file contents are read.
    """
    ts = timestamp_utc or utc_now_iso()
    exclude = exclude_dirs or DEFAULT_EXCLUDE_DIRS
    allowed_ext = allowed_extensions  # None = allow all
    count = 0
    events: list[ObservationEvent] = []

    for root in root_paths:
        if not root.exists() or not root.is_dir():
            continue
        root_resolved = root.resolve()
        try:
            for entry in root.rglob("*"):
                if count >= max_files_per_scan:
                    break
                try:
                    if entry.is_dir():
                        if entry.name in exclude:
                            continue
                        stat_result = None
                    else:
                        if allowed_ext is not None and entry.suffix.lstrip(".").lower() not in allowed_ext:
                            continue
                        try:
                            stat_result = entry.stat()
                        except OSError:
                            stat_result = None
                    payload = file_snapshot_payload(entry, stat_result, ts)
                    payload.update(
                        normalized_payload_extra(activity_type="file_snapshot", provenance="file_scan")
                    )
                    event_id = create_event_id("evt", "file", ts, payload["path"], str(count))
                    evt = ObservationEvent(
                        event_id=event_id,
                        source=EventSource.FILE,
                        timestamp_utc=ts,
                        device_id=device_id,
                        tier=tier,
                        payload=payload,
                    )
                    events.append(evt)
                    count += 1
                except OSError:
                    continue
        except OSError:
            continue
        if count >= max_files_per_scan:
            break

    return events


def file_payload(
    path: str | Path,
    name: str,
    kind: str,
    mtime_utc: str | None,
    action: str,
) -> dict[str, Any]:
    """Build payload for a file event (legacy/API). path/name may be redacted or hashed for privacy."""
    return {
        "path": str(path),
        "name": name,
        "kind": kind,
        "mtime_utc": mtime_utc,
        "action": action,
    }
