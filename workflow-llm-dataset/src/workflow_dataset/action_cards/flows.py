"""
M32L.1: Grouped card flows — link user moments to bundles and fast review paths.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.action_cards.models import ActionCard, GroupedCardFlow
from workflow_dataset.action_cards.bundles import load_bundle
from workflow_dataset.action_cards.review_paths import apply_path

FLOWS_FILE = "flows.json"


def _flows_path(repo_root: Path | str | None) -> Path:
    from workflow_dataset.action_cards.store import get_cards_dir
    return get_cards_dir(repo_root) / FLOWS_FILE


def load_all_flows(repo_root: Path | str | None = None) -> list[GroupedCardFlow]:
    path = _flows_path(repo_root)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data.get("flows", [])
        return [GroupedCardFlow.from_dict(x) for x in items]
    except Exception:
        return []


def save_flows(flows: list[GroupedCardFlow], repo_root: Path | str | None = None) -> Path:
    path = _flows_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"flows": [f.to_dict() for f in flows]}
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def load_flow(flow_id: str, repo_root: Path | str | None = None) -> GroupedCardFlow | None:
    for f in load_all_flows(repo_root):
        if f.flow_id == flow_id:
            return f
    return None


def save_flow(flow: GroupedCardFlow, repo_root: Path | str | None = None) -> Path:
    flows = load_all_flows(repo_root)
    for i, f in enumerate(flows):
        if f.flow_id == flow.flow_id:
            flows[i] = flow
            save_flows(flows, repo_root)
            return _flows_path(repo_root)
    flows.append(flow)
    save_flows(flows, repo_root)
    return _flows_path(repo_root)


def get_flow_for_moment(
    moment_kind: str,
    repo_root: Path | str | None = None,
) -> GroupedCardFlow | None:
    for f in load_all_flows(repo_root):
        if f.moment_kind == moment_kind:
            return f
    return None


def run_flow(
    moment_kind: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Run the grouped flow for a user moment: resolve flow -> bundle + path,
    then apply path to bundle's cards (or all cards if no bundle). Returns cards and metadata.
    """
    flow = get_flow_for_moment(moment_kind, repo_root)
    if not flow:
        return {
            "ok": False,
            "error": "no_flow_for_moment",
            "moment_kind": moment_kind,
            "cards": [],
        }
    card_ids_from_bundle: list[str] | None = None
    if flow.bundle_id:
        bundle = load_bundle(flow.bundle_id, repo_root)
        if bundle:
            card_ids_from_bundle = bundle.card_ids
    cards: list[ActionCard] = []
    if flow.review_path_id:
        cards = apply_path(flow.review_path_id, repo_root, card_ids_from_bundle=card_ids_from_bundle)
    elif card_ids_from_bundle:
        from workflow_dataset.action_cards.store import load_card
        for cid in card_ids_from_bundle:
            c = load_card(cid, repo_root)
            if c:
                cards.append(c)
    return {
        "ok": True,
        "flow_id": flow.flow_id,
        "moment_kind": flow.moment_kind,
        "label": flow.label,
        "bundle_id": flow.bundle_id,
        "review_path_id": flow.review_path_id,
        "cards_count": len(cards),
        "cards": [c.to_dict() for c in cards],
    }
