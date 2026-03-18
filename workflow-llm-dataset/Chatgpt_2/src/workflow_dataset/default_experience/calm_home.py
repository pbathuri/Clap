"""
M37C: Calm default home — narrowed operating surface: focus, next action, approvals, carry-forward, project, quiet automation/health.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from workflow_dataset.workspace.models import WorkspaceHomeSnapshot


def format_calm_default_home(
    snapshot: "WorkspaceHomeSnapshot | None" = None,
    repo_root: Path | str | None = None,
) -> str:
    """Format a calmer default home: current focus, next action, urgent approvals, carry-forward, most relevant project, quiet automation/health. No areas list."""
    if snapshot is None:
        from workflow_dataset.workspace.state import build_workspace_home_snapshot
        snapshot = build_workspace_home_snapshot(repo_root)
    ctx = snapshot.context
    lines = [
        "=== Workspace Home (calm default) ===",
        "",
        "[Current focus]",
        f"  Project: {ctx.active_project_id or '—'}  {ctx.active_project_title or ''}",
        f"  Goal: {(ctx.active_goal_text[:60] + '…') if ctx.active_goal_text else '—'}",
        "",
        "[Next best action]",
        f"  {ctx.next_recommended_action or '—'}  — {(ctx.next_recommended_detail or '')[:80]}",
        f"  Next project: {snapshot.top_priority_project_id or ctx.next_recommended_project_id or '—'}",
        "",
        "[Urgent approvals / reviews]",
        f"  {snapshot.approval_queue_summary or '—'}",
        "",
        "[Carry-forward / resume]",
    ]
    # Resume hint from workday state
    try:
        from workflow_dataset.workday.store import load_workday_state
        from workflow_dataset.workday.models import WorkdayState
        record = load_workday_state(repo_root)
        if record.state == WorkdayState.RESUME_PENDING.value:
            lines.append("  Day is in resume state. Run: workflow-dataset day resume then day start")
        elif record.state == WorkdayState.NOT_STARTED.value:
            lines.append("  Day not started. Run: workflow-dataset day start")
        else:
            lines.append("  (no carry-forward)")
    except Exception:
        lines.append("  —")
    lines.extend([
        "",
        "[Most relevant project]",
        f"  {ctx.active_project_id or '—'}  {ctx.active_project_title or ''}",
        "",
        "[Automation / health]",
        f"  {snapshot.trust_health_summary or '—'}",
        "",
    ])
    try:
        from workflow_dataset.default_experience.disclosure_paths import format_show_more_footer
        for line in format_show_more_footer():
            lines.append(line)
    except Exception:
        lines.append("More: workflow-dataset workspace home  |  workflow-dataset day status  |  workflow-dataset defaults paths")
    return "\n".join(lines) + "\n"
