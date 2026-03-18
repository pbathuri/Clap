"""
M39E–M39H: Vertical-specific defaults — apply recommended queue, calmness, operator, review posture.
Does not auto-apply trust or approval scope; only records recommendations and optional local prefs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.vertical_packs.registry import get_curated_pack
from workflow_dataset.vertical_packs.store import set_active_pack, get_active_pack


def apply_vertical_defaults(
    curated_pack_id: str,
    repo_root: Path | str | None = None,
    *,
    dry_run: bool = False,
    persist_active: bool = True,
) -> dict[str, Any]:
    """
    Apply curated vertical defaults for the given pack.
    - Sets active pack (persisted) if persist_active.
    - Returns summary: pack_id, value_pack_id, workday_preset_id, default_experience_profile_id,
      trust_preset_id, recommended_queue, recommended_workday, applied_commands (CLI hints for user to run).
    Does NOT change trust registry or approval scope; those require explicit user actions.
    """
    pack = get_curated_pack(curated_pack_id)
    if not pack:
        return {"error": f"Curated pack not found: {curated_pack_id}", "applied": False}
    root = Path(repo_root).resolve() if repo_root else None
    if not root:
        try:
            from workflow_dataset.path_utils import get_repo_root
            root = Path(get_repo_root()).resolve()
        except Exception:
            root = Path.cwd().resolve()
    applied_commands: list[str] = []
    if not dry_run and persist_active:
        set_active_pack(curated_pack_id, repo_root=root)
        applied_commands.append("(active pack set to " + curated_pack_id + ")")
    applied_commands.extend([
        f"# Workday: use preset {pack.workday_preset_id}",
        f"# Experience: workflow-dataset workspace home --profile {pack.default_experience_profile_id}",
        f"# Trust: workflow-dataset trust preset {pack.trust_review_posture.trust_preset_id} (apply explicitly if desired)",
        f"# First-value path: workflow-dataset vertical-packs first-value --id {curated_pack_id}",
    ])
    return {
        "pack_id": pack.pack_id,
        "value_pack_id": pack.value_pack_id,
        "workday_preset_id": pack.workday_preset_id,
        "default_experience_profile_id": pack.default_experience_profile_id,
        "trust_preset_id": pack.trust_review_posture.trust_preset_id,
        "recommended_queue": pack.recommended_queue.to_dict(),
        "recommended_workday": pack.recommended_workday.to_dict(),
        "applied_commands": applied_commands,
        "applied": not dry_run,
        "dry_run": dry_run,
    }


def get_recommended_commands_for_pack(curated_pack_id: str) -> list[str]:
    """Return list of recommended CLI commands for this vertical (for display only)."""
    pack = get_curated_pack(curated_pack_id)
    if not pack:
        return []
    return [
        f"workflow-dataset workspace home --profile {pack.default_experience_profile_id}",
        f"workflow-dataset value-packs first-run --id {pack.value_pack_id}",
        "workflow-dataset day status",
        "workflow-dataset trust cockpit",
    ]
