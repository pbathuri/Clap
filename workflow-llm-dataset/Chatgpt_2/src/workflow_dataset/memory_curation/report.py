"""
M44E–M44H Phase D: Curation status, archive report, next recommended action.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.memory_curation.store import (
    load_summaries,
    load_compression_candidates,
    load_forgetting_candidates,
    load_review_required,
    load_archival_states,
)
from workflow_dataset.memory_curation.summarization import build_compression_candidates_from_sessions
from workflow_dataset.memory_curation.retention import get_default_policies, get_protected_policies


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def status(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Curation status: counts for summaries, compression candidates, forgetting, review-required, archives."""
    root = _root(repo_root)
    summaries = load_summaries(repo_root)
    comp = load_compression_candidates(repo_root)
    forget = load_forgetting_candidates(repo_root)
    review = load_review_required(repo_root)
    archives = load_archival_states(repo_root)
    return {
        "summaries_count": len(summaries),
        "compression_candidates_count": len(comp),
        "compression_applied_count": sum(1 for c in comp if c.applied),
        "forgetting_candidates_count": len(forget),
        "forgetting_applied_count": sum(1 for c in forget if c.applied),
        "review_required_count": len(review),
        "review_required_pending_count": sum(1 for r in review if not r.reviewed),
        "archives_count": len(archives),
        "curation_dir": str((root / "data" / "local" / "memory_curation").resolve()),
    }


def archive_report(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Report on archival state: archives list, scope, location, retrievable."""
    archives = load_archival_states(repo_root)
    return {
        "archives_count": len(archives),
        "archives": [
            {
                "archive_id": a.archive_id,
                "scope": a.scope,
                "archived_at_utc": a.archived_at_utc,
                "location": a.location,
                "retrievable": a.retrievable,
                "unit_count": len(a.unit_ids),
            }
            for a in archives
        ],
    }


def next_action(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Next recommended curation action: review pending, run compression, run forgetting candidates, or none.
    """
    st = status(repo_root)
    review = load_review_required(repo_root)
    comp = load_compression_candidates(repo_root)
    forget = load_forgetting_candidates(repo_root)
    pending_review = [r for r in review if not r.reviewed]
    unapplied_comp = [c for c in comp if not c.applied]
    unapplied_forget = [c for c in forget if not c.applied and not c.review_required]

    if pending_review:
        return {
            "action": "review_required",
            "message": "Review forgetting candidates that require approval before applying.",
            "count": len(pending_review),
            "command_hint": "workflow-dataset memory-curation forgetting-candidates",
        }
    if unapplied_comp:
        return {
            "action": "summarize",
            "message": "Apply summarization/compression to reduce memory bloat.",
            "count": len(unapplied_comp),
            "command_hint": "workflow-dataset memory-curation summarize",
        }
    if unapplied_forget:
        return {
            "action": "apply_forgetting",
            "message": "Safe-to-forget candidates available (no review required).",
            "count": len(unapplied_forget),
            "command_hint": "workflow-dataset memory-curation forgetting-candidates",
        }
    return {
        "action": "none",
        "message": "No immediate curation action recommended.",
        "count": 0,
        "command_hint": "workflow-dataset memory-curation status",
    }


def mission_control_slice(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Mission-control visibility: growth pressure, top compression candidates, protected classes,
    forgetting awaiting review, next recommended action.
    """
    st = status(repo_root)
    policies = get_default_policies()
    protected = get_protected_policies()
    comp = load_compression_candidates(repo_root)
    review = load_review_required(repo_root)
    nxt = next_action(repo_root)
    # Top compression candidates (unapplied, by item_count)
    top_comp = sorted([c for c in comp if not c.applied], key=lambda c: c.item_count, reverse=True)[:5]
    return {
        "memory_growth_pressure": (
            "high" if st["compression_candidates_count"] > 10 or st["forgetting_candidates_count"] > 50
            else "medium" if st["compression_candidates_count"] > 3 or st["forgetting_candidates_count"] > 10
            else "low"
        ),
        "summaries_count": st["summaries_count"],
        "compression_candidates_count": st["compression_candidates_count"],
        "forgetting_candidates_count": st["forgetting_candidates_count"],
        "forgetting_awaiting_review_count": st["review_required_pending_count"],
        "protected_memory_classes": [p.policy_id for p in protected],
        "top_compression_candidates": [
            {"candidate_id": c.candidate_id, "reason": c.reason, "item_count": c.item_count}
            for c in top_comp
        ],
        "next_action": nxt,
    }
