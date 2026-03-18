"""
M46L.1: Long-run rollback policies — when to recommend rollback, prior stable ref resolution.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.stability_reviews.models import RollbackPolicy


DEFAULT_ROLLBACK_POLICY = RollbackPolicy(
    policy_id="default",
    label="Default long-run rollback policy",
    recommend_rollback_on_guidance=True,
    recommend_rollback_on_cohort_downgrade=True,
    max_blockers_before_rollback_considered=0,
    max_consecutive_pause_before_rollback_considered=3,
    prior_stable_ref_rule="latest_continue_review",
    description="Recommend rollback when guidance=rollback or cohort downgrade; prior stable = latest review with decision=continue.",
)


def get_default_rollback_policy() -> RollbackPolicy:
    return DEFAULT_ROLLBACK_POLICY


def load_rollback_policy(repo_root: Path | str | None = None) -> RollbackPolicy:
    """Load rollback policy from store, or return default."""
    root = _repo_root(repo_root)
    path = root / "data/local/stability_reviews/rollback_policy.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return _policy_from_dict(data)
        except Exception:
            pass
    return get_default_rollback_policy()


def save_rollback_policy(
    policy: RollbackPolicy,
    repo_root: Path | str | None = None,
) -> Path:
    """Persist rollback policy. Returns path to rollback_policy.json."""
    root = _repo_root(repo_root)
    d = root / "data/local/stability_reviews"
    d.mkdir(parents=True, exist_ok=True)
    path = d / "rollback_policy.json"
    path.write_text(json.dumps(policy.to_dict(), indent=2), encoding="utf-8")
    return path


def evaluate_rollback_policy(
    policy: RollbackPolicy,
    guidance: str,
    cohort_recommends_downgrade: bool,
    blocker_count: int,
    consecutive_pause_count: int,
) -> tuple[bool, str]:
    """
    Returns (should_recommend_rollback, reason).
    Does not execute rollback; only recommends.
    """
    if policy.recommend_rollback_on_guidance and (guidance or "").lower() == "rollback":
        return True, "Post-deployment guidance recommends rollback."
    if policy.recommend_rollback_on_cohort_downgrade and cohort_recommends_downgrade:
        return True, "Cohort health recommends downgrade."
    if blocker_count > policy.max_blockers_before_rollback_considered:
        if consecutive_pause_count >= policy.max_consecutive_pause_before_rollback_considered:
            return True, f"Blockers={blocker_count} and {consecutive_pause_count} consecutive pause reviews; consider rollback."
    return False, ""


def resolve_prior_stable_ref(
    policy: RollbackPolicy,
    reviews: list[dict[str, Any]],
) -> str:
    """
    Resolve prior_stable_ref from policy rule and review history.
    reviews: newest first (from list_reviews).
    """
    if policy.prior_stable_ref_rule == "manual" or not reviews:
        return ""
    if policy.prior_stable_ref_rule == "latest_continue_review":
        for r in reviews:
            rec = (r.get("decision_pack") or {}).get("recommended_decision", "")
            if rec in ("continue", "continue_with_watch"):
                return r.get("review_id", "")
    if policy.prior_stable_ref_rule == "latest_checkpoint":
        for r in reviews:
            if r.get("review_id"):
                return r.get("review_id", "")
    return ""


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _policy_from_dict(data: dict[str, Any]) -> RollbackPolicy:
    return RollbackPolicy(
        policy_id=data.get("policy_id", "default"),
        label=data.get("label", ""),
        recommend_rollback_on_guidance=data.get("recommend_rollback_on_guidance", True),
        recommend_rollback_on_cohort_downgrade=data.get("recommend_rollback_on_cohort_downgrade", True),
        max_blockers_before_rollback_considered=data.get("max_blockers_before_rollback_considered", 0),
        max_consecutive_pause_before_rollback_considered=data.get("max_consecutive_pause_before_rollback_considered", 3),
        prior_stable_ref_rule=data.get("prior_stable_ref_rule", "latest_continue_review"),
        description=data.get("description", ""),
    )
