"""
M26I–M26L: Persist and list taught skills. data/local/teaching/skills/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.teaching.skill_models import Skill

SKILLS_DIR = "data/local/teaching/skills"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_skills_dir(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / SKILLS_DIR


def _skill_path(skill_id: str, repo_root: Path | str | None) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in skill_id.strip())
    return get_skills_dir(repo_root) / f"{safe}.json"


def save_skill(skill: Skill, repo_root: Path | str | None = None) -> Path:
    path = get_skills_dir(repo_root)
    path.mkdir(parents=True, exist_ok=True)
    fp = _skill_path(skill.skill_id, repo_root)
    fp.write_text(json.dumps(skill.to_dict(), indent=2), encoding="utf-8")
    return fp


def load_skill(skill_id: str, repo_root: Path | str | None = None) -> Skill | None:
    fp = _skill_path(skill_id, repo_root)
    if not fp.exists() or not fp.is_file():
        return None
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
        return Skill.from_dict(data)
    except Exception:
        return None


def list_skills(
    status: str | None = None,
    repo_root: Path | str | None = None,
    limit: int = 200,
) -> list[Skill]:
    """List skills; optional filter by status (draft, accepted, rejected)."""
    root = get_skills_dir(repo_root)
    if not root.exists():
        return []
    out: list[Skill] = []
    for f in sorted(root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not f.is_file() or f.suffix != ".json":
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            s = Skill.from_dict(data)
            if status and s.status != status:
                continue
            out.append(s)
            if len(out) >= limit:
                break
        except Exception:
            continue
    return out


def delete_skill(skill_id: str, repo_root: Path | str | None = None) -> bool:
    fp = _skill_path(skill_id, repo_root)
    if fp.exists() and fp.is_file():
        fp.unlink()
        return True
    return False
