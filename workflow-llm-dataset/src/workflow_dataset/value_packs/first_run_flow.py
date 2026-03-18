"""
M24B: Build concrete first-value flow sequence for a value pack: install/bootstrap → first simulate → first trusted-real candidate.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.value_packs.models import ValuePack
from workflow_dataset.value_packs.registry import get_value_pack


def build_first_run_flow(
    pack_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Build first-value flow for a value pack. Returns steps (list of {step, title, command, what_user_sees, what_to_do_next}),
    pack, pack_id.
    """
    pack = get_value_pack(pack_id)
    if not pack:
        return {"pack_id": pack_id, "pack": None, "steps": [], "error": f"Value pack not found: {pack_id}"}

    steps: list[dict[str, Any]] = []
    for s in pack.first_value_sequence:
        steps.append({
            "step": s.step_number,
            "title": s.title,
            "command": s.command,
            "what_user_sees": s.what_user_sees or "",
            "what_to_do_next": s.what_to_do_next or "",
            "run_read_only": s.run_read_only,
        })
    return {
        "pack_id": pack_id,
        "pack": pack,
        "steps": steps,
    }


def get_sample_asset_path(relative_path: str, repo_root: Path | str | None = None) -> Path | None:
    """Resolve sample asset path under data/local/value_packs/samples/. Returns None if not present."""
    root = Path(repo_root) if repo_root else None
    if not root:
        try:
            from workflow_dataset.path_utils import get_repo_root
            root = get_repo_root()
        except Exception:
            root = Path.cwd()
    p = root / "data/local/value_packs/samples" / relative_path
    return p if p.exists() and p.is_file() else None
