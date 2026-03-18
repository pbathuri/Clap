"""
M37I–M37L: Resume target — best recommended first action from workday + continuity + project.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.state_durability.models import ResumeTarget


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_resume_target(repo_root: Path | str | None = None) -> ResumeTarget:
    """Build single best resume target from workday, continuity, and project. Fast path for most recent coherent state."""
    root = _root(repo_root)
    rationale: list[str] = []
    project_id = ""
    day_id = ""

    # Workday
    try:
        from workflow_dataset.workday.store import load_workday_state, current_day_id
        record = load_workday_state(root)
        day_id = record.day_id or current_day_id()
        if record.state == "resume_pending":
            rationale.append("Workday is resume_pending; good candidate for morning flow.")
        elif record.state and record.state != "not_started":
            rationale.append(f"Workday state: {record.state}.")
    except Exception:
        rationale.append("Workday state unavailable; will use continuity.")

    # Continuity: next session recommendation and strongest handoff
    try:
        from workflow_dataset.continuity_engine import get_strongest_resume_target, load_next_session_recommendation
        rec = load_next_session_recommendation(root)
        label, cmd = get_strongest_resume_target(root)
        if rec:
            if rec.first_action_label:
                label = rec.first_action_label
            if rec.first_action_command:
                cmd = rec.first_action_command
            day_id = day_id or rec.day_id or day_id
            rationale.append(f"Continuity: {rec.first_action_label or rec.first_action_command}")
            return ResumeTarget(
                label=label,
                command=cmd,
                quality="high" if (rec.carry_forward_count == 0 and not getattr(rec, "blocked_count", 0)) else "medium",
                rationale=rationale,
                project_id=project_id,
                day_id=day_id,
            )
    except Exception:
        pass

    # Fallback: continuity morning
    try:
        from workflow_dataset.continuity_engine import get_strongest_resume_target
        label, cmd = get_strongest_resume_target(root)
        return ResumeTarget(
            label=label,
            command=cmd,
            quality="medium",
            rationale=rationale + ["Using continuity handoff."],
            project_id=project_id,
            day_id=day_id,
        )
    except Exception:
        pass

    # Project as hint
    try:
        from workflow_dataset.project_case.store import get_current_project_id
        project_id = get_current_project_id(root) or ""
        if project_id:
            rationale.append(f"Active project: {project_id}")
            return ResumeTarget(
                label="Open workspace",
                command="workflow-dataset workspace open",
                quality="low",
                rationale=rationale,
                project_id=project_id,
                day_id=day_id,
            )
    except Exception:
        pass

    return ResumeTarget(
        label="Run morning flow",
        command="workflow-dataset continuity morning",
        quality="low",
        rationale=rationale or ["No prior state; start with morning flow."],
        day_id=day_id,
    )
