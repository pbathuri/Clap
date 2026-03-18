"""
M25C: Per-pack install history for rollback and audit. Stored in data/local/packs/install_history.json.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from workflow_dataset.packs.pack_state import get_packs_dir, _default_packs_dir

HISTORY_FILE = "install_history.json"


def _history_path(packs_dir: Path | str | None = None) -> Path:
    root = Path(packs_dir) if packs_dir else _default_packs_dir()
    root.mkdir(parents=True, exist_ok=True)
    return root / HISTORY_FILE


def _load_history(packs_dir: Path | str | None = None) -> dict[str, list[dict[str, Any]]]:
    """Load full history: { pack_id: [ {version, installed_utc, manifest_path?}, ... ] }."""
    path = _history_path(packs_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {k: v if isinstance(v, list) else [] for k, v in (data or {}).items()}
    except Exception:
        return {}


def _save_history(history: dict[str, list[dict[str, Any]]], packs_dir: Path | str | None = None) -> Path:
    path = _history_path(packs_dir)
    path.write_text(json.dumps(history, indent=2), encoding="utf-8")
    return path


def append_install_record(
    pack_id: str,
    version: str,
    packs_dir: Path | str | None = None,
    manifest_path: str | None = None,
) -> None:
    """Append one install record for pack_id. Newest first in list."""
    history = _load_history(packs_dir)
    rec = {"version": version, "installed_utc": time.time()}
    if manifest_path:
        rec["manifest_path"] = manifest_path
    if pack_id not in history:
        history[pack_id] = []
    history[pack_id].insert(0, rec)
    _save_history(history, packs_dir)


def get_pack_history(
    pack_id: str,
    packs_dir: Path | str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Return install history for pack_id (newest first)."""
    history = _load_history(packs_dir)
    return list(history.get(pack_id, []))[:limit]


def get_previous_version(pack_id: str, packs_dir: Path | str | None = None) -> str | None:
    """Return the previous installed version for pack_id (second in history), or None."""
    hist = get_pack_history(pack_id, packs_dir, limit=2)
    if len(hist) < 2:
        return None
    return hist[1].get("version")


def get_previous_manifest_path(pack_id: str, packs_dir: Path | str | None = None) -> Path | None:
    """Return path to previous version manifest if stored (e.g. in versions/<ver>/manifest.json)."""
    hist = get_pack_history(pack_id, packs_dir, limit=2)
    if len(hist) < 2:
        return None
    prev = hist[1]
    # Stored path may be relative or in versions/<ver>/manifest.json
    root = get_packs_dir(packs_dir)
    rel = prev.get("manifest_path")
    if rel:
        p = root / rel
        if p.exists():
            return p
    ver = prev.get("version")
    if ver:
        p = root / pack_id / "versions" / ver / "manifest.json"
        if p.exists():
            return p
    return None
