"""
M47A–M47B: Resolve chosen vertical and build first-value / repeat-value paths.
Authority: production_cut first, then vertical_packs active pack, then default.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

DEFAULT_VERTICAL_PACK_ID = "founder_operator_core"


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_chosen_vertical_id(repo_root: Path | str | None = None) -> str:
    """
    Return the chosen vertical id for excellence layer.
    Prefer production_cut.vertical_id when cut is set; else active pack id; else default.
    """
    root = _root(repo_root)
    try:
        from workflow_dataset.production_cut import get_active_cut
        cut = get_active_cut(root)
        if cut and getattr(cut, "vertical_id", None):
            return cut.vertical_id
    except Exception:
        pass
    try:
        from workflow_dataset.vertical_packs.store import get_active_pack
        active = get_active_pack(root)
        pack_id = active.get("active_curated_pack_id", "") or ""
        if pack_id:
            return pack_id
    except Exception:
        pass
    return DEFAULT_VERTICAL_PACK_ID


def build_first_value_path_for_vertical(
    vertical_id: str,
    repo_root: Path | str | None = None,
) -> Any:
    """
    Build first-value path for the given vertical.
    Uses vertical_packs.paths.build_path_for_pack(vertical_id); if None, falls back to
    operator_quickstart first_value_flow and adapts to FirstValuePath-like structure for reporting.
    """
    try:
        from workflow_dataset.vertical_packs.paths import build_path_for_pack
        path = build_path_for_pack(vertical_id)
        if path is not None:
            return path
    except Exception:
        pass
    # Fallback: generic first-value flow from operator_quickstart
    root = _root(repo_root)
    try:
        from workflow_dataset.operator_quickstart.first_value_flow import build_first_value_flow
        from workflow_dataset.vertical_packs.models import (
            FirstValuePath,
            FirstValuePathStep,
            SuccessMilestone,
            CommonFailurePoint,
        )
        flow = build_first_value_flow(root)
        steps_raw = flow.get("steps", [])
        steps = [
            FirstValuePathStep(
                s["step"],
                s.get("title", ""),
                s.get("command", ""),
                s.get("description", ""),
                s.get("suggested_next", ""),
                s.get("run_read_only", False),
                "",
            )
            for s in steps_raw
        ]
        return FirstValuePath(
            path_id=f"{vertical_id}_first_value_fallback",
            pack_id=vertical_id,
            label=f"First-value path for {vertical_id}",
            entry_point=steps[0].command if steps else "workflow-dataset profile bootstrap",
            required_surface_ids=[],
            steps=steps,
            milestones=[],
            suggested_next_actions=[s.get("suggested_next", "") for s in steps_raw if s.get("suggested_next")],
            first_value_milestone_id="first_simulate_done",
            common_failure_points=[
                CommonFailurePoint(1, "Bootstrap fails", "Run from repo root", "workflow-dataset profile bootstrap"),
                CommonFailurePoint(3, "Onboard not approved", "Run onboard approve", "workflow-dataset onboard status"),
            ],
        )
    except Exception:
        return None


def build_repeat_value_path_for_vertical(
    vertical_id: str,
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    """
    Build repeat-value path (high-frequency workflows) for the vertical.
    Delegates to vertical_speed list_frequent_workflows(vertical_pack_id=vertical_id).
    """
    try:
        from workflow_dataset.vertical_speed.identification import list_frequent_workflows
        workflows = list_frequent_workflows(repo_root=repo_root, vertical_pack_id=vertical_id)
        return [w.to_dict() for w in workflows]
    except Exception:
        return []
