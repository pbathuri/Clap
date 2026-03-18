"""
M44H.1: Operator-facing explanations — why a memory item is protected, compressible, or forgettable.
"""

from __future__ import annotations

from workflow_dataset.memory_curation.retention import get_policy_by_id
from workflow_dataset.memory_curation.models import RETENTION_SHORT, RETENTION_MEDIUM


# Reason -> short operator-facing label
FORGET_REASON_LABELS: dict[str, str] = {
    "expired_short_lived": "Short-lived memory older than policy limit (e.g. 7 days); safe to forget.",
    "summarized": "Content has been summarized into a rollup; original units can be forgotten.",
    "low_access": "Rarely or never accessed; eligible for forgetting under policy.",
    "policy_medium_term": "Medium-term working memory past retention (e.g. 30 days); review recommended before forgetting.",
    "max_units_per_source": "Source has exceeded maximum units per source; oldest units are forgettable.",
}

COMPRESS_REASON_LABELS: dict[str, str] = {
    "repeated_events": "Repeated similar events can be compressed into one summary.",
    "old_session_chunk": "Older session chunk; compress to reduce bloat while keeping provenance.",
    "similar_keywords": "Units share keywords; good candidate for a single summarized unit.",
    "session_history": "Session history rollup; many units from one session become one summary.",
}


def build_forgettable_explanation(
    reason: str,
    retention_tier: str = "",
    policy_label: str = "",
) -> str:
    """Build operator-facing explanation for why something is forgettable."""
    base = FORGET_REASON_LABELS.get(reason) or f"Forgettable under policy: {reason}."
    if retention_tier and not policy_label:
        p = get_policy_by_id(retention_tier) if retention_tier in ("short_lived", "medium_term", "long_term", "protected") else None
        if p:
            policy_label = p.label
    if policy_label:
        return f"{base} (Policy: {policy_label})"
    return base


def build_compressible_explanation(reason: str, item_count: int = 0) -> str:
    """Build operator-facing explanation for why something is compressible."""
    base = COMPRESS_REASON_LABELS.get(reason) or f"Compressible: {reason}."
    if item_count > 0:
        return f"{base} ({item_count} units would become one summary.)"
    return base


def build_review_required_explanation(
    reason: str,
    high_value_hint: bool = False,
) -> str:
    """Build operator-facing explanation for why review is required before forgetting."""
    base = FORGET_REASON_LABELS.get(reason) or f"Review required: {reason}."
    if high_value_hint:
        return f"{base} This item may be high-value (e.g. linked to corrections or trust); confirm before forgetting."
    return base
