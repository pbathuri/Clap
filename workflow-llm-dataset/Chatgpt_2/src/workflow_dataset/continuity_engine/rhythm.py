"""
M36L.1: Daily rhythm templates — list, get, recommend first phase/action for morning.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.continuity_engine.models import DailyRhythmTemplate, RhythmPhase
from workflow_dataset.continuity_engine.store import (
    load_rhythm_templates,
    get_active_rhythm_template_id,
)


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def list_rhythm_templates(repo_root: Path | str | None = None) -> list[DailyRhythmTemplate]:
    """Return all available daily rhythm templates (from store or built-in defaults)."""
    return load_rhythm_templates(repo_root=repo_root)


def get_rhythm_template(
    template_id: str | None = None, repo_root: Path | str | None = None
) -> DailyRhythmTemplate | None:
    """Return the template by id; if template_id is None, use active template."""
    root = _root(repo_root)
    tid = template_id or get_active_rhythm_template_id(root)
    for t in load_rhythm_templates(repo_root=root):
        if t.template_id == tid:
            return t
    return None


def get_default_first_action_for_phase(
    phase_id: str, repo_root: Path | str | None = None
) -> tuple[str, str]:
    """Return (phase_label, command) for the given phase_id from active template."""
    t = get_rhythm_template(repo_root=repo_root)
    if not t:
        return "Morning check", "workflow-dataset continuity morning"
    for p in t.phases:
        if p.phase_id == phase_id and p.default_first_action_command:
            return p.label, p.default_first_action_command
    if t.phases:
        first = min(t.phases, key=lambda x: x.order)
        return first.label, first.default_first_action_command or "workflow-dataset continuity morning"
    return "Morning check", "workflow-dataset continuity morning"


def get_recommended_first_phase(
    repo_root: Path | str | None = None,
) -> tuple[str, str, str]:
    """Return (phase_id, phase_label, command) for recommended first phase (default_first_phase_id or first in order)."""
    t = get_rhythm_template(repo_root=repo_root)
    if not t:
        return "morning_check", "Morning check", "workflow-dataset continuity morning"
    target_id = t.default_first_phase_id or (t.phases[0].phase_id if t.phases else "morning_check")
    for p in t.phases:
        if p.phase_id == target_id:
            return (
                p.phase_id,
                p.label,
                p.default_first_action_command or "workflow-dataset continuity morning",
            )
    if t.phases:
        first = min(t.phases, key=lambda x: x.order)
        return (
            first.phase_id,
            first.label,
            first.default_first_action_command or "workflow-dataset continuity morning",
        )
    return "morning_check", "Morning check", "workflow-dataset continuity morning"
