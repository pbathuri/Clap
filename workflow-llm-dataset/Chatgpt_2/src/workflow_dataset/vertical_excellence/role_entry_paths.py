"""
M47D.1: Role-tuned first-value entry paths inside the chosen vertical.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.vertical_excellence.models import RoleTunedEntryPath
from workflow_dataset.vertical_excellence.path_resolver import (
    build_first_value_path_for_vertical,
    get_chosen_vertical_id,
)

SUPPORTED_ROLES = ("operator", "reviewer", "analyst")
DEFAULT_ROLE = "operator"


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _steps_from_path(path: Any) -> list[tuple[str, str]]:
    """Return list of (title, command) from path.steps."""
    out: list[tuple[str, str]] = []
    steps = getattr(path, "steps", []) or []
    for s in steps:
        title = getattr(s, "title", "") or ""
        cmd = getattr(s, "command", "") or ""
        out.append((title, cmd))
    return out


def get_role_tuned_entry_path(
    vertical_id: str,
    role_id: str,
    repo_root: Path | str | None = None,
) -> RoleTunedEntryPath | None:
    """
    Build role-tuned first-value entry path for the vertical.
    operator: full path, portfolio/approvals first.
    reviewer: queue/review-first (onboard, inbox, review).
    analyst: focus-first (profile, runtime, focus-ready jobs).
    """
    root = _root(repo_root)
    path = build_first_value_path_for_vertical(vertical_id, root)
    if path is None:
        return None
    steps = _steps_from_path(path)
    entry = getattr(path, "entry_point", "") or (steps[0][1] if steps else "")
    role = role_id if role_id in SUPPORTED_ROLES else DEFAULT_ROLE

    if role == "operator":
        return RoleTunedEntryPath(
            vertical_id=vertical_id,
            role_id="operator",
            label="Operator entry — portfolio and approvals first",
            entry_point=entry,
            step_titles=[t for t, _ in steps],
            step_commands=[c for _, c in steps],
            first_value_outcome="First simulate run; approvals in place for real run.",
            best_next_after_entry="workflow-dataset day status",
        )
    if role == "reviewer":
        # Reviewer: onboard → inbox → review; fewer steps to first “review value”
        titles, commands = [], []
        for i, (t, c) in enumerate(steps):
            if any(x in c.lower() for x in ("onboard", "inbox", "queue", "review", "approval")):
                titles.append(t)
                commands.append(c)
        if not commands:
            titles = [t for t, _ in steps[:4]]
            commands = [c for _, c in steps[:4]]
        return RoleTunedEntryPath(
            vertical_id=vertical_id,
            role_id="reviewer",
            label="Reviewer entry — queue and approvals first",
            entry_point=commands[0] if commands else entry,
            step_titles=titles,
            step_commands=commands,
            first_value_outcome="First review cycle; inbox and approval status visible.",
            best_next_after_entry="workflow-dataset queue",
        )
    if role == "analyst":
        # Analyst: profile, runtime, focus work (jobs list / focus-ready)
        titles, commands = [], []
        for t, c in steps:
            if any(x in c.lower() for x in ("profile", "runtime", "jobs", "inbox", "focus")):
                titles.append(t)
                commands.append(c)
        if not commands:
            titles = [t for t, _ in steps[:5]]
            commands = [c for _, c in steps[:5]]
        return RoleTunedEntryPath(
            vertical_id=vertical_id,
            role_id="analyst",
            label="Analyst entry — focus work first",
            entry_point=commands[0] if commands else entry,
            step_titles=titles,
            step_commands=commands,
            first_value_outcome="First focus session; jobs list and inbox ready.",
            best_next_after_entry="workflow-dataset workspace home",
        )
    return RoleTunedEntryPath(
        vertical_id=vertical_id,
        role_id=role,
        label=f"Entry path for {role}",
        entry_point=entry,
        step_titles=[t for t, _ in steps],
        step_commands=[c for _, c in steps],
        first_value_outcome="First value reached.",
        best_next_after_entry="workflow-dataset day status",
    )


def get_role_tuned_entry_path_for_chosen_vertical(
    role_id: str,
    repo_root: Path | str | None = None,
) -> RoleTunedEntryPath | None:
    """Convenience: role-tuned path for current chosen vertical."""
    vid = get_chosen_vertical_id(repo_root)
    return get_role_tuned_entry_path(vid, role_id, repo_root)
