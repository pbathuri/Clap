"""
M35D.1: Routine eligibility matrix — which routine types may operate under which trust presets.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.trust.presets import get_preset, TrustPreset, preset_allows_tier
from workflow_dataset.trust.tiers import get_tier, list_tiers


# Routine type identifiers (used in eligibility matrix)
ROUTINE_TYPE_DIGEST = "digest"
ROUTINE_TYPE_FOLLOWUP = "followup"
ROUTINE_TYPE_BACKGROUND_RUN = "background_run"
ROUTINE_TYPE_WORKER_LANE = "worker_lane"
ROUTINE_TYPE_MACRO = "macro"
ROUTINE_TYPE_AD_HOC = "ad_hoc"

ROUTINE_TYPES = [
    ROUTINE_TYPE_DIGEST,
    ROUTINE_TYPE_FOLLOWUP,
    ROUTINE_TYPE_BACKGROUND_RUN,
    ROUTINE_TYPE_WORKER_LANE,
    ROUTINE_TYPE_MACRO,
    ROUTINE_TYPE_AD_HOC,
]

# Map routine_id (or prefix) -> routine_type for known routines
ROUTINE_ID_TO_TYPE: dict[str, str] = {
    "morning_digest": ROUTINE_TYPE_DIGEST,
    "project_digest": ROUTINE_TYPE_DIGEST,
    "blocked_followup": ROUTINE_TYPE_FOLLOWUP,
    "approval_followup": ROUTINE_TYPE_FOLLOWUP,
    "background_run": ROUTINE_TYPE_BACKGROUND_RUN,
    "worker_lane": ROUTINE_TYPE_WORKER_LANE,
    "macro": ROUTINE_TYPE_MACRO,
    "ad_hoc": ROUTINE_TYPE_AD_HOC,
}


def _tier_order(tier_id: str) -> int:
    tiers = list_tiers()
    for t in tiers:
        if t.tier_id == tier_id:
            return t.order
    return -1


# Eligibility matrix: preset_id -> routine_type -> max_tier_id allowed under that preset
# Empty or missing means use preset's max_authority_tier_id as cap.
ELIGIBILITY_MATRIX: dict[str, dict[str, str]] = {
    "cautious": {
        ROUTINE_TYPE_DIGEST: "suggest_only",
        ROUTINE_TYPE_FOLLOWUP: "suggest_only",
        ROUTINE_TYPE_BACKGROUND_RUN: "observe_only",
        ROUTINE_TYPE_WORKER_LANE: "observe_only",
        ROUTINE_TYPE_MACRO: "suggest_only",
        ROUTINE_TYPE_AD_HOC: "suggest_only",
    },
    "supervised_operator": {
        ROUTINE_TYPE_DIGEST: "sandbox_write",
        ROUTINE_TYPE_FOLLOWUP: "queued_execute",
        ROUTINE_TYPE_BACKGROUND_RUN: "sandbox_write",
        ROUTINE_TYPE_WORKER_LANE: "queued_execute",
        ROUTINE_TYPE_MACRO: "queued_execute",
        ROUTINE_TYPE_AD_HOC: "draft_only",
    },
    "bounded_trusted_routine": {
        ROUTINE_TYPE_DIGEST: "bounded_trusted_real",
        ROUTINE_TYPE_FOLLOWUP: "bounded_trusted_real",
        ROUTINE_TYPE_BACKGROUND_RUN: "queued_execute",
        ROUTINE_TYPE_WORKER_LANE: "bounded_trusted_real",
        ROUTINE_TYPE_MACRO: "bounded_trusted_real",
        ROUTINE_TYPE_AD_HOC: "sandbox_write",
    },
    "release_safe": {
        ROUTINE_TYPE_DIGEST: "bounded_trusted_real",
        ROUTINE_TYPE_FOLLOWUP: "queued_execute",
        ROUTINE_TYPE_BACKGROUND_RUN: "sandbox_write",
        ROUTINE_TYPE_WORKER_LANE: "bounded_trusted_real",
        ROUTINE_TYPE_MACRO: "queued_execute",
        ROUTINE_TYPE_AD_HOC: "sandbox_write",
    },
}


def routine_type_for(routine_id: str) -> str:
    """Infer routine type from routine_id. Returns ROUTINE_TYPE_AD_HOC if unknown."""
    if not routine_id:
        return ROUTINE_TYPE_AD_HOC
    if routine_id in ROUTINE_ID_TO_TYPE:
        return ROUTINE_ID_TO_TYPE[routine_id]
    # Prefix match for common patterns
    if "digest" in routine_id.lower():
        return ROUTINE_TYPE_DIGEST
    if "followup" in routine_id.lower():
        return ROUTINE_TYPE_FOLLOWUP
    if "background" in routine_id.lower() or "run" in routine_id.lower():
        return ROUTINE_TYPE_BACKGROUND_RUN
    if "lane" in routine_id.lower():
        return ROUTINE_TYPE_WORKER_LANE
    if "macro" in routine_id.lower():
        return ROUTINE_TYPE_MACRO
    return ROUTINE_TYPE_AD_HOC


def max_tier_for_routine_under_preset(preset_id: str, routine_type: str) -> str | None:
    """Max authority tier_id allowed for this routine type under this preset. None if preset unknown."""
    preset = get_preset(preset_id)
    if not preset:
        return None
    matrix_row = ELIGIBILITY_MATRIX.get(preset_id, {})
    max_tier = matrix_row.get(routine_type) or preset.max_authority_tier_id
    return max_tier if get_tier(max_tier) else preset.max_authority_tier_id


def is_eligible(preset_id: str, routine_id: str, tier_id: str) -> tuple[bool, str]:
    """
    Check if (preset, routine, tier) is eligible.
    Returns (eligible, reason_message).
    """
    preset = get_preset(preset_id)
    if not preset:
        return False, f"Unknown preset: {preset_id}"
    max_tier = max_tier_for_routine_under_preset(preset_id, routine_type_for(routine_id))
    if not max_tier:
        return False, f"No eligibility rule for preset={preset_id} routine_type={routine_type_for(routine_id)}"
    tier_ord = _tier_order(tier_id)
    max_ord = _tier_order(max_tier)
    if tier_ord < 0:
        return False, f"Unknown tier: {tier_id}"
    if max_ord < 0:
        return False, f"Unknown max_tier: {max_tier}"
    if tier_ord <= max_ord:
        return True, f"Eligible: tier {tier_id} <= max {max_tier} for preset {preset_id}"
    return False, f"Not eligible: tier {tier_id} exceeds max {max_tier} for preset {preset_id} and routine type {routine_type_for(routine_id)}"


def eligibility_matrix_report(preset_id: str | None = None) -> list[dict[str, Any]]:
    """
    Report which routine types may run at which max tier under which presets.
    If preset_id is set, only that preset; else all presets.
    """
    from workflow_dataset.trust.presets import list_presets
    if preset_id:
        p = get_preset(preset_id)
        presets = [p] if p else []
    else:
        presets = list_presets()
    rows: list[dict[str, Any]] = []
    for p in presets:
        row = {"preset_id": p.preset_id, "preset_name": p.name, "max_authority_tier_id": p.max_authority_tier_id, "routine_types": {}}
        matrix_row = ELIGIBILITY_MATRIX.get(p.preset_id, {})
        for rt in ROUTINE_TYPES:
            max_t = matrix_row.get(rt) or p.max_authority_tier_id
            row["routine_types"][rt] = max_t
        rows.append(row)
    return rows
