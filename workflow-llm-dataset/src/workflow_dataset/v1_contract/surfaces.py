"""
M50B: v1 surface classification — list core, advanced, quarantined, excluded.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.v1_contract.models import StableV1Contract


def get_v1_surfaces_classification(contract: StableV1Contract) -> dict[str, Any]:
    """Return full classification: v1_core, v1_advanced, quarantined, excluded with counts."""
    return {
        "v1_core": [s.to_dict() for s in contract.v1_core_surfaces],
        "v1_core_count": len(contract.v1_core_surfaces),
        "v1_advanced": [s.to_dict() for s in contract.v1_advanced_surfaces],
        "v1_advanced_count": len(contract.v1_advanced_surfaces),
        "quarantined": [s.to_dict() for s in contract.quarantined_surfaces],
        "quarantined_count": len(contract.quarantined_surfaces),
        "excluded": [s.to_dict() for s in contract.excluded_surfaces],
        "excluded_count": len(contract.excluded_surfaces),
        "vertical_id": contract.vertical_id,
        "has_active_cut": contract.has_active_cut,
    }


def list_v1_core(contract: StableV1Contract) -> list[str]:
    """Surface ids in v1 core."""
    return [s.surface_id for s in contract.v1_core_surfaces]


def list_v1_advanced(contract: StableV1Contract) -> list[str]:
    """Surface ids in v1 advanced."""
    return [s.surface_id for s in contract.v1_advanced_surfaces]


def list_quarantined(contract: StableV1Contract) -> list[str]:
    """Surface ids quarantined (experimental)."""
    return [s.surface_id for s in contract.quarantined_surfaces]


def list_excluded(contract: StableV1Contract) -> list[str]:
    """Surface ids excluded from v1."""
    return [s.surface_id for s in contract.excluded_surfaces]
