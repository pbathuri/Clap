"""
M50C: Explain surface classification for v1 contract.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.v1_contract.models import StableV1Contract


def explain_surface(surface_id: str, contract: StableV1Contract) -> dict[str, Any]:
    """
    Explain how a surface is classified in the v1 contract: v1_core | v1_advanced | quarantined | excluded.
    Returns rationale and whether users may rely on it for v1.
    """
    for s in contract.v1_core_surfaces:
        if s.surface_id == surface_id:
            return {
                "surface_id": surface_id,
                "label": s.label,
                "classification": "v1_core",
                "rationale": s.rationale or "Core surface for stable v1; fully supported.",
                "may_rely_on": True,
                "support_note": "In scope for v1 support.",
            }
    for s in contract.v1_advanced_surfaces:
        if s.surface_id == surface_id:
            return {
                "surface_id": surface_id,
                "label": s.label,
                "classification": "v1_advanced",
                "rationale": s.rationale or "Supported advanced surface for stable v1.",
                "may_rely_on": True,
                "support_note": "Supported but optional or power-user.",
            }
    for s in contract.quarantined_surfaces:
        if s.surface_id == surface_id:
            return {
                "surface_id": surface_id,
                "label": s.label,
                "classification": "quarantined_experimental",
                "rationale": s.rationale or "Experimental; not in v1 supported set.",
                "may_rely_on": False,
                "support_note": "Quarantined; use at own risk.",
                "reveal_rule": s.reveal_rule,
            }
    for s in contract.excluded_surfaces:
        if s.surface_id == surface_id:
            return {
                "surface_id": surface_id,
                "label": s.label,
                "classification": "excluded",
                "rationale": f"Excluded from v1: {s.reason}.",
                "may_rely_on": False,
                "support_note": "Out of v1 scope.",
                "reason": s.reason,
            }
    return {
        "surface_id": surface_id,
        "label": surface_id.replace("_", " ").title(),
        "classification": "unknown",
        "rationale": "Surface not found in v1 contract; may be unmapped or from another vertical.",
        "may_rely_on": False,
        "support_note": "Not in current v1 contract.",
    }
