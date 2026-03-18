"""
M44E–M44H Phase C: Retention policies — short/medium/long/protected; review-required vs safe-to-forget.
"""

from __future__ import annotations

from workflow_dataset.memory_curation.models import (
    RetentionPolicyCuration,
    RETENTION_SHORT,
    RETENTION_MEDIUM,
    RETENTION_LONG,
    RETENTION_PROTECTED,
)

# Default policy set (first-draft)
DEFAULT_POLICIES: list[RetentionPolicyCuration] = [
    RetentionPolicyCuration(
        policy_id="short_lived",
        label="Short-lived memory",
        retention_tier=RETENTION_SHORT,
        max_age_days=7,
        max_units_per_source=0,
        protected=False,
        description="Ephemeral; eligible for summarization or permitted forgetting after 7 days.",
    ),
    RetentionPolicyCuration(
        policy_id="medium_term",
        label="Medium-term working memory",
        retention_tier=RETENTION_MEDIUM,
        max_age_days=30,
        max_units_per_source=500,
        protected=False,
        description="Working memory; can be summarized or forgotten after 30 days or when over 500 units per source.",
    ),
    RetentionPolicyCuration(
        policy_id="long_term",
        label="Long-term durable memory",
        retention_tier=RETENTION_LONG,
        max_age_days=0,
        max_units_per_source=0,
        protected=False,
        description="Durable; keep unless explicitly archived or reviewed for forgetting.",
    ),
    RetentionPolicyCuration(
        policy_id="protected",
        label="Protected memory",
        retention_tier=RETENTION_PROTECTED,
        max_age_days=0,
        max_units_per_source=0,
        protected=True,
        description="Never auto-forget (corrections, trust, approvals); review-required for any deletion.",
    ),
]


def get_default_policies() -> list[RetentionPolicyCuration]:
    """Return the default retention policy set."""
    return list(DEFAULT_POLICIES)


def get_policy_by_id(policy_id: str) -> RetentionPolicyCuration | None:
    """Return policy with given policy_id or None."""
    for p in DEFAULT_POLICIES:
        if p.policy_id == policy_id:
            return p
    return None


def get_protected_policies() -> list[RetentionPolicyCuration]:
    """Return policies that mark memory as protected (no auto-forget)."""
    return [p for p in DEFAULT_POLICIES if p.protected]


def retention_tier_requires_review(tier: str) -> bool:
    """True if forgetting under this tier must go through review."""
    return tier == RETENTION_PROTECTED or tier == RETENTION_LONG
