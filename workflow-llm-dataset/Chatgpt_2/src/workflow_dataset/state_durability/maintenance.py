"""
M37I–M37L: Long-run state maintenance — stale cleanup, partial reconciliation, readiness summary.
Inspectable and local; no blind overwrites.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.state_durability.boundaries import (
    collect_all_boundaries,
    collect_stale_markers,
    collect_corrupt_notes,
)
from workflow_dataset.state_durability.models import DurableStateSnapshot
from workflow_dataset.state_durability.startup_health import build_startup_readiness, build_recoverable_partial_state


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_stale_cleanup_report(
    repo_root: Path | str | None = None,
    stale_hours: float = 24.0,
) -> dict[str, Any]:
    """Report what could be cleaned (stale markers); does NOT delete. Inspectable only."""
    root = _root(repo_root)
    stale = collect_stale_markers(root, stale_hours=stale_hours)
    return {
        "generated_at_utc": utc_now_iso(),
        "stale_threshold_hours": stale_hours,
        "stale_subsystems": [s.subsystem_id for s in stale],
        "stale_details": [s.to_dict() for s in stale],
        "recommendation": "No automatic cleanup; optional: run continuity shutdown to refresh shutdown/carry-forward, or ignore if intentional.",
    }


def build_reconcile_report(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Report partial state and suggested reconciliation steps; does NOT write. Inspectable only."""
    root = _root(repo_root)
    partial = build_recoverable_partial_state(root)
    readiness = build_startup_readiness(root)
    return {
        "generated_at_utc": utc_now_iso(),
        "can_resume_degraded": partial.can_resume_degraded,
        "boundaries_ok_count": len(partial.boundaries_ok),
        "boundaries_missing_count": len(partial.boundaries_missing),
        "boundaries_corrupt_count": len(partial.boundaries_corrupt),
        "recommended_actions": partial.recommended_recovery_actions,
        "readiness_summary": readiness.summary_lines,
    }


def build_durable_snapshot(
    repo_root: Path | str | None = None,
    stale_hours: float = 24.0,
) -> DurableStateSnapshot:
    """Build full durable state snapshot (readiness + resume target + partial state)."""
    try:
        from workflow_dataset.utils.hashes import stable_id
    except Exception:
        def stable_id(*parts: str, prefix: str = "") -> str:
            import hashlib
            return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:14]
    root = _root(repo_root)
    readiness = build_startup_readiness(root, stale_hours=stale_hours)
    partial = build_recoverable_partial_state(root, stale_hours=stale_hours)
    from workflow_dataset.state_durability.resume_target import build_resume_target
    resume = build_resume_target(root)
    now = utc_now_iso()
    snapshot_id = stable_id("snap", now[:16], prefix="snap_")
    summary_lines = list(readiness.summary_lines)
    return DurableStateSnapshot(
        snapshot_id=snapshot_id,
        generated_at_utc=now,
        readiness=readiness,
        resume_target=resume,
        partial_state=partial,
        summary_lines=summary_lines,
    )


def build_startup_readiness_summary(
    repo_root: Path | str | None = None,
    stale_hours: float = 24.0,
) -> list[str]:
    """Short summary lines for startup-time display (e.g. in mission control or CLI)."""
    readiness = build_startup_readiness(repo_root=repo_root, stale_hours=stale_hours)
    return readiness.summary_lines or ["State not checked."]
