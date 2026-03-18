"""
M33A–M33D: Cross-app context bridge — connect signals across file, app, browser, terminal, notes, project/session.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id

from workflow_dataset.workflow_episodes.models import (
    WorkflowEpisode,
    WorkflowStage,
    LinkedActivity,
    InferredProjectAssociation,
)
from workflow_dataset.observe.local_events import load_all_events, ObservationEvent, EventSource, ACTIVITY_TYPE_KEY, PROJECT_HINT_KEY


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _parse_project_from_event(evt: ObservationEvent, root_paths: list[Path] | None) -> str:
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


def build_active_episode(
    repo_root: Path | str | None = None,
    event_log_dir: Path | str | None = None,
    root_paths: list[Path] | None = None,
    max_events: int = 300,
    time_window_minutes: int = 60,
    min_activities: int = 1,
) -> WorkflowEpisode | None:
    """
    Build one active workflow episode from recent observation events and optional live context.
    Links activities across sources (file, app, browser, terminal) into a single episode with
    inferred project and evidence. Returns None if no coherent episode (e.g. no events or stale).
    """
    root = _repo_root(repo_root)
    log_dir = Path(event_log_dir) if event_log_dir else (root / "data/local/event_log")
    if not log_dir.exists():
        return None

    events = load_all_events(log_dir, source_filter=None, max_events=max_events)
    if not events:
        return None

    # Optional: live context for project hint
    live_project_hint = ""
    try:
        from workflow_dataset.live_context.state import get_live_context_state
        ctx = get_live_context_state(root / "data/local")
        if ctx and getattr(ctx, "inferred_project", None):
            live_project_hint = ctx.inferred_project.label or ""
    except Exception:
        pass

    roots = root_paths or [root]
    project_counts: dict[str, int] = defaultdict(int)
    linked: list[LinkedActivity] = []

    for evt in events[:max_events]:
        src = getattr(evt.source, "value", str(evt.source)) if hasattr(evt, "source") else "file"
        payload = evt.payload or {}
        activity_type = payload.get(ACTIVITY_TYPE_KEY) or f"{src}_event"
        path_str = payload.get("path", "")
        label = payload.get("filename", "") or (Path(path_str).name if path_str else evt.event_id[:12])
        proj = _parse_project_from_event(evt, roots)
        if proj:
            project_counts[proj] += 1
        evidence = f"source={src} project_hint={proj or 'none'}"
        linked.append(
            LinkedActivity(
                event_id=evt.event_id,
                source=src,
                timestamp_utc=evt.timestamp_utc,
                activity_type=activity_type,
                path=path_str,
                label=label[:80],
                evidence=evidence,
            )
        )

    if len(linked) < min_activities:
        return None

    # Best project
    ranked = sorted(project_counts.items(), key=lambda x: -x[1])
    best_project = ranked[0][0] if ranked else (live_project_hint or "")
    if live_project_hint and live_project_hint not in project_counts:
        best_project = best_project or live_project_hint
    total = sum(project_counts.values()) or 1
    best_count = project_counts.get(best_project, 0)
    project_confidence = min(0.95, 0.3 + 0.5 * (best_count / total) + (0.15 if live_project_hint and best_project == live_project_hint else 0))

    inferred_project = None
    if best_project:
        inferred_project = InferredProjectAssociation(
            project_id=best_project,
            label=best_project,
            confidence=round(project_confidence, 2),
            evidence=[f"file_events={best_count}", f"total={total}", "live_context_hint=" + live_project_hint if live_project_hint else "live_context_hint=none"],
        )

    now = utc_now_iso()
    episode_id = stable_id("ep", now, best_project or "none", str(len(linked)), prefix="ep_")
    evidence_summary = [f"activities={len(linked)}", f"project={best_project}", f"project_confidence={project_confidence:.2f}"]

    return WorkflowEpisode(
        episode_id=episode_id,
        started_at_utc=linked[-1].timestamp_utc if linked else now,
        updated_at_utc=now,
        linked_activities=linked,
        inferred_project=inferred_project,
        current_task_hypothesis=None,
        stage=WorkflowStage.UNKNOWN,
        stage_evidence=[],
        next_step_candidates=[],
        handoff_gaps=[],
        overall_confidence=project_confidence,
        evidence_summary=evidence_summary,
        is_active=True,
        closed_at_utc="",
        close_reason="",
    )
