"""
M40L.1: Sustained-use checkpoints — assess at usage milestones (sessions, days).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workflow_dataset.production_launch.models import SustainedUseCheckpoint
from workflow_dataset.production_launch.post_deployment_guidance import build_post_deployment_guidance


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _checkpoints_path(root: Path) -> Path:
    return root / "data/local/production_launch/sustained_use_checkpoints.json"


# Thresholds for checkpoint kinds (sessions or days)
SUSTAINED_USE_KINDS = {
    "session_5": {"min_sessions": 5, "label": "After 5 sessions"},
    "session_10": {"min_sessions": 10, "label": "After 10 sessions"},
    "day_7": {"min_days": 7, "label": "After 7 days"},
    "auto": {"label": "Auto (from current state)"},
}


def _get_sessions_and_days_context(root: Path) -> dict[str, Any]:
    """Infer sessions count and days-in-use context from cohort/outcomes/dashboard."""
    ctx: dict[str, Any] = {"sessions_count": 0, "days_estimate": 0, "source": "unknown"}
    try:
        from workflow_dataset.release.dashboard_data import get_dashboard_data
        dash = get_dashboard_data(repo_root=root)
        cohort = dash.get("cohort", {})
        ctx["sessions_count"] = cohort.get("sessions_count", 0) or 0
        ctx["source"] = "dashboard"
    except Exception:
        pass
    try:
        from workflow_dataset.outcomes.store import list_session_outcomes
        outcomes = list_session_outcomes(limit=100, repo_root=root)
        if outcomes and ctx["sessions_count"] == 0:
            ctx["sessions_count"] = len(outcomes)
            ctx["source"] = "outcomes"
    except Exception:
        pass
    # Rough days: if we had outcomes or sessions, assume at least 1 day; no real "first use" timestamp without extra state
    ctx["days_estimate"] = 1 if ctx["sessions_count"] > 0 else 0
    return ctx


def build_sustained_use_checkpoint(
    repo_root: Path | str | None = None,
    kind: str = "auto",
) -> dict[str, Any]:
    """
    Build sustained-use checkpoint report. kind: session_5 | session_10 | day_7 | auto.
    Auto picks session_5/session_10/day_7 based on current sessions/days.
    """
    root = _repo_root(repo_root)
    now = datetime.now(timezone.utc)
    at_iso = now.isoformat()[:19] + "Z"
    ctx = _get_sessions_and_days_context(root)
    sessions = ctx.get("sessions_count", 0)
    days = ctx.get("days_estimate", 0)

    if kind == "auto":
        if sessions >= 10:
            kind = "session_10"
        elif sessions >= 5:
            kind = "session_5"
        elif days >= 7 or sessions > 0:
            kind = "day_7"
        else:
            kind = "session_5"  # default to session_5 threshold for criteria

    meta = SUSTAINED_USE_KINDS.get(kind, {"label": kind})
    min_sessions = meta.get("min_sessions", 0)
    min_days = meta.get("min_days", 0)
    criteria_met = (min_sessions and sessions >= min_sessions) or (min_days and days >= min_days) or (kind == "day_7" and sessions > 0)

    guidance_result = build_post_deployment_guidance(root)
    guidance = guidance_result.get("guidance", "continue")
    if guidance in ("rollback", "repair"):
        criteria_met = False
    recommended_actions = guidance_result.get("recommended_actions", [])

    report_summary = f"Sessions={sessions} days_est={days} kind={kind}. Criteria_met={criteria_met}. Guidance={guidance}."
    checkpoint_id = f"{kind}_{at_iso[:10]}_{now.hour:02d}{now.minute:02d}"

    checkpoint = SustainedUseCheckpoint(
        checkpoint_id=checkpoint_id,
        kind=kind,
        at_iso=at_iso,
        criteria_met=criteria_met,
        report_summary=report_summary,
        sessions_or_days_context=ctx,
        guidance=guidance,
        recommended_actions=recommended_actions,
    )
    return {
        "checkpoint": checkpoint.to_dict(),
        "post_deployment_guidance": guidance_result,
        "criteria_met": criteria_met,
        "next_recommended": "Run another checkpoint after more sessions or schedule day_7." if criteria_met else "Address guidance (repair/rollback) then re-run checkpoint.",
    }


def record_sustained_use_checkpoint(
    repo_root: Path | str | None = None,
    kind: str = "auto",
) -> Path:
    """Build and append checkpoint to sustained_use_checkpoints.json; return path."""
    root = _repo_root(repo_root)
    data = build_sustained_use_checkpoint(root, kind=kind)
    path = _checkpoints_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    if path.exists():
        try:
            records = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(records, list):
                records = []
        except Exception:
            records = []
    records.append(data["checkpoint"])
    path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return path


def list_sustained_use_checkpoints(repo_root: Path | str | None = None, limit: int = 10) -> list[dict[str, Any]]:
    """List recorded checkpoints (newest first)."""
    root = _repo_root(repo_root)
    path = _checkpoints_path(root)
    if not path.exists():
        return []
    try:
        records = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(records, list):
            return []
        return list(reversed(records[-limit:]))
    except Exception:
        return []
