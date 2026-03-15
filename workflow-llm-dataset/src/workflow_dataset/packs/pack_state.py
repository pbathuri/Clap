"""
M22: Installed pack state (local file). Tracks pack_id -> manifest path / install metadata.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _default_packs_dir() -> Path:
    return Path("data/local/packs")


def _state_path(packs_dir: Path | str | None = None) -> Path:
    root = Path(packs_dir) if packs_dir else _default_packs_dir()
    return root / "installed_state.json"


def load_pack_state(packs_dir: Path | str | None = None) -> dict[str, Any]:
    """Load installed pack state. Returns { pack_id: { path, version, installed_utc } }."""
    path = _state_path(packs_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_pack_state(state: dict[str, Any], packs_dir: Path | str | None = None) -> Path:
    """Save installed pack state."""
    root = Path(packs_dir) if packs_dir else _default_packs_dir()
    root.mkdir(parents=True, exist_ok=True)
    path = root / "installed_state.json"
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return path


def get_packs_dir(packs_dir: Path | str | None = None) -> Path:
    """Return root packs directory; ensure it exists."""
    root = Path(packs_dir) if packs_dir else _default_packs_dir()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _active_role_path(packs_dir: Path | str | None = None) -> Path:
    root = Path(packs_dir) if packs_dir else _default_packs_dir()
    root.mkdir(parents=True, exist_ok=True)
    return root / "active_role.txt"


def get_active_role(packs_dir: Path | str | None = None) -> str:
    """Return currently active role (from activate); empty if none."""
    path = _active_role_path(packs_dir)
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def set_active_role(role: str, packs_dir: Path | str | None = None) -> Path:
    """Set active role for pack-driven resolution (e.g. when no --role passed)."""
    path = _active_role_path(packs_dir)
    path.write_text(role.strip(), encoding="utf-8")
    return path


def clear_active_role(packs_dir: Path | str | None = None) -> Path:
    """Clear active role."""
    path = _active_role_path(packs_dir)
    if path.exists():
        path.unlink()
    return path
