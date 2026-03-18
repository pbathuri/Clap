"""
Observation runtime: run collection respecting consent/boundaries (M31).

Dispatches to existing collectors (file implemented; app/browser/terminal/calendar/teaching stubs).
Only collects from sources that are enabled and in scope; emits to local event stream.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.observe.boundaries import check_source_enabled, get_source_health
from workflow_dataset.observe.local_events import ObservationEvent, append_events
from workflow_dataset.observe.sources import get_observation_source_registry


def run_observation(
    observation_enabled: bool,
    allowed_sources: list[str] | None,
    file_root_paths: list[Path] | None = None,
    file_exclude_dirs: set[str] | None = None,
    file_max_files: int = 10_000,
    file_allowed_extensions: set[str] | None = None,
    event_log_dir: Path | str | None = None,
    device_id: str = "",
    tier: int = 1,
) -> dict[str, Any]:
    """
    Run observation for all enabled sources. Returns summary: events_per_source, written_path,
    blocked, errors. Only file collector is implemented; others are no-op when enabled.
    """
    allowed_sources = allowed_sources or []
    log_dir = Path(event_log_dir) if event_log_dir else None
    events: list[ObservationEvent] = []
    blocked: list[str] = []
    errors: list[str] = []

    # File
    if "file" in allowed_sources and observation_enabled:
        ok, reason = check_source_enabled("file", observation_enabled, allowed_sources)
        if ok and file_root_paths and log_dir is not None:
            try:
                from workflow_dataset.observe.file_activity import collect_file_events
                file_events = collect_file_events(
                    file_root_paths,
                    max_files_per_scan=file_max_files,
                    exclude_dirs=file_exclude_dirs,
                    allowed_extensions=file_allowed_extensions,
                    device_id=device_id,
                    tier=tier,
                )
                events.extend(file_events)
            except Exception as e:
                errors.append(f"file:{e!s}")
        elif not ok:
            blocked.append("file")

    # Stub sources: no-op (no events) but not blocked if allowed
    for source_id in ["app", "browser", "terminal", "calendar", "teaching"]:
        if source_id in allowed_sources and observation_enabled:
            health, _ = get_source_health(
                source_id, observation_enabled, allowed_sources, scope_ok=True, collector_ok=True
            )
            if health == "stub":
                pass  # no events from stubs
            elif health != "ok":
                blocked.append(source_id)

    written_path: Path | None = None
    if events and log_dir:
        written_path = append_events(log_dir, events)

    return {
        "events_per_source": {"file": len([e for e in events if e.source.value == "file"])},
        "total_events": len(events),
        "written_path": str(written_path) if written_path else None,
        "blocked": blocked,
        "errors": errors,
    }
