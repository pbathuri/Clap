"""
M32I–M32L: Action card store — persist and list cards under data/local/action_cards.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.action_cards.models import ActionCard, CardState

CARDS_DIR = "data/local/action_cards"
CARDS_FILE = "cards.json"


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_cards_dir(repo_root: Path | str | None = None) -> Path:
    return _repo_root(repo_root) / CARDS_DIR


def _cards_path(repo_root: Path | str | None) -> Path:
    return get_cards_dir(repo_root) / CARDS_FILE


def load_all_cards(repo_root: Path | str | None = None) -> list[ActionCard]:
    path = _cards_path(repo_root)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data.get("cards", [])
        return [ActionCard.from_dict(x) for x in items]
    except Exception:
        return []


def save_cards(cards: list[ActionCard], repo_root: Path | str | None = None) -> Path:
    path = _cards_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"cards": [c.to_dict() for c in cards]}
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def load_card(card_id: str, repo_root: Path | str | None = None) -> ActionCard | None:
    for c in load_all_cards(repo_root):
        if c.card_id == card_id:
            return c
    return None


def save_card(card: ActionCard, repo_root: Path | str | None = None) -> Path:
    cards = load_all_cards(repo_root)
    for i, c in enumerate(cards):
        if c.card_id == card.card_id:
            cards[i] = card
            save_cards(cards, repo_root)
            return _cards_path(repo_root)
    cards.append(card)
    save_cards(cards, repo_root)
    return _cards_path(repo_root)


def update_card_state(
    card_id: str,
    state: CardState,
    repo_root: Path | str | None = None,
    updated_utc: str = "",
    executed_at: str = "",
    outcome_summary: str = "",
    blocked_reason: str = "",
) -> bool:
    card = load_card(card_id, repo_root)
    if not card:
        return False
    card.state = state
    if updated_utc:
        card.updated_utc = updated_utc
    if executed_at:
        card.executed_at = executed_at
    if outcome_summary:
        card.outcome_summary = outcome_summary
    if blocked_reason:
        card.blocked_reason = blocked_reason
    save_card(card, repo_root)
    return True


def list_cards(
    repo_root: Path | str | None = None,
    state: CardState | None = None,
    limit: int = 100,
) -> list[ActionCard]:
    cards = load_all_cards(repo_root)
    if state is not None:
        cards = [c for c in cards if c.state == state]
    return cards[:limit]
