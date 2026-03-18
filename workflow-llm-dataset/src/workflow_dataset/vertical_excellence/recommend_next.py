"""
M47C + M47D.1: Recommend next action — first-value path, blocked recovery, new vs returning user.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from workflow_dataset.vertical_excellence.compression import (
    assess_first_value_stage,
    list_blocked_first_value_cases,
)
from workflow_dataset.vertical_excellence.path_resolver import get_chosen_vertical_id
from workflow_dataset.vertical_excellence.role_entry_paths import get_role_tuned_entry_path_for_chosen_vertical
from workflow_dataset.vertical_excellence.on_ramp_presets import get_on_ramp_preset, PRESET_MINIMAL


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


@dataclass
class NextRecommendation:
    """Single recommended next action with rationale."""
    command: str
    label: str
    rationale: str


def recommend_next_for_vertical(
    repo_root: Path | str | None = None,
    user_recency: str | None = None,  # "new" | "returning" | None (auto)
    role_id: str | None = None,
) -> NextRecommendation | None:
    """
    Recommend the next action for the chosen vertical.
    Prefer: (1) recover from blocked first-value, (2) next step on first-value path, (3) start first-value path.
    M47D.1: When user_recency="new", use role-tuned or minimal on-ramp entry. When "returning", prefer day status / queue.
    """
    root = _root(repo_root)
    vertical_id = get_chosen_vertical_id(root)
    if not vertical_id:
        return NextRecommendation(
            command="workflow-dataset production-cut lock --id founder_operator_core",
            label="Set chosen vertical",
            rationale="No chosen vertical; lock production cut to focus first-value path.",
        )
    blocked = list_blocked_first_value_cases(root)
    if blocked:
        b = blocked[0]
        hint = b.get("hint", "workflow-dataset vertical-excellence friction-points")
        cmd = hint if isinstance(hint, str) and hint.startswith("workflow-dataset") else "workflow-dataset vertical-excellence friction-points"
        return NextRecommendation(
            command=cmd,
            label="Recover from blocked first-value",
            rationale=hint if isinstance(hint, str) else "Blocked at step {}.".format(b.get("step_index", 0)),
        )
    stage = assess_first_value_stage(root)

    # M47D.1: Returning user — best next is day status or queue
    if user_recency == "returning":
        if stage.status == "first_value_reached" or stage.status == "completed":
            return NextRecommendation(
                command=stage.next_command_hint or "workflow-dataset day status",
                label="Best next (returning)",
                rationale="Resume: day status then queue or workspace.",
            )
        return NextRecommendation(
            command="workflow-dataset day status",
            label="Best next (returning)",
            rationale="Quick re-entry: day status then queue or continuity.",
        )

    # First value already reached
    if stage.status == "first_value_reached" or stage.status == "completed":
        return NextRecommendation(
            command=stage.next_command_hint or "workflow-dataset day status",
            label="Continue after first value",
            rationale="First value reached; use day status or suggested next to continue.",
        )

    # M47D.1: New user — role-tuned or minimal on-ramp entry
    if user_recency == "new" or (stage.status == "not_started" and user_recency is None):
        role = role_id or "operator"
        role_path = get_role_tuned_entry_path_for_chosen_vertical(role, root)
        if role_path and role_path.step_commands:
            entry_cmd = role_path.entry_point or role_path.step_commands[0]
            return NextRecommendation(
                command=entry_cmd,
                label="Start here (new user)" if user_recency == "new" else "Start first-value path",
                rationale=role_path.label + "; then " + role_path.best_next_after_entry + ".",
            )
        minimal = get_on_ramp_preset(PRESET_MINIMAL)
        entry_cmd = minimal.entry_point if minimal else "workflow-dataset profile bootstrap"
        return NextRecommendation(
            command=entry_cmd,
            label="Start here (new user)" if user_recency == "new" else "Start first-value path",
            rationale="Fastest on-ramp: profile bootstrap, onboard, first simulate.",
        )

    # In progress
    return NextRecommendation(
        command=stage.next_command_hint or "workflow-dataset vertical-excellence first-value",
        label="Next step on first-value path",
        rationale="Step {} of {}: run the suggested command to advance.".format(stage.step_index, stage.total_steps),
    )
