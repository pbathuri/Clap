"""
M23L: Context history and drift. Compare two work-state snapshots.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from workflow_dataset.context.work_state import WorkState
from workflow_dataset.context.snapshot import load_snapshot


@dataclass
class ContextDrift:
    """What changed between two work-state snapshots."""
    newly_recommendable_jobs: list[str] = field(default_factory=list)
    newly_blocked_jobs: list[str] = field(default_factory=list)
    approvals_changed: bool = False
    approvals_summary: str = ""
    intake_labels_added: list[str] = field(default_factory=list)
    intake_labels_removed: list[str] = field(default_factory=list)
    reminders_count_change: int = 0
    routines_count_change: int = 0
    recent_workspaces_count_change: int = 0
    unreviewed_count_change: int = 0
    summary: list[str] = field(default_factory=list)


def compare_snapshots(
    older: WorkState | dict[str, Any],
    newer: WorkState | dict[str, Any],
) -> ContextDrift:
    """
    Compare two work states. 'older' is baseline, 'newer' is current.
    Returns drift: newly recommendable (in newer recent_successful or trusted, not in older), newly blocked, etc.
    """
    def to_dict(ws: WorkState | dict) -> dict:
        if isinstance(ws, dict):
            return ws
        from workflow_dataset.context.work_state import work_state_to_dict
        return work_state_to_dict(ws)

    a = to_dict(older)
    b = to_dict(newer)

    drift = ContextDrift()

    # Jobs: newly in recent_successful or trusted in b but not in a
    a_success = {r.get("job_pack_id") for r in a.get("recent_successful_jobs", []) if r.get("job_pack_id")}
    b_success = {r.get("job_pack_id") for r in b.get("recent_successful_jobs", []) if r.get("job_pack_id")}
    a_trusted = set(a.get("trusted_for_real_jobs", []))
    b_trusted = set(b.get("trusted_for_real_jobs", []))
    a_blocked = set(a.get("approval_blocked_jobs", []))
    b_blocked = set(b.get("approval_blocked_jobs", []))

    newly_ok = (b_success | b_trusted) - (a_success | a_trusted) - b_blocked
    drift.newly_recommendable_jobs = sorted(newly_ok)

    newly_blocked = b_blocked - a_blocked
    drift.newly_blocked_jobs = sorted(newly_blocked)

    # Approvals
    a_approvals = a.get("approvals_file_exists") and (a.get("approved_paths_count", 0) + a.get("approved_action_scopes_count", 0))
    b_approvals = b.get("approvals_file_exists") and (b.get("approved_paths_count", 0) + b.get("approved_action_scopes_count", 0))
    drift.approvals_changed = a_approvals != b_approvals
    drift.approvals_summary = f"older: paths={a.get('approved_paths_count', 0)} scopes={a.get('approved_action_scopes_count', 0)}  newer: paths={b.get('approved_paths_count', 0)} scopes={b.get('approved_action_scopes_count', 0)}"

    # Intake
    a_labels = set(a.get("intake_labels", []))
    b_labels = set(b.get("intake_labels", []))
    drift.intake_labels_added = sorted(b_labels - a_labels)
    drift.intake_labels_removed = sorted(a_labels - b_labels)

    # Counts
    drift.reminders_count_change = b.get("reminders_count", 0) - a.get("reminders_count", 0)
    drift.routines_count_change = b.get("routines_count", 0) - a.get("routines_count", 0)
    drift.recent_workspaces_count_change = b.get("recent_workspaces_count", 0) - a.get("recent_workspaces_count", 0)
    drift.unreviewed_count_change = b.get("unreviewed_count", 0) - a.get("unreviewed_count", 0)

    # Summary lines
    if drift.newly_recommendable_jobs:
        drift.summary.append(f"Newly recommendable jobs: {', '.join(drift.newly_recommendable_jobs)}")
    if drift.newly_blocked_jobs:
        drift.summary.append(f"Newly blocked jobs: {', '.join(drift.newly_blocked_jobs)}")
    if drift.approvals_changed:
        drift.summary.append("Approvals changed: " + drift.approvals_summary)
    if drift.intake_labels_added:
        drift.summary.append(f"Intake added: {', '.join(drift.intake_labels_added)}")
    if drift.intake_labels_removed:
        drift.summary.append(f"Intake removed: {', '.join(drift.intake_labels_removed)}")
    if drift.reminders_count_change != 0:
        drift.summary.append(f"Reminders count change: {drift.reminders_count_change:+d}")
    if drift.unreviewed_count_change != 0:
        drift.summary.append(f"Unreviewed workspaces change: {drift.unreviewed_count_change:+d}")
    if not drift.summary:
        drift.summary.append("No significant drift detected.")

    return drift


def load_latest_and_previous(
    repo_root: Path | str | None = None,
) -> tuple[WorkState | None, WorkState | None]:
    """Load latest and previous snapshots for compare. Returns (latest, previous)."""
    latest = load_snapshot("latest", repo_root)
    previous = load_snapshot("previous", repo_root)
    return (latest, previous)
