"""
M44H.1: Protected memory classes — rules that mark memory as protected with operator-facing explanation.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.memory_curation.models import MemoryProtectionRule
from workflow_dataset.memory_curation.store import load_protection_rules


def get_default_protection_rules() -> list[MemoryProtectionRule]:
    """First-draft default protection rules (corrections, trust, approvals)."""
    return [
        MemoryProtectionRule(
            rule_id="corrections",
            label="Correction-linked memory",
            match_source="corrections",
            match_tags=[],
            match_source_ref_pattern="",
            protection_reason="This memory is linked to user corrections; it is protected from automatic forgetting so that correction context is preserved.",
            created_at_utc="",
            active=True,
        ),
        MemoryProtectionRule(
            rule_id="trust",
            label="Trust and approval memory",
            match_source="trust",
            match_tags=["approval", "trusted"],
            match_source_ref_pattern="",
            protection_reason="This memory is linked to trust or approval decisions; it is protected to avoid losing consent or safety context.",
            created_at_utc="",
            active=True,
        ),
        MemoryProtectionRule(
            rule_id="source_ref_approval",
            label="Approval registry refs",
            match_source="",
            match_tags=[],
            match_source_ref_pattern="approval",
            protection_reason="This memory references approval or consent data; it is protected from automatic forgetting.",
            created_at_utc="",
            active=True,
        ),
    ]


def match_unit_against_rules(
    unit: dict[str, Any],
    rules: list[MemoryProtectionRule] | None = None,
    *,
    source_key: str = "source",
    source_ref_key: str = "source_ref",
    tags_key: str = "tags",
) -> list[MemoryProtectionRule]:
    """
    Return protection rules that match the given unit (source, source_ref, tags).
    Only active rules are considered.
    """
    if rules is None:
        rules = get_default_protection_rules()
    matched = []
    source = (unit.get(source_key) or "").strip()
    source_ref = (unit.get(source_ref_key) or "").strip()
    tags = unit.get(tags_key)
    if isinstance(tags, list):
        tag_set = {str(t).strip() for t in tags}
    else:
        tag_set = set()

    for r in rules:
        if not r.active:
            continue
        if r.match_source and source != r.match_source:
            continue
        if r.match_source_ref_pattern and r.match_source_ref_pattern not in source_ref:
            continue
        if r.match_tags and not (tag_set & set(r.match_tags)):
            continue
        matched.append(r)
    return matched


def explain_why_protected(
    unit: dict[str, Any],
    rules: list[MemoryProtectionRule] | None = None,
) -> str:
    """
    Operator-facing explanation: why this memory item is protected (which rules matched).
    Returns empty string if no rules match.
    """
    matched = match_unit_against_rules(unit, rules)
    if not matched:
        return ""
    parts = [r.protection_reason for r in matched]
    return " ".join(parts) if len(parts) == 1 else "Protected: " + "; ".join(parts)
