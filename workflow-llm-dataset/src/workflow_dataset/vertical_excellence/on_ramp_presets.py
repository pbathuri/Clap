"""
M47D.1: Faster on-ramp presets — compressed step sets for quick first value.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.vertical_excellence.models import OnRampPreset
from workflow_dataset.vertical_excellence.path_resolver import (
    build_first_value_path_for_vertical,
    get_chosen_vertical_id,
)

PRESET_MINIMAL = "minimal"
PRESET_STANDARD = "standard"
PRESET_FULL = "full"


def list_on_ramp_presets() -> list[OnRampPreset]:
    """Return built-in on-ramp presets."""
    return [
        OnRampPreset(
            preset_id=PRESET_MINIMAL,
            label="Minimal — 3 steps to first value",
            description="Fastest on-ramp: profile bootstrap, onboard status, one simulate.",
            step_count=3,
            step_indices=[1, 3, 6],  # bootstrap, onboard, first simulate
            entry_point="workflow-dataset profile bootstrap",
            suggested_for="new_user",
        ),
        OnRampPreset(
            preset_id=PRESET_STANDARD,
            label="Standard — 5 steps to first value",
            description="Profile, runtime, onboard, inbox, first simulate.",
            step_count=5,
            step_indices=[1, 2, 3, 5, 6],
            entry_point="workflow-dataset profile bootstrap",
            suggested_for="both",
        ),
        OnRampPreset(
            preset_id=PRESET_FULL,
            label="Full — all steps",
            description="Complete first-value flow: all 6 steps.",
            step_count=6,
            step_indices=[1, 2, 3, 4, 5, 6],
            entry_point="workflow-dataset profile bootstrap",
            suggested_for="new_user",
        ),
    ]


def get_on_ramp_preset(preset_id: str) -> OnRampPreset | None:
    """Return preset by id (minimal | standard | full)."""
    for p in list_on_ramp_presets():
        if p.preset_id == preset_id:
            return p
    return None


def build_path_with_preset(
    vertical_id: str,
    preset_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any] | None:
    """
    Build first-value path filtered to preset step indices.
    Returns dict with entry_point, steps (list of {step_number, title, command}), preset_id.
    """
    preset = get_on_ramp_preset(preset_id)
    if preset is None:
        return None
    path = build_first_value_path_for_vertical(vertical_id, repo_root)
    if path is None:
        return None
    steps = getattr(path, "steps", []) or []
    indices_set = set(preset.step_indices)
    filtered = [
        {"step_number": getattr(s, "step_number", i), "title": getattr(s, "title", ""), "command": getattr(s, "command", "")}
        for i, s in enumerate(steps, 1)
        if i in indices_set
    ]
    return {
        "vertical_id": vertical_id,
        "preset_id": preset_id,
        "entry_point": preset.entry_point or (filtered[0]["command"] if filtered else ""),
        "steps": filtered,
        "step_count": len(filtered),
        "label": preset.label,
        "suggested_for": preset.suggested_for,
    }
