"""
M44E–M44H Phase A: Memory curation models — ephemeral, durable, summarized unit,
compression candidate, forgetting candidate, retention policy, review-required deletion, archival state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Retention tiers (curation-level)
RETENTION_SHORT = "short_lived"       # e.g. days; can summarize or drop
RETENTION_MEDIUM = "medium_term"     # working memory; weeks
RETENTION_LONG = "long_term"         # durable; keep
RETENTION_PROTECTED = "protected"    # never auto-forget (corrections, trust, approvals)


@dataclass
class EphemeralMemory:
    """Memory classified as short-lived; eligible for summarization or permitted forgetting under policy."""
    unit_id: str = ""
    source: str = ""
    source_ref: str = ""
    created_at_utc: str = ""
    expires_at_utc: str = ""
    summary_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "source": self.source,
            "source_ref": self.source_ref,
            "created_at_utc": self.created_at_utc,
            "expires_at_utc": self.expires_at_utc,
            "summary_hint": self.summary_hint,
        }


@dataclass
class DurableMemory:
    """Memory classified as long-term durable; protect from automatic forgetting."""
    unit_id: str = ""
    source: str = ""
    source_ref: str = ""
    created_at_utc: str = ""
    retention_tier: str = RETENTION_LONG
    protected_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "source": self.source,
            "source_ref": self.source_ref,
            "created_at_utc": self.created_at_utc,
            "retention_tier": self.retention_tier,
            "protected_reason": self.protected_reason,
        }


@dataclass
class SummarizedMemoryUnit:
    """Rollup of multiple units/sessions; preserves provenance (source_unit_ids, source_session_ids)."""
    summary_id: str = ""
    summary_text: str = ""
    source_unit_ids: list[str] = field(default_factory=list)
    source_session_ids: list[str] = field(default_factory=list)
    source_kind: str = ""  # repeated_events | session_history | operator_pattern | episode_chain
    created_at_utc: str = ""
    keyword_tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary_id": self.summary_id,
            "summary_text": self.summary_text,
            "source_unit_ids": list(self.source_unit_ids),
            "source_session_ids": list(self.source_session_ids),
            "source_kind": self.source_kind,
            "created_at_utc": self.created_at_utc,
            "keyword_tags": list(self.keyword_tags),
        }


@dataclass
class CompressionCandidate:
    """Identified batch of items/units to compress into one summary."""
    candidate_id: str = ""
    unit_ids: list[str] = field(default_factory=list)
    session_ids: list[str] = field(default_factory=list)
    reason: str = ""  # repeated_events | old_session_chunk | similar_keywords
    item_count: int = 0
    created_at_utc: str = ""
    applied: bool = False
    resulting_summary_id: str = ""
    operator_explanation: str = ""  # M44H.1: why this is compressible (operator-facing)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "unit_ids": list(self.unit_ids),
            "session_ids": list(self.session_ids),
            "reason": self.reason,
            "item_count": self.item_count,
            "created_at_utc": self.created_at_utc,
            "applied": self.applied,
            "resulting_summary_id": self.resulting_summary_id,
            "operator_explanation": self.operator_explanation,
        }


@dataclass
class ForgettingCandidate:
    """Item/unit or batch proposed for forgetting (under policy or after summarization)."""
    candidate_id: str = ""
    unit_ids: list[str] = field(default_factory=list)
    reason: str = ""  # expired_short_lived | summarized | low_access | policy_medium_term
    created_at_utc: str = ""
    review_required: bool = True
    applied: bool = False
    operator_explanation: str = ""  # M44H.1: why this is forgettable (operator-facing)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "unit_ids": list(self.unit_ids),
            "reason": self.reason,
            "created_at_utc": self.created_at_utc,
            "review_required": self.review_required,
            "applied": self.applied,
            "operator_explanation": self.operator_explanation,
        }


@dataclass
class RetentionPolicyCuration:
    """Curation-level retention policy: short/medium/long/protected with optional max age and caps."""
    policy_id: str = ""
    label: str = ""
    retention_tier: str = RETENTION_MEDIUM
    max_age_days: int = 0  # 0 = no hard cap from this policy
    max_units_per_source: int = 0  # 0 = no cap
    protected: bool = False
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "label": self.label,
            "retention_tier": self.retention_tier,
            "max_age_days": self.max_age_days,
            "max_units_per_source": self.max_units_per_source,
            "protected": self.protected,
            "description": self.description,
        }


@dataclass
class ReviewRequiredDeletionCandidate:
    """Forgetting candidate that must not be applied until operator review."""
    candidate_id: str = ""
    forgetting_candidate_id: str = ""
    unit_ids: list[str] = field(default_factory=list)
    reason: str = ""
    high_value_hint: bool = False  # e.g. linked to corrections/trust
    created_at_utc: str = ""
    reviewed: bool = False
    approved_for_forget: bool = False
    operator_explanation: str = ""  # M44H.1: why review is required / what would be forgotten

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "forgetting_candidate_id": self.forgetting_candidate_id,
            "unit_ids": list(self.unit_ids),
            "reason": self.reason,
            "high_value_hint": self.high_value_hint,
            "created_at_utc": self.created_at_utc,
            "reviewed": self.reviewed,
            "approved_for_forget": self.approved_for_forget,
            "operator_explanation": self.operator_explanation,
        }


@dataclass
class ArchivalState:
    """Archived-but-retrievable state: moved to archive or marked archived with pointer."""
    archive_id: str = ""
    unit_ids: list[str] = field(default_factory=list)
    scope: str = ""  # e.g. event_log_2024_q1, session_history_old
    archived_at_utc: str = ""
    location: str = ""  # path or store ref
    retrievable: bool = True
    policy_id: str = ""  # M44H.1: optional link to ArchivalPolicyCuration

    def to_dict(self) -> dict[str, Any]:
        return {
            "archive_id": self.archive_id,
            "unit_ids": list(self.unit_ids),
            "scope": self.scope,
            "archived_at_utc": self.archived_at_utc,
            "location": self.location,
            "retrievable": self.retrievable,
            "policy_id": self.policy_id,
        }


# ----- M44H.1: Protection rules, review packs, archival policies -----


@dataclass
class MemoryProtectionRule:
    """Rule that marks memory as protected; operator-facing explanation of why."""
    rule_id: str = ""
    label: str = ""
    match_source: str = ""  # optional: source must equal (e.g. corrections, trust)
    match_tags: list[str] = field(default_factory=list)  # any of these tags present
    match_source_ref_pattern: str = ""  # optional: substring match on source_ref
    protection_reason: str = ""  # operator-facing: why this memory is protected
    created_at_utc: str = ""
    active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "label": self.label,
            "match_source": self.match_source,
            "match_tags": list(self.match_tags),
            "match_source_ref_pattern": self.match_source_ref_pattern,
            "protection_reason": self.protection_reason,
            "created_at_utc": self.created_at_utc,
            "active": self.active,
        }


@dataclass
class ReviewPackItem:
    """Single item in a review pack: either forgetting or compression action."""
    item_id: str = ""
    kind: str = ""  # forgetting | compression
    candidate_id: str = ""
    unit_ids: list[str] = field(default_factory=list)
    reason: str = ""
    operator_explanation: str = ""
    approved: bool | None = None  # None = not yet decided, True/False = operator decision

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "kind": self.kind,
            "candidate_id": self.candidate_id,
            "unit_ids": list(self.unit_ids),
            "reason": self.reason,
            "operator_explanation": self.operator_explanation,
            "approved": self.approved,
        }


@dataclass
class ReviewPack:
    """Bundle of forgetting/compression actions for operator review in one go."""
    pack_id: str = ""
    label: str = ""
    items: list[ReviewPackItem] = field(default_factory=list)
    created_at_utc: str = ""
    reviewed_at_utc: str = ""
    status: str = ""  # pending | reviewed

    def to_dict(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "label": self.label,
            "items": [i.to_dict() for i in self.items],
            "created_at_utc": self.created_at_utc,
            "reviewed_at_utc": self.reviewed_at_utc,
            "status": self.status,
        }


@dataclass
class ArchivalPolicyCuration:
    """Safer long-term archival: min age, review required, caps."""
    policy_id: str = ""
    label: str = ""
    min_age_days: int = 0  # do not archive before this age
    require_review_before_archive: bool = True
    max_archives_per_scope: int = 0  # 0 = no cap
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "label": self.label,
            "min_age_days": self.min_age_days,
            "require_review_before_archive": self.require_review_before_archive,
            "max_archives_per_scope": self.max_archives_per_scope,
            "description": self.description,
        }
