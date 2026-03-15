"""
Detect routines (recurring patterns) from file observation events.

Deterministic heuristics only: frequently touched folders/projects,
repeated file extensions by project, work periods by hour, path clusters.
All inference on-device. No file content read.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from workflow_dataset.utils.hashes import stable_id

# Minimum occurrences to consider something a "routine"
MIN_TOUCHES_FOLDER = 3
MIN_TOUCHES_PROJECT = 3
MIN_FILES_FOR_EXTENSION_PATTERN = 2
MIN_HOUR_SAMPLES = 2


def _parse_file_events(events: list[Any], root_paths: list[Path] | None = None) -> list[dict[str, Any]]:
    """Extract path, project, extension, hour_utc from file events. No content."""
    roots = [Path(r).resolve() for r in (root_paths or [])]
    rows: list[dict[str, Any]] = []
    for evt in events:
        src = getattr(evt, "source", None)
        if src is not None:
            src = getattr(src, "value", str(src))
        else:
            try:
                src = evt.get("source") if isinstance(evt, dict) else None
            except (TypeError, AttributeError):
                continue
        if src != "file":
            continue
        payload = getattr(evt, "payload", evt) if hasattr(evt, "payload") else evt
        if not isinstance(payload, dict):
            continue
        path_str = payload.get("path")
        if not path_str:
            continue
        path_obj = Path(path_str).resolve()
        is_dir = payload.get("is_dir", False)
        ext = (payload.get("extension") or "").strip().lower()
        if not ext and not is_dir and path_obj.suffix:
            ext = path_obj.suffix.lstrip(".").lower()
        ts = getattr(evt, "timestamp_utc", payload.get("timestamp_utc") or "")
        hour_utc = None
        if ts and len(ts) >= 13:
            try:
                hour_utc = int(ts[11:13])
            except ValueError:
                pass
        project = ""
        for r in roots:
            try:
                rel = path_obj.relative_to(r)
                if rel.parts:
                    project = rel.parts[0]
                break
            except ValueError:
                continue
        if not project and path_obj.parts:
            project = path_obj.parts[-2] if len(path_obj.parts) >= 2 else path_obj.parts[0]
        rows.append({
            "path": path_str,
            "path_obj": path_obj,
            "project": project,
            "extension": ext,
            "hour_utc": hour_utc,
            "is_dir": is_dir,
            "timestamp_utc": ts,
        })
    return rows


def detect_routines(
    events: list[Any],
    root_paths: list[Path] | None = None,
    min_folder_touches: int = MIN_TOUCHES_FOLDER,
    min_project_touches: int = MIN_TOUCHES_PROJECT,
    min_extensions_per_project: int = MIN_FILES_FOR_EXTENSION_PATTERN,
    min_hour_samples: int = MIN_HOUR_SAMPLES,
) -> list[dict[str, Any]]:
    """
    Infer simple recurring patterns from file observation events.
    Returns list of routine dicts: routine_type, label, touch_count, project/path, extensions, hours, confidence, supporting_signals.
    """
    rows = _parse_file_events(events, root_paths)
    if not rows:
        return []

    routines: list[dict[str, Any]] = []

    # 1. Frequently touched folders (by path prefix)
    folder_touches: dict[str, int] = defaultdict(int)
    for r in rows:
        p = r["path_obj"]
        if r["is_dir"]:
            folder_touches[r["path"]] += 1
        else:
            folder_touches[str(p.parent)] += 1
    for path, count in sorted(folder_touches.items(), key=lambda x: -x[1]):
        if count >= min_folder_touches:
            routines.append({
                "routine_type": "frequent_folder",
                "routine_id": stable_id("routine", "folder", path, str(count), prefix="routine"),
                "label": f"User often works in folder {Path(path).name}",
                "path": path,
                "project": "",
                "touch_count": count,
                "extensions": [],
                "hours": [],
                "confidence": min(0.9, 0.5 + 0.1 * min(count - min_folder_touches, 4)),
                "supporting_signals": [f"path_touches={count}"],
            })

    # 2. Frequently touched projects (top-level folder)
    project_touches: dict[str, int] = defaultdict(int)
    for r in rows:
        if r["project"]:
            project_touches[r["project"]] += 1
    for project, count in sorted(project_touches.items(), key=lambda x: -x[1]):
        if count >= min_project_touches:
            routines.append({
                "routine_type": "frequent_project",
                "routine_id": stable_id("routine", "project", project, str(count), prefix="routine"),
                "label": f"User frequently works in project '{project}'",
                "path": "",
                "project": project,
                "touch_count": count,
                "extensions": [],
                "hours": [],
                "confidence": min(0.9, 0.5 + 0.1 * min(count - min_project_touches, 4)),
                "supporting_signals": [f"project_touches={count}"],
            })

    # 3. Repeated file extensions by project (e.g. .csv, .xlsx in project Y)
    project_extensions: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in rows:
        if not r["is_dir"] and r["project"] and r["extension"]:
            project_extensions[r["project"]][r["extension"]] += 1
    for project, ext_counts in project_extensions.items():
        total = sum(ext_counts.values())
        if total < min_extensions_per_project:
            continue
        top_exts = sorted(ext_counts.items(), key=lambda x: -x[1])[:5]
        exts = [e for e, c in top_exts if c >= 1]
        if not exts:
            continue
        label_exts = ", ".join(f".{e}" for e in exts[:3])
        routines.append({
            "routine_type": "repeated_extensions_by_project",
            "routine_id": stable_id("routine", "ext", project, label_exts, prefix="routine"),
            "label": f"User repeatedly opens {label_exts} files in project '{project}'",
            "path": "",
            "project": project,
            "touch_count": total,
            "extensions": exts,
            "hours": [],
            "confidence": min(0.85, 0.5 + 0.05 * len(exts)),
            "supporting_signals": [f"project={project}", f"extensions={exts}", f"file_count={total}"],
        })

    # 4. Work periods by hour-of-day (peak hours)
    hour_counts: dict[int, int] = defaultdict(int)
    for r in rows:
        if r["hour_utc"] is not None:
            hour_counts[r["hour_utc"]] += 1
    if hour_counts and sum(hour_counts.values()) >= min_hour_samples:
        peak_hours = sorted(hour_counts.items(), key=lambda x: -x[1])[:3]
        hours = [h for h, c in peak_hours if c >= 1]
        if hours:
            routines.append({
                "routine_type": "work_period_by_hour",
                "routine_id": stable_id("routine", "hour", ",".join(map(str, hours)), prefix="routine"),
                "label": f"User repeatedly edits files during hours (UTC): {hours}",
                "path": "",
                "project": "",
                "touch_count": sum(hour_counts[h] for h in hours),
                "extensions": [],
                "hours": hours,
                "confidence": 0.7,
                "supporting_signals": [f"peak_hours_utc={hours}"],
            })

    # 5. Path cluster (path prefix with many touches)
    prefix_touches: dict[str, int] = defaultdict(int)
    for r in rows:
        parts = r["path_obj"].parts
        for i in range(1, len(parts) + 1):
            prefix = str(Path(*parts[:i]))
            prefix_touches[prefix] += 1
    for prefix, count in sorted(prefix_touches.items(), key=lambda x: -x[1]):
        if count >= min_folder_touches and len(Path(prefix).parts) >= 2:
            routines.append({
                "routine_type": "path_cluster",
                "routine_id": stable_id("routine", "cluster", prefix, str(count), prefix="routine"),
                "label": f"Active path cluster: {prefix}",
                "path": prefix,
                "project": Path(prefix).parts[-1] if Path(prefix).parts else "",
                "touch_count": count,
                "extensions": [],
                "hours": [],
                "confidence": min(0.8, 0.5 + 0.05 * min(count - min_folder_touches, 6)),
                "supporting_signals": [f"path_prefix_touches={count}"],
            })
            break

    return routines


def attach_routine_to_workflow(
    routine_id: str,
    workflow_chain_id: str,
    graph_store: Any,
) -> None:
    """Link a routine to a workflow chain. TODO: implement persistence (edge routine -> workflow)."""
    pass
