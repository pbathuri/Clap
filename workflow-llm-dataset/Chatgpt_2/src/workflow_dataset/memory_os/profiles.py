"""
M44D.1: Retrieval profiles — conservative, continuity-heavy, operator-heavy, coding-heavy.
"""

from __future__ import annotations

from workflow_dataset.memory_os.models import (
    RetrievalProfile,
    PROFILE_CONSERVATIVE,
    PROFILE_CONTINUITY_HEAVY,
    PROFILE_OPERATOR_HEAVY,
    PROFILE_CODING_HEAVY,
)
from workflow_dataset.memory_os.surfaces import (
    SURFACE_PROJECT,
    SURFACE_SESSION,
    SURFACE_CONTINUITY,
    SURFACE_OPERATOR,
    SURFACE_CURSOR,
    SURFACE_LEARNING,
)
from workflow_dataset.memory_os.models import (
    RETRIEVAL_INTENT_RECALL_CONTEXT,
    RETRIEVAL_INTENT_RECALL_BLOCKER,
    RETRIEVAL_INTENT_RECALL_DECISION_RATIONALE,
    RETRIEVAL_INTENT_RECALL_REVIEW_HISTORY,
    RETRIEVAL_INTENT_RECALL_PATTERN,
)

_PROFILES: list[RetrievalProfile] = [
    RetrievalProfile(
        profile_id=PROFILE_CONSERVATIVE,
        label="Conservative",
        description="High-confidence only, fewer items, trusted memory only. Use when decisions must be low-risk.",
        surface_weights={s: 0.5 for s in [SURFACE_PROJECT, SURFACE_SESSION]},
        intent_weights={RETRIEVAL_INTENT_RECALL_CONTEXT: 1.0},
        min_confidence=0.7,
        max_items=10,
        trusted_only=True,
        preference_reason="Conservative profile prefers high-confidence, trusted-only memory and fewer items; reduces noise and weak links.",
    ),
    RetrievalProfile(
        profile_id=PROFILE_CONTINUITY_HEAVY,
        label="Continuity-heavy",
        description="Weight continuity and resume context; recall_context and recall_blocker.",
        surface_weights={
            SURFACE_CONTINUITY: 1.0,
            SURFACE_SESSION: 0.8,
            SURFACE_PROJECT: 0.6,
        },
        intent_weights={
            RETRIEVAL_INTENT_RECALL_CONTEXT: 1.0,
            RETRIEVAL_INTENT_RECALL_BLOCKER: 1.0,
        },
        min_confidence=0.0,
        max_items=20,
        trusted_only=False,
        preference_reason="Continuity-heavy profile prioritizes resume and next-session context and unresolved blockers; best for picking up where you left off.",
    ),
    RetrievalProfile(
        profile_id=PROFILE_OPERATOR_HEAVY,
        label="Operator-heavy",
        description="Weight operator/history surface; decision rationale and review history.",
        surface_weights={
            SURFACE_OPERATOR: 1.0,
            SURFACE_PROJECT: 0.7,
            SURFACE_SESSION: 0.6,
        },
        intent_weights={
            RETRIEVAL_INTENT_RECALL_DECISION_RATIONALE: 1.0,
            RETRIEVAL_INTENT_RECALL_REVIEW_HISTORY: 1.0,
            RETRIEVAL_INTENT_RECALL_CONTEXT: 0.8,
        },
        min_confidence=0.0,
        max_items=20,
        trusted_only=False,
        preference_reason="Operator-heavy profile emphasizes operator decisions and review history; best for understanding past choices and approvals.",
    ),
    RetrievalProfile(
        profile_id=PROFILE_CODING_HEAVY,
        label="Coding-heavy",
        description="Weight cursor/coding surface; pattern and context recall.",
        surface_weights={
            SURFACE_CURSOR: 1.0,
            SURFACE_LEARNING: 0.7,
            SURFACE_SESSION: 0.5,
        },
        intent_weights={
            RETRIEVAL_INTENT_RECALL_PATTERN: 1.0,
            RETRIEVAL_INTENT_RECALL_CONTEXT: 1.0,
        },
        min_confidence=0.0,
        max_items=15,
        trusted_only=False,
        preference_reason="Coding-heavy profile prioritizes Cursor and coding context and patterns; best for in-IDE and learning workflows.",
    ),
]


def list_profiles() -> list[RetrievalProfile]:
    """Return all retrieval profiles."""
    return list(_PROFILES)


def get_profile(profile_id: str) -> RetrievalProfile | None:
    """Return profile by id."""
    for p in _PROFILES:
        if p.profile_id == profile_id:
            return p
    return None


def get_profile_reason(profile_id: str) -> str:
    """Return human-readable reason why this profile is preferred over others in its intended context."""
    p = get_profile(profile_id)
    if p:
        return p.preference_reason or f"Profile {profile_id} applied."
    return f"Unknown profile {profile_id}."


def apply_profile_filters(
    items: list[dict],
    profile: RetrievalProfile | None,
) -> list[dict]:
    """Filter and cap items by profile: min_confidence, trusted_only, max_items."""
    if not profile:
        return items
    out = items
    if profile.min_confidence > 0:
        out = [it for it in out if (it.get("confidence") or 0) >= profile.min_confidence]
    if profile.trusted_only:
        out = [it for it in out if (it.get("tier") or "") == "trusted"]
    if profile.max_items > 0:
        out = out[: profile.max_items]
    return out
