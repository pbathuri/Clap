"""
M37I–M37L: Startup health checks, state hydration order, degraded resume.
"""

from __future__ import annotations

from pathlib import Path

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.state_durability.models import (
    StartupReadiness,
    RecoverablePartialState,
    PersistenceBoundary,
    CorruptedStateNote,
    StaleStateMarker,
)
from workflow_dataset.state_durability.boundaries import (
    collect_all_boundaries,
    collect_corrupt_notes,
    collect_stale_markers,
)


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


# Order in which subsystems are typically hydrated at startup (workday first, then continuity, project, etc.)
HYDRATION_ORDER = [
    "workday",
    "workday_preset",
    "continuity_shutdown",
    "continuity_next_session",
    "continuity_carry_forward",
    "project_current",
    "background_queue",
]


def build_startup_readiness(
    repo_root: Path | str | None = None,
    stale_hours: float = 24.0,
) -> StartupReadiness:
    """Build startup readiness: check all boundaries, aggregate ok/missing/corrupt/stale, set degraded if needed."""
    root = _root(repo_root)
    now = utc_now_iso()
    boundaries = collect_all_boundaries(root)
    corrupt = collect_corrupt_notes(root)
    stale = collect_stale_markers(root, stale_hours=stale_hours)

    ok_list: list[PersistenceBoundary] = []
    missing_list: list[PersistenceBoundary] = []
    for b in boundaries:
        if b.status == "ok":
            ok_list.append(b)
        elif b.status == "missing":
            missing_list.append(b)
        # corrupt already in corrupt list

    critical_ok = all(b.status == "ok" for b in boundaries if b.critical_for_startup)
    ready = critical_ok and len(corrupt) == 0
    degraded_but_usable = not ready and critical_ok  # e.g. only workday is critical; rest can be missing

    summary_lines: list[str] = []
    if ready:
        summary_lines.append("All critical state is present and readable.")
    else:
        if corrupt:
            summary_lines.append(f"{len(corrupt)} corrupt or unreadable state file(s).")
        if missing_list and any(b.critical_for_startup for b in missing_list):
            summary_lines.append("Some critical state is missing.")
        if not critical_ok:
            summary_lines.append("Startup may be degraded; run 'workflow-dataset state health' for details.")
    if stale:
        summary_lines.append(f"{len(stale)} subsystem(s) have stale state (older than {stale_hours}h).")

    recommended_first_action = "workflow-dataset continuity morning"
    if corrupt:
        recommended_first_action = "workflow-dataset state health"
    elif not ready and missing_list:
        recommended_first_action = "workflow-dataset day start" if "workday" in [m.subsystem_id for m in missing_list] else "workflow-dataset continuity morning"

    return StartupReadiness(
        ready=ready,
        generated_at_utc=now,
        boundaries=boundaries,
        corrupt_notes=corrupt,
        stale_markers=stale,
        hydration_order=HYDRATION_ORDER,
        degraded_but_usable=degraded_but_usable,
        summary_lines=summary_lines,
        recommended_first_action=recommended_first_action,
    )


def build_recoverable_partial_state(
    repo_root: Path | str | None = None,
    stale_hours: float = 24.0,
) -> RecoverablePartialState:
    """Build recoverable partial state: what is ok, missing, corrupt, stale; can we resume degraded; recommended actions."""
    root = _root(repo_root)
    boundaries = collect_all_boundaries(root)
    corrupt = collect_corrupt_notes(root)
    stale = collect_stale_markers(root, stale_hours=stale_hours)

    ok_list = [b for b in boundaries if b.status == "ok"]
    missing_list = [b for b in boundaries if b.status == "missing"]
    can_resume = all(b.status == "ok" for b in boundaries if b.critical_for_startup)
    actions: list[str] = []
    if corrupt:
        actions.append("Run 'workflow-dataset state health' and fix or restore corrupt files.")
    if missing_list and any(b.critical_for_startup for b in missing_list):
        actions.append("Run 'workflow-dataset day start' to initialize workday state.")
    if not actions:
        actions.append("Run 'workflow-dataset continuity morning' to resume.")

    return RecoverablePartialState(
        boundaries_ok=ok_list,
        boundaries_missing=missing_list,
        boundaries_corrupt=corrupt,
        boundaries_stale=stale,
        can_resume_degraded=can_resume,
        recommended_recovery_actions=actions,
    )
