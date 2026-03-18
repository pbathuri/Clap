"""
M44I–M44L: Persist retrieval-grounded recommendations for explain-by-id and mission control.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.memory_intelligence.models import (
    RetrievalGroundedRecommendation,
    MemoryGroundedPlaybook,
    MemoryGroundedActionPack,
)

DIR_NAME = "data/local/memory_intelligence"
RECOMMENDATIONS_FILE = "recommendations.json"
PLAYBOOKS_FILE = "playbooks.json"
ACTION_PACKS_FILE = "action_packs.json"
MAX_STORED = 500
MAX_PLAYBOOKS = 50
MAX_ACTION_PACKS = 50


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _load_all(root: Path) -> list[dict[str, Any]]:
    path = root / DIR_NAME / RECOMMENDATIONS_FILE
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return list(data.get("recommendations", []))
    except Exception:
        return []


def _save_all(root: Path, recs: list[dict[str, Any]]) -> Path:
    d = root / DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    path = d / RECOMMENDATIONS_FILE
    path.write_text(json.dumps({"recommendations": recs}, indent=2), encoding="utf-8")
    return path


def save_recommendation(rec: RetrievalGroundedRecommendation, repo_root: Path | str | None = None) -> None:
    """Append a recommendation to the store (by id); cap total count."""
    root = _repo_root(repo_root)
    recs = _load_all(root)
    by_id = {r["recommendation_id"]: r for r in recs}
    by_id[rec.recommendation_id] = rec.to_dict()
    recs = list(by_id.values())
    recs.sort(key=lambda x: x.get("created_at_utc", ""), reverse=True)
    if len(recs) > MAX_STORED:
        recs = recs[:MAX_STORED]
    _save_all(root, recs)


def load_recommendation(recommendation_id: str, repo_root: Path | str | None = None) -> dict[str, Any] | None:
    """Load a single recommendation by id."""
    root = _repo_root(repo_root)
    for r in _load_all(root):
        if r.get("recommendation_id") == recommendation_id:
            return r
    return None


def list_recent_recommendations(
    limit: int = 50,
    project_id: str | None = None,
    kind: str | None = None,
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    """List recent recommendations, optionally filtered by project_id or kind."""
    root = _repo_root(repo_root)
    recs = _load_all(root)
    if project_id:
        recs = [r for r in recs if r.get("project_id") == project_id]
    if kind:
        recs = [r for r in recs if r.get("kind") == kind]
    recs.sort(key=lambda x: x.get("created_at_utc", ""), reverse=True)
    return recs[:limit]


# ----- M44L.1: Memory-grounded playbooks and action packs -----


def _load_playbooks(root: Path) -> list[dict[str, Any]]:
    path = root / DIR_NAME / PLAYBOOKS_FILE
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return list(data.get("playbooks", []))
    except Exception:
        return []


def _save_playbooks(root: Path, playbooks: list[dict[str, Any]]) -> Path:
    d = root / DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    path = d / PLAYBOOKS_FILE
    path.write_text(json.dumps({"playbooks": playbooks}, indent=2), encoding="utf-8")
    return path


def save_memory_grounded_playbook(pb: MemoryGroundedPlaybook, repo_root: Path | str | None = None) -> None:
    root = _repo_root(repo_root)
    all_pbs = _load_playbooks(root)
    by_id = {p["playbook_id"]: p for p in all_pbs}
    by_id[pb.playbook_id] = pb.to_dict()
    all_pbs = list(by_id.values())
    all_pbs.sort(key=lambda x: x.get("created_at_utc", ""), reverse=True)
    if len(all_pbs) > MAX_PLAYBOOKS:
        all_pbs = all_pbs[:MAX_PLAYBOOKS]
    _save_playbooks(root, all_pbs)


def load_memory_grounded_playbook(playbook_id: str, repo_root: Path | str | None = None) -> dict[str, Any] | None:
    root = _repo_root(repo_root)
    for p in _load_playbooks(root):
        if p.get("playbook_id") == playbook_id:
            return p
    return None


def list_memory_grounded_playbooks(
    curated_pack_id: str | None = None,
    limit: int = 20,
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    root = _repo_root(repo_root)
    all_pbs = _load_playbooks(root)
    if curated_pack_id:
        all_pbs = [p for p in all_pbs if p.get("curated_pack_id") == curated_pack_id]
    all_pbs.sort(key=lambda x: x.get("created_at_utc", ""), reverse=True)
    return all_pbs[:limit]


def _load_action_packs(root: Path) -> list[dict[str, Any]]:
    path = root / DIR_NAME / ACTION_PACKS_FILE
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return list(data.get("action_packs", []))
    except Exception:
        return []


def _save_action_packs(root: Path, packs: list[dict[str, Any]]) -> Path:
    d = root / DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    path = d / ACTION_PACKS_FILE
    path.write_text(json.dumps({"action_packs": packs}, indent=2), encoding="utf-8")
    return path


def save_memory_grounded_action_pack(pack: MemoryGroundedActionPack, repo_root: Path | str | None = None) -> None:
    root = _repo_root(repo_root)
    all_packs = _load_action_packs(root)
    by_id = {p["action_pack_id"]: p for p in all_packs}
    by_id[pack.action_pack_id] = pack.to_dict()
    all_packs = list(by_id.values())
    all_packs.sort(key=lambda x: x.get("created_at_utc", ""), reverse=True)
    if len(all_packs) > MAX_ACTION_PACKS:
        all_packs = all_packs[:MAX_ACTION_PACKS]
    _save_action_packs(root, all_packs)


def load_memory_grounded_action_pack(action_pack_id: str, repo_root: Path | str | None = None) -> dict[str, Any] | None:
    root = _repo_root(repo_root)
    for p in _load_action_packs(root):
        if p.get("action_pack_id") == action_pack_id:
            return p
    return None


def list_memory_grounded_action_packs(
    vertical_id: str | None = None,
    project_id: str | None = None,
    limit: int = 20,
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    root = _repo_root(repo_root)
    all_packs = _load_action_packs(root)
    if vertical_id:
        all_packs = [p for p in all_packs if p.get("vertical_id") == vertical_id]
    if project_id:
        all_packs = [p for p in all_packs if p.get("project_id") == project_id]
    all_packs.sort(key=lambda x: x.get("created_at_utc", ""), reverse=True)
    return all_packs[:limit]
