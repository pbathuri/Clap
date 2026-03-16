"""
M23K: Seed example routine. Optional.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.copilot.routines import Routine, save_routine


def seed_morning_routine(repo_root: Path | str | None = None) -> Path:
    """Create a morning reporting routine (single job: weekly_status_from_notes)."""
    r = Routine(
        routine_id="morning_reporting",
        title="Morning reporting",
        description="Run weekly status from notes (single job).",
        job_pack_ids=["weekly_status_from_notes"],
        ordering=None,
        stop_on_first_blocked=True,
        required_approvals=[],
        simulate_only=True,
        expected_outputs=[],
    )
    return save_routine(r, repo_root)
