"""
M32L.1: Micro-assistance bundles — reusable named groups of action cards per user moment.
"""

from __future__ import annotations

import json
from pathlib import Path

from workflow_dataset.action_cards.models import MicroAssistanceBundle
from workflow_dataset.action_cards.store import get_cards_dir

BUNDLES_FILE = "bundles.json"


def _bundles_path(repo_root: Path | str | None) -> Path:
    return get_cards_dir(repo_root) / BUNDLES_FILE


def load_all_bundles(repo_root: Path | str | None = None) -> list[MicroAssistanceBundle]:
    path = _bundles_path(repo_root)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data.get("bundles", [])
        return [MicroAssistanceBundle.from_dict(x) for x in items]
    except Exception:
        return []


def save_bundles(bundles: list[MicroAssistanceBundle], repo_root: Path | str | None = None) -> Path:
    path = _bundles_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"bundles": [b.to_dict() for b in bundles]}
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def load_bundle(bundle_id: str, repo_root: Path | str | None = None) -> MicroAssistanceBundle | None:
    for b in load_all_bundles(repo_root):
        if b.bundle_id == bundle_id:
            return b
    return None


def save_bundle(bundle: MicroAssistanceBundle, repo_root: Path | str | None = None) -> Path:
    bundles = load_all_bundles(repo_root)
    for i, b in enumerate(bundles):
        if b.bundle_id == bundle.bundle_id:
            bundles[i] = bundle
            save_bundles(bundles, repo_root)
            return _bundles_path(repo_root)
    bundles.append(bundle)
    save_bundles(bundles, repo_root)
    return _bundles_path(repo_root)


def list_bundles_by_moment(
    moment_kind: str,
    repo_root: Path | str | None = None,
    limit: int = 50,
) -> list[MicroAssistanceBundle]:
    bundles = [b for b in load_all_bundles(repo_root) if b.moment_kind == moment_kind]
    return bundles[:limit]


def add_card_to_bundle(
    bundle_id: str,
    card_id: str,
    repo_root: Path | str | None = None,
) -> bool:
    b = load_bundle(bundle_id, repo_root)
    if not b:
        return False
    if card_id not in b.card_ids:
        b.card_ids = b.card_ids + [card_id]
        save_bundle(b, repo_root)
    return True


def remove_card_from_bundle(
    bundle_id: str,
    card_id: str,
    repo_root: Path | str | None = None,
) -> bool:
    b = load_bundle(bundle_id, repo_root)
    if not b:
        return False
    if card_id in b.card_ids:
        b.card_ids = [x for x in b.card_ids if x != card_id]
        save_bundle(b, repo_root)
    return True
