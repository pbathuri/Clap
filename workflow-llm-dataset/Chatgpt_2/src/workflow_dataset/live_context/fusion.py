"""
Context fusion: fuse observation + graph + session into active work context (M32B).

Consumes recent observation events, optional graph projects/routines, optional session hint.
Produces current ActiveWorkContext, ranked candidates, confidence, evidence.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from workflow_dataset.live_context.models import (
    ActiveWorkContext,
    ActivityMode,
    FocusState,
    FocusStateKind,
    FocusTarget,
    InferredProject,
    InferredTaskFamily,
    WorkMode,
    SourceContribution,
    CONTEXT_STALE_SECONDS,
)
from workflow_dataset.observe.local_events import (
    ObservationEvent,
    load_all_events,
    ACTIVITY_TYPE_KEY,
    PROJECT_HINT_KEY,
)
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def _parse_project_from_file_event(evt: ObservationEvent, root_paths: list[Path] | None) -> str:
    """Extract project label from a file event: payload project_hint or path under root."""
    payload = evt.payload or {}
    hint = payload.get(PROJECT_HINT_KEY)
    if hint:
        return str(hint).strip() or ""
    path_str = payload.get("path")
    if not path_str:
        return ""
    path_obj = Path(path_str).resolve()
    roots = [Path(r).resolve() for r in (root_paths or [])]
    for r in roots:
        try:
            rel = path_obj.relative_to(r)
            if rel.parts:
                return rel.parts[0]
        except ValueError:
            continue
    if path_obj.parts:
        return path_obj.parts[-2] if len(path_obj.parts) >= 2 else path_obj.parts[0]
    return ""


def _parse_focus_from_events(events: list[ObservationEvent], root_paths: list[Path] | None) -> FocusTarget | None:
    """Best-effort focus target from most recent file event."""
    for evt in events:
        if (getattr(evt, "source", None) is not None and getattr(evt.source, "value", None) == "file") or (
            isinstance(getattr(evt, "source", None), str) and evt.source == "file"
        ):
            payload = evt.payload or {}
            path_str = payload.get("path")
            name = payload.get("filename", "")
            if path_str:
                return FocusTarget(kind="path", value=path_str, display_name=name or Path(path_str).name)
    return None


# Extension buckets for activity mode inference (M32D.1)
_WRITING_EXT = {"md", "mdx", "txt", "doc", "docx", "rst", "tex", "adoc"}
_REVIEWING_EXT = {"pdf", "doc", "docx", "md"}  # overlap with writing; review often PDFs
_PLANNING_EXT = {"xlsx", "xls", "csv", "numbers", "ods", "md", "mdc"}
_CODING_EXT = {"py", "ts", "tsx", "js", "jsx", "go", "rs", "rb", "java", "kt", "swift", "c", "cpp", "h", "hpp", "r", "sql", "sh", "bash", "zsh"}
_ADMIN_EXT = {"yaml", "yml", "json", "toml", "ini", "cfg", "conf", "env", "xml"}


def _infer_activity_mode(use_events: list[ObservationEvent]) -> tuple[ActivityMode, str]:
    """Infer activity mode from file extensions in recent events. Returns (mode, reason)."""
    ext_counts: dict[str, int] = defaultdict(int)
    for evt in use_events:
        src = getattr(evt, "source", None)
        src_val = getattr(src, "value", str(src)) if src is not None else ""
        if src_val != "file":
            continue
        payload = evt.payload or {}
        ext = (payload.get("extension") or "").strip().lower()
        if not ext and payload.get("path"):
            ext = Path(payload["path"]).suffix.lstrip(".").lower()
        if ext:
            ext_counts[ext] += 1
    if not ext_counts:
        return ActivityMode.UNKNOWN, "No file extensions in recent events."
    total = sum(ext_counts.values())
    writing_n = sum(ext_counts.get(e, 0) for e in _WRITING_EXT)
    planning_n = sum(ext_counts.get(e, 0) for e in _PLANNING_EXT)
    coding_n = sum(ext_counts.get(e, 0) for e in _CODING_EXT)
    admin_n = sum(ext_counts.get(e, 0) for e in _ADMIN_EXT)
    if coding_n >= total * 0.4:
        return ActivityMode.CODING, f"Recent files are mostly source code ({coding_n}/{total} events); extensions suggest coding."
    if writing_n >= total * 0.4:
        return ActivityMode.WRITING, f"Recent files are mostly documents/prose ({writing_n}/{total} events); extensions suggest writing."
    if planning_n >= total * 0.35:
        return ActivityMode.PLANNING, f"Recent files include spreadsheets/plans ({planning_n}/{total} events); suggests planning."
    if admin_n >= total * 0.4:
        return ActivityMode.ADMIN, f"Recent files are mostly config/admin ({admin_n}/{total} events); suggests admin or config work."
    if writing_n + planning_n > 0 and total >= 3:
        return ActivityMode.REVIEWING, f"Mix of documents and plans ({writing_n} writing-like, {planning_n} planning-like); could be reviewing."
    top_ext = max(ext_counts.items(), key=lambda x: x[1])
    return ActivityMode.UNKNOWN, f"Mixed or unclear extensions; top extension .{top_ext[0]} ({top_ext[1]}/{total} events)."


def _infer_focus_state(
    use_events: list[ObservationEvent],
    root_paths: list[Path] | None,
) -> tuple[FocusState | None, str]:
    """Infer focus state from file path pattern. Returns (focus_state, reason)."""
    file_paths: list[Path] = []
    for evt in use_events:
        src = getattr(evt, "source", None)
        src_val = getattr(src, "value", str(src)) if src is not None else ""
        if src_val != "file":
            continue
        payload = evt.payload or {}
        path_str = payload.get("path")
        if path_str and not payload.get("is_dir", False):
            file_paths.append(Path(path_str).resolve())
    if not file_paths:
        return None, "No file paths in recent events."
    # Distinct files (by resolved path)
    distinct_files = len(set(file_paths))
    dirs = [p.parent for p in file_paths]
    distinct_dirs = len(set(dirs))
    # Same dir?
    if distinct_files <= 2 and distinct_dirs <= 1:
        return (
            FocusState(kind=FocusStateKind.SINGLE_FILE, confidence=0.8, reason="One or two files in a single directory.", signal_summary=f"distinct_files={distinct_files} distinct_dirs={distinct_dirs}"),
            "Recent activity is concentrated on one or two files in the same directory; strong single-file or tight focus.",
        )
    if distinct_dirs == 1:
        return (
            FocusState(kind=FocusStateKind.MULTI_FILE_SAME_DIR, confidence=0.75, reason="Multiple files in one directory.", signal_summary=f"distinct_files={distinct_files} distinct_dirs=1"),
            "Multiple files touched but all in the same directory; likely working within one folder.",
        )
    # One project (top-level under root)?
    project_dirs: set[str] = set()
    roots = [Path(r).resolve() for r in (root_paths or [])]
    for p in dirs:
        for r in roots:
            try:
                rel = p.relative_to(r)
                if rel.parts:
                    project_dirs.add(rel.parts[0])
                    break
            except ValueError:
                continue
    if len(project_dirs) == 1 and distinct_dirs > 1:
        return (
            FocusState(kind=FocusStateKind.PROJECT_BROWSE, confidence=0.7, reason="Multiple dirs under one project.", signal_summary=f"distinct_dirs={distinct_dirs} projects={list(project_dirs)}"),
            "Activity spans multiple directories but within a single project; browsing or navigating the project.",
        )
    if distinct_dirs >= 2 and (len(project_dirs) >= 2 or not project_dirs):
        return (
            FocusState(kind=FocusStateKind.SCATTERED, confidence=0.65, reason="Multiple projects or unrelated paths.", signal_summary=f"distinct_dirs={distinct_dirs}"),
            "Activity across multiple directories or projects; focus is scattered or switching.",
        )
    return (
        FocusState(kind=FocusStateKind.UNKNOWN, confidence=0.5, reason="Pattern unclear.", signal_summary=f"distinct_files={distinct_files} distinct_dirs={distinct_dirs}"),
        "Could not determine a clear focus pattern from recent file paths.",
    )


def _compute_work_mode(
    project_counts: dict[str, int],
    recent_project: str,
    last_signal_utc: str,
    now_utc: str,
) -> WorkMode:
    """First-draft work mode from project distribution and recency."""
    if not last_signal_utc:
        return WorkMode.IDLE
    # Simple recency: if last signal is old, IDLE or UNKNOWN
    try:
        from datetime import datetime, timezone
        last = datetime.fromisoformat(last_signal_utc.replace("Z", "+00:00"))
        now = datetime.fromisoformat(now_utc.replace("Z", "+00:00"))
        delta_sec = (now - last).total_seconds()
        if delta_sec > CONTEXT_STALE_SECONDS:
            return WorkMode.IDLE
    except Exception:
        pass
    if not project_counts:
        return WorkMode.UNKNOWN
    total = sum(project_counts.values())
    if total == 0:
        return WorkMode.UNKNOWN
    top = sorted(project_counts.items(), key=lambda x: -x[1])
    if top[0][1] >= total * 0.7 and top[0][0] == recent_project:
        return WorkMode.FOCUSED
    if len(top) >= 2 and top[1][1] > 0:
        return WorkMode.SWITCHING
    return WorkMode.UNKNOWN


def fuse_active_context(
    events: list[ObservationEvent],
    root_paths: list[Path] | None = None,
    graph_projects: list[dict[str, Any]] | None = None,
    graph_routines: list[dict[str, Any]] | None = None,
    session_hint: str = "",
    project_hint: str = "",
    max_events: int = 200,
) -> ActiveWorkContext:
    """
    Fuse bounded signals into current active work context.
    events: recent observation events (newest first recommended).
    root_paths: for inferring project from file paths.
    graph_projects: optional list of {node_id, label} from graph.
    graph_routines: optional list of {routine_id, label, project} from routines.
    """
    now = utc_now_iso()
    context_id = stable_id("ctx", now, str(len(events)), prefix="ctx")
    # Use up to max_events
    use_events = events[:max_events] if events else []
    last_signal_utc = use_events[0].timestamp_utc if use_events else ""

    project_counts: dict[str, int] = defaultdict(int)
    file_events = 0
    for evt in use_events:
        src = getattr(evt, "source", None)
        src_val = getattr(src, "value", str(src)) if src is not None else ""
        if src_val == "file":
            file_events += 1
            proj = _parse_project_from_file_event(evt, root_paths)
            if proj:
                project_counts[proj] += 1

    # Ranked project candidates
    ranked_projects = sorted(project_counts.items(), key=lambda x: -x[1])
    best_project = ranked_projects[0][0] if ranked_projects else (project_hint or "")
    if project_hint and project_hint not in project_counts:
        project_counts[project_hint] = 0
    best_count = ranked_projects[0][1] if ranked_projects else 0
    total_file = sum(project_counts.values()) or 1
    project_confidence = min(0.95, 0.3 + 0.4 * (best_count / total_file) + (0.2 if project_hint and best_project == project_hint else 0))

    inferred_project = None
    if best_project:
        evidence = [f"file_events={best_count}", f"total_file_events={total_file}"]
        if project_hint and best_project == project_hint:
            evidence.append("session_project_hint")
        inferred_project = InferredProject(
            project_id=best_project,
            label=best_project,
            confidence=round(project_confidence, 2),
            evidence=evidence,
        )

    # Task family: first-draft from top routine by project match if we have routines
    inferred_task = None
    if graph_routines and best_project:
        for r in graph_routines:
            if r.get("project") == best_project:
                inferred_task = InferredTaskFamily(
                    task_id=r.get("routine_id", ""),
                    label=r.get("label", "routine"),
                    confidence=min(0.8, r.get("confidence", 0.5) + 0.1),
                    evidence=["graph_routine_match"],
                )
                break

    focus = _parse_focus_from_events(use_events, root_paths)

    work_mode = _compute_work_mode(
        dict(project_counts),
        best_project,
        last_signal_utc,
        now,
    )

    # Activity mode and focus state (M32D.1)
    activity_mode, activity_mode_reason = _infer_activity_mode(use_events)
    focus_state, focus_state_reason = _infer_focus_state(use_events, root_paths)

    # Source contributions
    contributions: list[SourceContribution] = []
    if file_events > 0:
        contributions.append(
            SourceContribution(
                source="file",
                weight=min(1.0, file_events / 50.0),
                evidence_summary=f"{file_events} file events",
                signals_count=file_events,
            )
        )
    if graph_projects:
        contributions.append(
            SourceContribution(
                source="graph",
                weight=0.3,
                evidence_summary=f"{len(graph_projects)} project nodes",
                signals_count=len(graph_projects),
            )
        )
    if session_hint or project_hint:
        contributions.append(
            SourceContribution(
                source="session",
                weight=0.2,
                evidence_summary=f"hints: session={bool(session_hint)} project={bool(project_hint)}",
                signals_count=1,
            )
        )

    overall_confidence = 0.0
    if contributions:
        overall_confidence = min(0.95, 0.2 + sum(c.weight for c in contributions) * 0.25)
    evidence_summary = [f"projects_ranked={list(project_counts.keys())[:5]}", f"work_mode={work_mode.value}"]

    try:
        from datetime import datetime, timezone
        last_dt = datetime.fromisoformat(last_signal_utc.replace("Z", "+00:00"))
        now_dt = datetime.fromisoformat(now.replace("Z", "+00:00"))
        is_stale = (now_dt - last_dt).total_seconds() > CONTEXT_STALE_SECONDS
    except Exception:
        is_stale = not bool(use_events)

    return ActiveWorkContext(
        context_id=context_id,
        timestamp_utc=now,
        focus_target=focus,
        inferred_project=inferred_project,
        inferred_task_family=inferred_task,
        work_mode=work_mode,
        activity_mode=activity_mode,
        focus_state=focus_state,
        activity_mode_reason=activity_mode_reason,
        focus_state_reason=focus_state_reason,
        overall_confidence=round(overall_confidence, 2),
        evidence_summary=evidence_summary,
        source_contributions=contributions,
        is_stale=is_stale,
        last_signal_utc=last_signal_utc,
        session_hint=session_hint,
        project_hint=project_hint,
    )


def fuse_active_context_from_sources(
    event_log_dir: Path | str,
    graph_store_path: Path | str | None = None,
    root_paths: list[Path] | list[str] | None = None,
    session_hint: str = "",
    project_hint: str = "",
    max_events: int = 200,
) -> ActiveWorkContext:
    """
    Load recent events and optional graph, then fuse. Convenience for CLI/callers.
    """
    log_dir = Path(event_log_dir)
    events = load_all_events(log_dir, max_events=max_events)
    roots = None
    if root_paths:
        roots = [Path(p).resolve() if isinstance(p, str) else p for p in root_paths]
    graph_projects: list[dict[str, Any]] = []
    graph_routines: list[dict[str, Any]] = []
    if graph_store_path and Path(graph_store_path).exists():
        try:
            import sqlite3
            from workflow_dataset.personal.work_graph import NodeType
            from workflow_dataset.personal.graph_store import list_nodes
            conn = sqlite3.connect(str(graph_store_path))
            try:
                for n in list_nodes(conn, node_type=NodeType.PROJECT.value, limit=100):
                    graph_projects.append({"node_id": n["node_id"], "label": n.get("label", n["node_id"])})
                for n in list_nodes(conn, node_type=NodeType.ROUTINE.value, limit=100):
                    attrs = n.get("attributes") or {}
                    graph_routines.append({
                        "routine_id": n["node_id"],
                        "label": n.get("label", n["node_id"]),
                        "project": attrs.get("project", ""),
                        "confidence": attrs.get("confidence", 0.5),
                    })
            finally:
                conn.close()
        except Exception:
            pass
    return fuse_active_context(
        events,
        root_paths=roots,
        graph_projects=graph_projects or None,
        graph_routines=graph_routines or None,
        session_hint=session_hint,
        project_hint=project_hint,
        max_events=max_events,
    )
