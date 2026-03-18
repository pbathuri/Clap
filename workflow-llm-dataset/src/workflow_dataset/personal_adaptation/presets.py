"""
M31L.1: Personal profile presets — named sets of candidates for grouped apply and review.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.personal_adaptation.models import PersonalProfilePreset
from workflow_dataset.personal_adaptation.store import get_presets_dir, get_adaptation_dir

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:16]


def _repo_root(root: Path | str | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def save_preset(
    preset: PersonalProfilePreset,
    repo_root: Path | str | None = None,
) -> Path:
    """Save preset to data/local/personal_adaptation/presets/<preset_id>.json."""
    root = _repo_root(repo_root)
    dir_path = get_presets_dir(root)
    dir_path.mkdir(parents=True, exist_ok=True)
    path = dir_path / f"{preset.preset_id}.json"
    path.write_text(json.dumps(preset.to_dict(), indent=2), encoding="utf-8")
    return path


def load_preset(
    preset_id: str,
    repo_root: Path | str | None = None,
) -> PersonalProfilePreset | None:
    """Load preset by id."""
    root = _repo_root(repo_root)
    path = get_presets_dir(root) / f"{preset_id}.json"
    if not path.exists():
        return None
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        return PersonalProfilePreset.from_dict(d)
    except Exception:
        return None


def list_presets(repo_root: Path | str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """List preset summaries (preset_id, name, candidate_ids count)."""
    root = _repo_root(repo_root)
    dir_path = get_presets_dir(root)
    if not dir_path.exists():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(dir_path.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
            out.append({
                "preset_id": d.get("preset_id", path.stem),
                "name": d.get("name", ""),
                "description": d.get("description", "")[:80],
                "candidate_count": len(d.get("candidate_ids", [])),
                "created_utc": d.get("created_utc", ""),
            })
        except Exception:
            pass
    return out


def create_preset(
    name: str,
    candidate_ids: list[str],
    description: str = "",
    repo_root: Path | str | None = None,
) -> PersonalProfilePreset:
    """Create and save a new preset from name and candidate ids."""
    ts = utc_now_iso()
    preset_id = stable_id("preset", name, *candidate_ids[:3], prefix="preset_")
    preset = PersonalProfilePreset(
        preset_id=preset_id,
        name=name,
        description=description,
        candidate_ids=candidate_ids,
        created_utc=ts,
        updated_utc=ts,
    )
    save_preset(preset, repo_root=repo_root)
    return preset
