"""
M50C: v1 freeze report — what is in v1, excluded, quarantined, what users may rely on.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.v1_contract.contract import build_stable_v1_contract
from workflow_dataset.v1_contract.models import StableV1Contract


def build_freeze_report(
    contract: StableV1Contract | None = None,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Build v1 freeze report: what is in v1, excluded, quarantined, why, what users may rely on, next action.
    """
    if contract is None:
        contract = build_stable_v1_contract(repo_root)

    in_v1_ids = [s.surface_id for s in contract.v1_core_surfaces] + [s.surface_id for s in contract.v1_advanced_surfaces]
    quarantined_ids = [s.surface_id for s in contract.quarantined_surfaces]
    excluded_ids = [s.surface_id for s in contract.excluded_surfaces]

    may_rely_on = (
        "Core and advanced surfaces are supported for stable v1. "
        "Quarantined surfaces are experimental. Excluded surfaces are out of scope."
    )
    next_freeze_action = ""
    if not contract.has_active_cut:
        next_freeze_action = "Lock production cut for chosen vertical: workflow-dataset production-cut lock."
    else:
        next_freeze_action = "Contract is frozen; run workflow-dataset stable-v1 gate to validate readiness."

    workflow_ids = []
    if contract.stable_workflow_contract:
        workflow_ids = list(contract.stable_workflow_contract.workflow_ids)

    return {
        "vertical_id": contract.vertical_id,
        "vertical_label": contract.vertical_label,
        "frozen_at_utc": contract.frozen_at_utc,
        "has_active_cut": contract.has_active_cut,
        "in_v1_surface_ids": in_v1_ids,
        "in_v1_count": len(in_v1_ids),
        "quarantined_surface_ids": quarantined_ids,
        "quarantined_count": len(quarantined_ids),
        "excluded_surface_ids": excluded_ids,
        "excluded_count": len(excluded_ids),
        "stable_workflow_ids": workflow_ids,
        "why_core": "Core surfaces are required for the chosen vertical; fully supported.",
        "why_advanced": "Advanced surfaces are optional or power-user; supported for v1.",
        "why_quarantined": "Quarantined surfaces are experimental; not in v1 supported set.",
        "why_excluded": "Excluded surfaces are out of scope, blocked, or non-core for v1.",
        "may_rely_on_summary": may_rely_on,
        "next_freeze_action": next_freeze_action,
        "support_summary": contract.support_commitment_note.summary if contract.support_commitment_note else "",
    }


def format_freeze_report_text(report: dict[str, Any], max_items: int = 20) -> str:
    """Format freeze report as operator-facing text."""
    lines = [
        "--- V1 freeze report ---",
        f"Vertical: {report.get('vertical_label', report.get('vertical_id', '—'))}",
        f"Frozen: {report.get('frozen_at_utc', '—')}  Active cut: {report.get('has_active_cut', False)}",
        "",
        f"In v1 ({report.get('in_v1_count', 0)}): " + ", ".join(report.get("in_v1_surface_ids", [])[:max_items]),
        f"Quarantined ({report.get('quarantined_count', 0)}): " + ", ".join(report.get("quarantined_surface_ids", [])[:max_items]),
        f"Excluded ({report.get('excluded_count', 0)}): " + ", ".join(report.get("excluded_surface_ids", [])[:max_items]),
        f"Stable workflows: {report.get('stable_workflow_ids', [])}",
        "",
        "May rely on: " + (report.get("may_rely_on_summary", "") or "")[:200],
        "",
        "Next: " + (report.get("next_freeze_action", "") or "—"),
    ]
    return "\n".join(lines)
