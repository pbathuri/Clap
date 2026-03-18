"""
M44A: Memory OS model — namespace, retrieval surface, intent, scope, evidence bundle, explanation, freshness, trusted vs weak.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ----- Namespace -----

@dataclass
class MemoryNamespace:
    """Logical namespace for memory (personal, product, learning, cursor)."""
    namespace_id: str = ""
    label: str = ""
    description: str = ""
    storage_hint: str = ""  # substrate | fusion | slices

    def to_dict(self) -> dict[str, Any]:
        return {
            "namespace_id": self.namespace_id,
            "label": self.label,
            "description": self.description,
            "storage_hint": self.storage_hint,
        }


# ----- Retrieval surface -----

@dataclass
class RetrievalSurface:
    """Named retrieval surface: project, session, episode, continuity, operator, learning, cursor."""
    surface_id: str = ""
    label: str = ""
    description: str = ""
    entity_types: list[str] = field(default_factory=list)  # project | session | episode | routine
    supports_intents: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface_id": self.surface_id,
            "label": self.label,
            "description": self.description,
            "entity_types": list(self.entity_types),
            "supports_intents": list(self.supports_intents),
        }


# ----- Retrieval intent (OS-level) -----

RETRIEVAL_INTENT_RECALL_CONTEXT = "recall_context"
RETRIEVAL_INTENT_RECALL_SIMILAR_CASE = "recall_similar_case"
RETRIEVAL_INTENT_RECALL_BLOCKER = "recall_blocker"
RETRIEVAL_INTENT_RECALL_PATTERN = "recall_pattern"
RETRIEVAL_INTENT_RECALL_DECISION_RATIONALE = "recall_decision_rationale"
RETRIEVAL_INTENT_RECALL_REVIEW_HISTORY = "recall_review_history"

RETRIEVAL_INTENTS = [
    RETRIEVAL_INTENT_RECALL_CONTEXT,
    RETRIEVAL_INTENT_RECALL_SIMILAR_CASE,
    RETRIEVAL_INTENT_RECALL_BLOCKER,
    RETRIEVAL_INTENT_RECALL_PATTERN,
    RETRIEVAL_INTENT_RECALL_DECISION_RATIONALE,
    RETRIEVAL_INTENT_RECALL_REVIEW_HISTORY,
]


@dataclass
class RetrievalIntentOS:
    """OS-level retrieval intent: named intent + optional query + limit."""
    intent: str = RETRIEVAL_INTENT_RECALL_CONTEXT
    query: str = ""
    top_k: int = 20

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "query": self.query,
            "top_k": self.top_k,
        }


# ----- Retrieval scope -----

@dataclass
class RetrievalScope:
    """Scope for retrieval: project_id, session_id, episode_id, optional time window."""
    project_id: str = ""
    session_id: str = ""
    episode_id: str = ""
    entity_type: str = ""  # project | session | episode | routine
    entity_id: str = ""
    time_window_hours: float = 0.0  # 0 = no time filter

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "session_id": self.session_id,
            "episode_id": self.episode_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "time_window_hours": self.time_window_hours,
        }


# ----- Evidence bundle -----

@dataclass
class MemoryEvidenceItem:
    """Single evidence item: unit or link with score and provenance."""
    memory_id: str = ""
    source: str = ""  # substrate | fusion_link
    score: float = 0.0
    provenance_ref: str = ""
    snippet: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "source": self.source,
            "score": self.score,
            "provenance_ref": self.provenance_ref,
            "snippet": self.snippet[:300] if self.snippet else "",
        }


@dataclass
class MemoryEvidenceBundle:
    """Bundle of evidence items for a retrieval result."""
    retrieval_id: str = ""
    items: list[MemoryEvidenceItem] = field(default_factory=list)
    total_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "retrieval_id": self.retrieval_id,
            "items": [i.to_dict() for i in self.items],
            "total_count": self.total_count,
        }


# ----- Retrieval explanation -----

@dataclass
class RetrievalExplanation:
    """Why this memory was retrieved: reason, evidence, confidence, near-matches, weak warnings, profile."""
    retrieval_id: str = ""
    reason: str = ""
    evidence_bundle: MemoryEvidenceBundle | None = None
    confidence: float = 0.0  # 0–1
    near_match_ids: list[str] = field(default_factory=list)
    weak_memory_warnings: list[str] = field(default_factory=list)
    no_match_reason: str = ""  # when empty result
    profile_used: str = ""      # M44D.1: which retrieval profile was applied
    profile_reason: str = ""    # M44D.1: why this profile was preferred over others

    def to_dict(self) -> dict[str, Any]:
        return {
            "retrieval_id": self.retrieval_id,
            "reason": self.reason,
            "evidence_bundle": self.evidence_bundle.to_dict() if self.evidence_bundle else None,
            "confidence": self.confidence,
            "near_match_ids": list(self.near_match_ids),
            "weak_memory_warnings": list(self.weak_memory_warnings),
            "no_match_reason": self.no_match_reason,
            "profile_used": self.profile_used,
            "profile_reason": self.profile_reason,
        }


# ----- Freshness / recency / confidence -----

@dataclass
class FreshnessMarkers:
    """Freshness, recency, and confidence markers for a memory item."""
    last_updated_utc: str = ""
    created_at_utc: str = ""
    recency_tier: str = ""  # recent | older | stale
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_updated_utc": self.last_updated_utc,
            "created_at_utc": self.created_at_utc,
            "recency_tier": self.recency_tier,
            "confidence": self.confidence,
        }


# ----- Trusted vs weak -----

TRUSTED_MEMORY = "trusted"
WEAK_MEMORY = "weak"


@dataclass
class TrustedMemoryMarker:
    """Marks memory as trusted (high confidence, reviewed) or weak (low confidence, needs_review)."""
    memory_id: str = ""
    tier: str = TRUSTED_MEMORY  # trusted | weak
    confidence: float = 0.0
    needs_review: bool = False
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "tier": self.tier,
            "confidence": self.confidence,
            "needs_review": self.needs_review,
            "reason": self.reason,
        }


# ----- M44D.1: Retrieval profiles -----

PROFILE_CONSERVATIVE = "conservative"
PROFILE_CONTINUITY_HEAVY = "continuity_heavy"
PROFILE_OPERATOR_HEAVY = "operator_heavy"
PROFILE_CODING_HEAVY = "coding_heavy"

RETRIEVAL_PROFILE_IDS = [
    PROFILE_CONSERVATIVE,
    PROFILE_CONTINUITY_HEAVY,
    PROFILE_OPERATOR_HEAVY,
    PROFILE_CODING_HEAVY,
]


@dataclass
class RetrievalProfile:
    """
    Retrieval profile: presets for surface/intent weighting and filters.
    conservative: high-confidence only, fewer items, trusted only.
    continuity_heavy: weight continuity surface, context + blocker.
    operator_heavy: weight operator surface, decision_rationale, review_history.
    coding_heavy: weight cursor surface, pattern + context.
    """
    profile_id: str = ""
    label: str = ""
    description: str = ""
    surface_weights: dict[str, float] = field(default_factory=dict)  # surface_id -> weight 0..1
    intent_weights: dict[str, float] = field(default_factory=dict)   # intent -> weight 0..1
    min_confidence: float = 0.0   # filter out below this (0 = no filter)
    max_items: int = 20           # cap items returned
    trusted_only: bool = False    # if True, exclude weak tier
    preference_reason: str = ""  # why this profile is preferred over others in certain contexts

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "label": self.label,
            "description": self.description,
            "surface_weights": dict(self.surface_weights),
            "intent_weights": dict(self.intent_weights),
            "min_confidence": self.min_confidence,
            "max_items": self.max_items,
            "trusted_only": self.trusted_only,
            "preference_reason": self.preference_reason,
        }


# ----- M44D.1: Vertical memory views -----

@dataclass
class VerticalMemoryView:
    """
    Vertical-specific memory view: which surfaces and profile to use for a product vertical.
    Enables "project vertical", "session vertical", "learning vertical", "coding vertical", etc.
    """
    view_id: str = ""
    vertical_id: str = ""   # project | session | learning | coding | continuity | operator
    label: str = ""
    description: str = ""
    surface_ids: list[str] = field(default_factory=list)   # ordered preference
    preferred_profile_id: str = ""
    why_this_profile: str = ""  # why this profile is preferred for this vertical

    def to_dict(self) -> dict[str, Any]:
        return {
            "view_id": self.view_id,
            "vertical_id": self.vertical_id,
            "label": self.label,
            "description": self.description,
            "surface_ids": list(self.surface_ids),
            "preferred_profile_id": self.preferred_profile_id,
            "why_this_profile": self.why_this_profile,
        }
