"""
M32L.1: Fast review paths — filter + sort + action for common accepted cards.
"""

from __future__ import annotations

import json
from pathlib import Path

from workflow_dataset.action_cards.models import ActionCard, FastReviewPath
from workflow_dataset.action_cards.store import get_cards_dir, load_all_cards, load_card

PATHS_FILE = "review_paths.json"


def _paths_path(repo_root: Path | str | None) -> Path:
    return get_cards_dir(repo_root) / PATHS_FILE


def load_all_review_paths(repo_root: Path | str | None = None) -> list[FastReviewPath]:
    path = _paths_path(repo_root)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data.get("review_paths", [])
        return [FastReviewPath.from_dict(x) for x in items]
    except Exception:
        return []


def save_review_paths(paths: list[FastReviewPath], repo_root: Path | str | None = None) -> Path:
    p = _paths_path(repo_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {"review_paths": [x.to_dict() for x in paths]}
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p


def load_review_path(path_id: str, repo_root: Path | str | None = None) -> FastReviewPath | None:
    for x in load_all_review_paths(repo_root):
        if x.path_id == path_id:
            return x
    return None


def save_review_path(path: FastReviewPath, repo_root: Path | str | None = None) -> Path:
    paths = load_all_review_paths(repo_root)
    for i, p in enumerate(paths):
        if p.path_id == path.path_id:
            paths[i] = path
            save_review_paths(paths, repo_root)
            return _paths_path(repo_root)
    paths.append(path)
    save_review_paths(paths, repo_root)
    return _paths_path(repo_root)


def apply_path(
    path_id: str,
    repo_root: Path | str | None = None,
    card_ids_from_bundle: list[str] | None = None,
) -> list[ActionCard]:
    """
    Apply a fast review path: resolve path, filter cards (from store or from bundle ids), sort, return ordered list.
    If card_ids_from_bundle is set, only those cards are considered; otherwise all cards from store are used.
    """
    path = load_review_path(path_id, repo_root)
    if not path:
        return []
    if card_ids_from_bundle:
        cards = []
        for cid in card_ids_from_bundle:
            card = load_card(cid, repo_root)
            if card:
                cards.append(card)
    else:
        cards = load_all_cards(repo_root)

    # Filter
    if path.filter_state:
        cards = [c for c in cards if c.state.value == path.filter_state]
    if path.filter_handoff_target:
        cards = [c for c in cards if c.handoff_target.value == path.filter_handoff_target]
    if path.filter_source_type:
        cards = [c for c in cards if c.source_type == path.filter_source_type]

    # Sort
    key = path.sort_by
    reverse = path.sort_order == "desc"
    if key == "created_utc":
        cards.sort(key=lambda c: c.created_utc or "", reverse=reverse)
    elif key == "updated_utc":
        cards.sort(key=lambda c: c.updated_utc or "", reverse=reverse)
    elif key == "title":
        cards.sort(key=lambda c: (c.title or "").lower(), reverse=reverse)
    else:
        cards.sort(key=lambda c: c.updated_utc or "", reverse=reverse)

    return cards[: path.limit]
