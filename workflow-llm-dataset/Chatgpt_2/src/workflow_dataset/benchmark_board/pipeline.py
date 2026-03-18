"""
M42I–M42L: Promotion/rollback pipeline — reject, quarantine, promote (experimental/limited/production), rollback.
Every decision is explicit and persisted.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.benchmark_board.store import (
    append_promotion_decision,
    append_rollback,
    add_quarantined,
    remove_quarantined,
    get_quarantined,
    set_promoted,
    get_latest_promoted,
    get_benchmark_board_dir,
)


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def reject_candidate(
    candidate_id: str,
    reason: str = "",
    scorecard_id: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Record rejection of candidate; do not promote. Explicit decision."""
    root = _repo_root(repo_root)
    get_benchmark_board_dir(repo_root=root).mkdir(parents=True, exist_ok=True)
    append_promotion_decision(candidate_id, "reject", scope="", reason=reason or "Rejected by operator", scorecard_id=scorecard_id, repo_root=root)
    return {"candidate_id": candidate_id, "decision": "reject", "reason": reason or "Rejected by operator"}


def quarantine_candidate(
    candidate_id: str,
    reason: str = "",
    scorecard_id: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Quarantine candidate; add to quarantined list and record decision."""
    root = _repo_root(repo_root)
    get_benchmark_board_dir(repo_root=root).mkdir(parents=True, exist_ok=True)
    add_quarantined(candidate_id, repo_root=root)
    append_promotion_decision(candidate_id, "quarantine", scope="", reason=reason or "Quarantined for review", scorecard_id=scorecard_id, repo_root=root)
    return {"candidate_id": candidate_id, "decision": "quarantine", "reason": reason or "Quarantined for review"}


def promote_experimental(
    candidate_id: str,
    reason: str = "",
    scorecard_id: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Promote candidate to experimental surface only. Explicit decision."""
    root = _repo_root(repo_root)
    get_benchmark_board_dir(repo_root=root).mkdir(parents=True, exist_ok=True)
    set_promoted(candidate_id, "experimental_only", repo_root=root)
    append_promotion_decision(candidate_id, "promote_experimental", scope="experimental_only", reason=reason or "Promoted to experimental", scorecard_id=scorecard_id, repo_root=root)
    return {"candidate_id": candidate_id, "decision": "promote_experimental", "scope": "experimental_only", "reason": reason or "Promoted to experimental"}


def promote_limited_cohort(
    candidate_id: str,
    reason: str = "",
    scorecard_id: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Promote candidate to limited cohort only. Explicit decision."""
    root = _repo_root(repo_root)
    get_benchmark_board_dir(repo_root=root).mkdir(parents=True, exist_ok=True)
    set_promoted(candidate_id, "limited_cohort", repo_root=root)
    append_promotion_decision(candidate_id, "promote_limited_cohort", scope="limited_cohort", reason=reason or "Promoted to limited cohort", scorecard_id=scorecard_id, repo_root=root)
    return {"candidate_id": candidate_id, "decision": "promote_limited_cohort", "scope": "limited_cohort", "reason": reason or "Promoted to limited cohort"}


def promote_production_safe(
    candidate_id: str,
    reason: str = "",
    scorecard_id: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Promote candidate to production-safe route. Explicit decision."""
    root = _repo_root(repo_root)
    get_benchmark_board_dir(repo_root=root).mkdir(parents=True, exist_ok=True)
    set_promoted(candidate_id, "production_safe", repo_root=root)
    append_promotion_decision(candidate_id, "promote_production_safe", scope="production_safe", reason=reason or "Promoted to production-safe", scorecard_id=scorecard_id, repo_root=root)
    return {"candidate_id": candidate_id, "decision": "promote_production_safe", "scope": "production_safe", "reason": reason or "Promoted to production-safe"}


def rollback_to_prior(
    candidate_id: str,
    prior_id: str,
    reason: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Roll back from candidate to prior model/run. Explicit decision; record in rollback history."""
    root = _repo_root(repo_root)
    get_benchmark_board_dir(repo_root=root).mkdir(parents=True, exist_ok=True)
    append_rollback(candidate_id, prior_id, reason=reason or "Rollback by operator", repo_root=root)
    return {"candidate_id": candidate_id, "prior_id": prior_id, "reason": reason or "Rollback by operator"}
