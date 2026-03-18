"""
M22: Registry of installed packs — list, get, load manifest from state.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.packs.pack_models import PackManifest
from workflow_dataset.packs.pack_state import load_pack_state, get_packs_dir


def list_installed_packs(packs_dir: Path | str | None = None) -> list[dict[str, Any]]:
    """Return list of installed pack records: { pack_id, version, path, installed_utc }."""
    state = load_pack_state(packs_dir)
    return [{"pack_id": k, **v} for k, v in state.items()]


def get_installed_pack(pack_id: str, packs_dir: Path | str | None = None) -> dict[str, Any] | None:
    """Return installed pack record for pack_id or None."""
    state = load_pack_state(packs_dir)
    rec = state.get(pack_id)
    return {"pack_id": pack_id, **rec} if isinstance(rec, dict) else None


def get_installed_manifest(pack_id: str, packs_dir: Path | str | None = None) -> PackManifest | None:
    """Load and return PackManifest for an installed pack, or None."""
    rec = get_installed_pack(pack_id, packs_dir)
    if not rec:
        return None
    path = rec.get("path") or rec.get("manifest_path")
    if not path:
        return None
    p = Path(path)
    if not p.is_absolute():
        root = get_packs_dir(packs_dir)
        p = root / path
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return PackManifest.model_validate(data)
    except Exception:
        return None
