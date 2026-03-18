"""
M39E–M39H: First-value milestone tracking — next milestone, blocked step, strongest path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.vertical_packs.store import get_active_pack, get_path_progress
from workflow_dataset.vertical_packs.registry import get_curated_pack


def get_next_vertical_milestone(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Return next vertical milestone and path state from active pack and progress.
    Keys: active_curated_pack_id, path_id, next_milestone_id, next_milestone_label, reached_milestone_ids,
    blocked_step_index, strongest_value_path_id, suggested_next_command.
    """
    active = get_active_pack(repo_root)
    pack_id = active.get("active_curated_pack_id", "")
    if not pack_id:
        return {
            "active_curated_pack_id": "",
            "path_id": "",
            "next_milestone_id": "",
            "next_milestone_label": "",
            "reached_milestone_ids": [],
            "blocked_step_index": 0,
            "strongest_value_path_id": "",
            "suggested_next_command": "workflow-dataset vertical-packs list",
        }
    pack = get_curated_pack(pack_id)
    progress = get_path_progress(repo_root)
    path_id = progress.get("path_id", "") or (pack.first_value_path.path_id if pack and pack.first_value_path else "")
    reached = progress.get("reached_milestone_ids", [])
    next_id = progress.get("next_milestone_id", "")
    blocked = progress.get("blocked_step_index", 0)
    next_label = ""
    suggested = "workflow-dataset vertical-packs first-value --id " + pack_id
    if pack and pack.first_value_path:
        for m in pack.first_value_path.milestones:
            if m.milestone_id == next_id:
                next_label = m.label
                suggested = m.command_hint or suggested
                break
        if not next_id and pack.first_value_path.milestones:
            first = pack.first_value_path.milestones[0]
            next_id = first.milestone_id
            next_label = first.label
            suggested = first.command_hint or suggested
    return {
        "active_curated_pack_id": pack_id,
        "path_id": path_id,
        "next_milestone_id": next_id,
        "next_milestone_label": next_label,
        "reached_milestone_ids": list(reached),
        "blocked_step_index": blocked,
        "strongest_value_path_id": path_id,
        "suggested_next_command": suggested,
    }


def get_blocked_vertical_onboarding_step(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    If progress indicates a blocked step, return step_index, symptom, remediation_hint.
    Otherwise return empty dict or step_index 0.
    """
    progress = get_path_progress(repo_root)
    blocked = progress.get("blocked_step_index", 0)
    if not blocked:
        return {}
    pack_id = progress.get("pack_id", "")
    pack = get_curated_pack(pack_id)
    if not pack or not pack.first_value_path:
        return {"blocked_step_index": blocked, "symptom": "", "remediation_hint": "Check vertical-packs first-value --id " + pack_id}
    for fp in pack.first_value_path.common_failure_points:
        if fp.step_index == blocked:
            return {
                "blocked_step_index": blocked,
                "symptom": fp.symptom,
                "remediation_hint": fp.remediation_hint,
                "escalation_command": fp.escalation_command,
            }
    return {"blocked_step_index": blocked, "symptom": "", "remediation_hint": "Retry step or run suggested_next_command from vertical progress."}


def build_milestone_progress_output(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Full progress output for CLI/mission control: next milestone, blocked step, strongest path, suggested command.
    When blocked_step_index is set, includes operator_guidance_when_stalled from vertical playbook (M39H.1)."""
    out = get_next_vertical_milestone(repo_root)
    blocked_info = get_blocked_vertical_onboarding_step(repo_root)
    if blocked_info:
        out["blocked_onboarding_step"] = blocked_info
        pack_id = out.get("active_curated_pack_id", "")
        blocked = out.get("blocked_step_index", 0)
        if pack_id and blocked:
            from workflow_dataset.vertical_packs.playbooks import get_operator_guidance_when_stalled
            out["operator_guidance_when_stalled"] = get_operator_guidance_when_stalled(
                pack_id, blocked, repo_root=repo_root
            )
    return out
