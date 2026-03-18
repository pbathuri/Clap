"""
M47D: Format first-value path report, friction-point report, recommend-next output.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.vertical_excellence.compression import (
    assess_first_value_stage,
    list_ambiguity_points,
    list_blocked_first_value_cases,
    list_friction_points,
)
from workflow_dataset.vertical_excellence.path_resolver import (
    build_first_value_path_for_vertical,
    build_repeat_value_path_for_vertical,
    get_chosen_vertical_id,
)
from workflow_dataset.vertical_excellence.recommend_next import recommend_next_for_vertical


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def format_first_value_path_report(repo_root: Path | str | None = None) -> str:
    """Produce a human-readable first-value path report for the chosen vertical."""
    root = _root(repo_root)
    vertical_id = get_chosen_vertical_id(root)
    path = build_first_value_path_for_vertical(vertical_id, root)
    stage = assess_first_value_stage(root)
    lines = [
        "[Vertical excellence] First-value path report",
        "vertical_id=" + vertical_id,
        "stage: " + stage.status + " (step " + str(stage.step_index) + "/" + str(stage.total_steps) + ")",
        "next_command_hint: " + (stage.next_command_hint or "—"),
        "",
    ]
    if path is None:
        lines.append("path: (none — use value-packs first-run or production-cut lock)")
        return "\n".join(lines)
    lines.append("path_id=" + getattr(path, "path_id", ""))
    lines.append("entry_point=" + getattr(path, "entry_point", ""))
    steps = getattr(path, "steps", []) or []
    for s in steps:
        cmd = getattr(s, "command", "")
        title = getattr(s, "title", "")
        lines.append("  step " + str(getattr(s, "step_number", 0)) + ": " + title + "  # " + cmd)
    lines.append("")
    return "\n".join(lines)


def format_friction_point_report(repo_root: Path | str | None = None) -> str:
    """Produce a human-readable friction-point report."""
    root = _root(repo_root)
    frictions = list_friction_points(root)
    blocked = list_blocked_first_value_cases(root)
    lines = [
        "[Vertical excellence] Friction points report",
        "friction_count=" + str(len(frictions)),
        "blocked_first_value_cases=" + str(len(blocked)),
        "",
    ]
    for f in frictions:
        lines.append("  " + f.friction_id + "  kind=" + f.kind + "  step=" + str(f.step_index))
        lines.append("    label: " + f.label)
        if f.remediation_hint:
            lines.append("    remediation: " + f.remediation_hint)
        if f.escalation_command:
            lines.append("    escalation: " + f.escalation_command)
    for b in blocked:
        lines.append("  blocked: " + b.get("reason", "") + " at step " + str(b.get("step_index", 0)) + "  hint: " + str(b.get("hint", "")))
    return "\n".join(lines)


def format_recommend_next(repo_root: Path | str | None = None) -> str:
    """Produce human-readable recommend-next output."""
    rec = recommend_next_for_vertical(repo_root)
    if rec is None:
        return "[Vertical excellence] recommend-next: (no recommendation)"
    lines = [
        "[Vertical excellence] Recommend next",
        "command: " + rec.command,
        "label: " + rec.label,
        "rationale: " + rec.rationale,
    ]
    return "\n".join(lines)
