"""
M44H.1: Safer long-term archival policies — min age, review required, caps.
"""

from __future__ import annotations

from workflow_dataset.memory_curation.models import ArchivalPolicyCuration
from workflow_dataset.memory_curation.store import load_archival_policies, save_archival_policies


DEFAULT_ARCHIVAL_POLICIES: list[ArchivalPolicyCuration] = [
    ArchivalPolicyCuration(
        policy_id="session_history_old",
        label="Old session history",
        min_age_days=90,
        require_review_before_archive=True,
        max_archives_per_scope=12,
        description="Session history older than 90 days; require operator review before archiving. Cap 12 archives per scope.",
    ),
    ArchivalPolicyCuration(
        policy_id="event_log_quarterly",
        label="Quarterly event log",
        min_age_days=60,
        require_review_before_archive=True,
        max_archives_per_scope=8,
        description="Event log segments; minimum 60 days old before archival. Review required.",
    ),
    ArchivalPolicyCuration(
        policy_id="outcome_history_old",
        label="Old outcome history",
        min_age_days=180,
        require_review_before_archive=True,
        max_archives_per_scope=4,
        description="Outcome history older than 180 days; review before archive. Keeps recent signals intact.",
    ),
]


def get_default_archival_policies() -> list[ArchivalPolicyCuration]:
    """Return the default archival policy set."""
    return list(DEFAULT_ARCHIVAL_POLICIES)


def get_archival_policy_by_id(policy_id: str, repo_root=None) -> ArchivalPolicyCuration | None:
    """Return archival policy by id; check stored first, then defaults."""
    stored = load_archival_policies(repo_root)
    for p in stored:
        if p.policy_id == policy_id:
            return p
    for p in DEFAULT_ARCHIVAL_POLICIES:
        if p.policy_id == policy_id:
            return p
    return None


def ensure_archival_policies_saved(repo_root=None) -> None:
    """If no stored policies exist, write defaults to store."""
    stored = load_archival_policies(repo_root)
    if not stored:
        save_archival_policies(DEFAULT_ARCHIVAL_POLICIES, repo_root)
