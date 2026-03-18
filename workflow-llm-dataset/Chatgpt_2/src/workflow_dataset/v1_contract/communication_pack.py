"""
M50D.1: Stable-v1 communication pack and experimental quarantine summary — safe to rely on vs exploratory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.v1_contract.models import (
    StableV1Contract,
    StableV1CommunicationPack,
    SafeToRelyOnItem,
    DoNotRelyOnItem,
    ExperimentalQuarantineSummary,
)
from workflow_dataset.v1_contract.contract import build_stable_v1_contract


def build_stable_v1_communication_pack(
    contract: StableV1Contract | None = None,
    repo_root: Path | str | None = None,
) -> StableV1CommunicationPack:
    """
    Build stable-v1 communication pack: what is safe to rely on, what is exploratory.
    Operator-facing for clear safe-vs-exploratory messaging.
    """
    if contract is None:
        contract = build_stable_v1_contract(repo_root)

    now = utc_now_iso()
    safe: list[SafeToRelyOnItem] = []
    do_not: list[DoNotRelyOnItem] = []

    for s in contract.v1_core_surfaces:
        safe.append(SafeToRelyOnItem(
            item_id=s.surface_id,
            label=s.label or s.surface_id,
            one_liner="Core surface; fully supported for v1.",
            category="surface",
        ))
    for s in contract.v1_advanced_surfaces:
        safe.append(SafeToRelyOnItem(
            item_id=s.surface_id,
            label=s.label or s.surface_id,
            one_liner="Supported advanced surface for v1.",
            category="surface",
        ))
    if contract.stable_workflow_contract and contract.stable_workflow_contract.workflow_ids:
        for w in contract.stable_workflow_contract.workflow_ids:
            safe.append(SafeToRelyOnItem(
                item_id=w,
                label=w.replace("_", " ").title(),
                one_liner="In stable v1 workflow set.",
                category="workflow",
            ))
    if contract.support_commitment_note and contract.support_commitment_note.summary:
        safe.append(SafeToRelyOnItem(
            item_id="support_commitment",
            label="Support commitment",
            one_liner=contract.support_commitment_note.summary[:120],
            category="support",
        ))
    if contract.migration_support_expectation:
        safe.append(SafeToRelyOnItem(
            item_id="migration",
            label="Migration continuity",
            one_liner=contract.migration_support_expectation,
            category="migration",
        ))

    for s in contract.quarantined_surfaces:
        do_not.append(DoNotRelyOnItem(
            item_id=s.surface_id,
            label=s.label or s.surface_id,
            one_liner="Experimental; not in v1 supported set. Use at own risk.",
            category="quarantined",
        ))
    for s in contract.excluded_surfaces:
        do_not.append(DoNotRelyOnItem(
            item_id=s.surface_id,
            label=s.label or s.surface_id,
            one_liner=f"Out of v1 scope ({s.reason}).",
            category="excluded",
        ))

    core_count = len(contract.v1_core_surfaces)
    advanced_count = len(contract.v1_advanced_surfaces)
    stable_surfaces_summary = f"{core_count} core and {advanced_count} advanced surfaces are supported for stable v1."
    workflow_ids = contract.stable_workflow_contract.workflow_ids if contract.stable_workflow_contract else []
    stable_workflows_summary = f"{len(workflow_ids)} workflows in v1 scope." if workflow_ids else "No workflow set locked."
    support_one_liner = contract.support_commitment_note.summary[:100] if contract.support_commitment_note else "Core and advanced surfaces supported; quarantined and excluded are not."
    exploratory_one_liner = f"{len(contract.quarantined_surfaces)} quarantined and {len(contract.excluded_surfaces)} excluded; these are exploratory or out of scope."

    headline = f"Stable v1: {contract.vertical_label or contract.vertical_id}. Safe to rely on core and advanced surfaces; quarantined is exploratory."

    return StableV1CommunicationPack(
        pack_id="stable_v1_communication_pack",
        generated_at_utc=now,
        headline=headline,
        safe_to_rely_on=safe,
        do_not_rely_on=do_not,
        stable_surfaces_summary=stable_surfaces_summary,
        stable_workflows_summary=stable_workflows_summary,
        support_commitment_one_liner=support_one_liner,
        exploratory_summary_one_liner=exploratory_one_liner,
    )


def build_experimental_quarantine_summary(
    contract: StableV1Contract | None = None,
    repo_root: Path | str | None = None,
) -> ExperimentalQuarantineSummary:
    """Build experimental quarantine summary: what remains exploratory, why."""
    if contract is None:
        contract = build_stable_v1_contract(repo_root)

    now = utc_now_iso()
    items: list[dict[str, Any]] = []
    for s in contract.quarantined_surfaces:
        items.append({
            "surface_id": s.surface_id,
            "label": s.label or s.surface_id,
            "why_exploratory": s.rationale or "Experimental; not in v1 supported set.",
            "reveal_rule": s.reveal_rule,
        })
    for s in contract.excluded_surfaces:
        items.append({
            "surface_id": s.surface_id,
            "label": s.label or s.surface_id,
            "why_exploratory": f"Excluded from v1 ({s.reason}); out of scope.",
            "reveal_rule": "n/a",
        })

    count = len(contract.quarantined_surfaces) + len(contract.excluded_surfaces)
    one_liner = f"{len(contract.quarantined_surfaces)} quarantined and {len(contract.excluded_surfaces)} excluded surfaces are not in stable v1; do not rely on them for supported use."
    headline = "Experimental / out of scope: not safe to rely on for v1."

    return ExperimentalQuarantineSummary(
        summary_id="experimental_quarantine_summary",
        generated_at_utc=now,
        headline=headline,
        one_liner=one_liner,
        items=items,
        count=count,
    )


def format_safe_vs_exploratory_text(
    contract: StableV1Contract | None = None,
    repo_root: Path | str | None = None,
    pack: StableV1CommunicationPack | None = None,
) -> str:
    """Operator-facing text: what is safe to rely on vs what remains exploratory."""
    if pack is None:
        pack = build_stable_v1_communication_pack(contract=contract, repo_root=repo_root)
    lines = [
        "--- Safe to rely on vs exploratory ---",
        pack.headline,
        "",
        "Safe to rely on (stable v1):",
        "  " + pack.stable_surfaces_summary,
        "  " + pack.stable_workflows_summary,
        "  " + pack.support_commitment_one_liner,
        "",
    ]
    for s in pack.safe_to_rely_on[:15]:
        lines.append(f"  • {s.label}: {s.one_liner}")
    if len(pack.safe_to_rely_on) > 15:
        lines.append(f"  ... and {len(pack.safe_to_rely_on) - 15} more")
    lines.append("")
    lines.append("Do not rely on (exploratory / out of scope):")
    lines.append("  " + pack.exploratory_summary_one_liner)
    for d in pack.do_not_rely_on[:15]:
        lines.append(f"  • {d.label}: {d.one_liner}")
    if len(pack.do_not_rely_on) > 15:
        lines.append(f"  ... and {len(pack.do_not_rely_on) - 15} more")
    return "\n".join(lines)
