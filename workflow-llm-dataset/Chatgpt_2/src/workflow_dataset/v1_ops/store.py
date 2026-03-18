"""
M50H.1: Persist and list stable-v1 maintenance packs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.v1_ops.models import StableV1MaintenancePack

PACKS_DIR = "data/local/v1_ops/maintenance_packs"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _packs_dir(root: Path) -> Path:
    d = root / PACKS_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def _pack_filename(pack_id: str, generated_at_utc: str) -> str:
    # Safe filename: pack_id + first 19 chars of ISO (YYYY-MM-DDTHH-MM-SS)
    safe_ts = (generated_at_utc or "").replace(":", "-").replace(" ", "T")[:19]
    return f"{pack_id}_{safe_ts}.json"


def save_maintenance_pack(
    pack: StableV1MaintenancePack,
    repo_root: Path | str | None = None,
) -> Path:
    """Persist a stable-v1 maintenance pack. Returns path to saved file."""
    root = _repo_root(repo_root)
    d = _packs_dir(root)
    pack_id = pack.pack_id or "stable_v1_maintenance_pack"
    generated = pack.generated_at_utc or ""
    name = _pack_filename(pack_id, generated)
    path = d / name
    path.write_text(json.dumps(pack.to_dict(), indent=2), encoding="utf-8")
    return path


def load_maintenance_pack(
    pack_id_or_latest: str = "latest",
    repo_root: Path | str | None = None,
) -> StableV1MaintenancePack | None:
    """Load a maintenance pack by id prefix or 'latest' (most recent by generated_at)."""
    root = _repo_root(repo_root)
    d = _packs_dir(root)
    if not d.exists():
        return None
    files = sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return None
    if pack_id_or_latest == "latest":
        path = files[0]
    else:
        matching = [p for p in files if pack_id_or_latest in p.stem]
        path = matching[0] if matching else files[0]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return StableV1MaintenancePack.from_dict(data)
    except Exception:
        return None


def list_maintenance_packs(repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """List saved maintenance packs: pack_id, generated_at_utc, path (relative or stem)."""
    root = _repo_root(repo_root)
    d = _packs_dir(root)
    if not d.exists():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            out.append({
                "pack_id": data.get("pack_id", path.stem),
                "label": data.get("label", ""),
                "generated_at_utc": data.get("generated_at_utc", ""),
                "path_stem": path.stem,
            })
        except Exception:
            out.append({"pack_id": path.stem, "label": "", "generated_at_utc": "", "path_stem": path.stem})
    return out
