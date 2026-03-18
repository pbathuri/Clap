"""
M50D: Mission control slice — active v1 contract, quarantined, excluded, top ambiguity, next freeze action.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.v1_contract.contract import build_stable_v1_contract
from workflow_dataset.v1_contract.report import build_freeze_report
from workflow_dataset.v1_contract.surfaces import list_v1_core, list_quarantined, list_excluded
from workflow_dataset.v1_contract.communication_pack import (
    build_stable_v1_communication_pack,
    build_experimental_quarantine_summary,
)


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def v1_contract_slice(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Additive mission-control slice for v1 contract.
    Keys: vertical_id, has_active_cut, v1_core_count, v1_advanced_count, quarantined_count, excluded_count,
    quarantined_surface_ids, excluded_surface_ids, top_v1_ambiguity, next_freeze_action.
    """
    root = _root(repo_root)
    contract = build_stable_v1_contract(root)
    report = build_freeze_report(contract=contract)

    quarantined_ids = list_quarantined(contract)
    excluded_ids = list_excluded(contract)
    core_ids = list_v1_core(contract)

    top_ambiguity = ""
    if not contract.has_active_cut:
        top_ambiguity = "No production cut locked; v1 contract is from default vertical."
    elif not contract.frozen_at_utc:
        top_ambiguity = "Production cut has no frozen_at_utc."

    pack = build_stable_v1_communication_pack(contract=contract)
    exp_summary = build_experimental_quarantine_summary(contract=contract)

    return {
        "vertical_id": contract.vertical_id,
        "vertical_label": contract.vertical_label,
        "has_active_cut": contract.has_active_cut,
        "frozen_at_utc": contract.frozen_at_utc,
        "v1_core_count": len(contract.v1_core_surfaces),
        "v1_advanced_count": len(contract.v1_advanced_surfaces),
        "quarantined_count": len(quarantined_ids),
        "excluded_count": len(excluded_ids),
        "quarantined_surface_ids": quarantined_ids[:15],
        "excluded_surface_ids": excluded_ids[:15],
        "v1_core_surface_ids": core_ids[:10],
        "top_v1_ambiguity": top_ambiguity,
        "next_freeze_action": report.get("next_freeze_action", "workflow-dataset v1-contract show"),
        "stable_pack_headline": pack.headline,
        "experimental_summary_count": exp_summary.count,
    }
