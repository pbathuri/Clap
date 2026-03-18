"""
M24N–M24Q: Bridge session outcomes to corrections, trust review, pack refinement, next-run recommendations.
Proposes only; no auto-apply.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.outcomes.signals import generate_improvement_signals
from workflow_dataset.outcomes.store import list_session_outcomes
from workflow_dataset.outcomes.patterns import most_useful_per_pack, repeated_block_patterns


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def outcome_to_correction_suggestions(
    repo_root: Path | str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Suggest correction events from outcome signals (e.g. recurring blocker -> suggest correction category). No side effects."""
    root = _repo_root(repo_root)
    signals = generate_improvement_signals(repo_root=root)
    suggestions: list[dict[str, Any]] = []
    for s in signals.get("signals_list", [])[:limit]:
        if s.get("signal_type") in ("recurring_blocker", "job_fails_repeatedly"):
            suggestions.append({
                "suggested_category": "missing_approval_blocker_explanation" if "approval" in (s.get("detail") or "") else "other",
                "source_ref": s.get("ref", ""),
                "reason": s.get("title", ""),
                "action": "Consider adding correction via corrections capture",
            })
    return suggestions


def pack_refinement_suggestions(
    repo_root: Path | str | None = None,
    pack_id: str | None = None,
) -> list[dict[str, Any]]:
    """Suggest pack refinements from outcomes: high-value jobs to promote, recurring blockers to document. No side effects."""
    root = _repo_root(repo_root)
    useful = most_useful_per_pack(repo_root=root, top_n=5)
    blocks = repeated_block_patterns(repo_root=root, min_occurrences=2, limit=20)
    suggestions: list[dict[str, Any]] = []
    for u in useful:
        if pack_id and u.get("pack_id") != pack_id:
            continue
        suggestions.append({
            "kind": "promote_high_value",
            "pack_id": u.get("pack_id", ""),
            "source_ref": u.get("source_ref", ""),
            "detail": f"Score {u.get('score', 0)} from outcomes; consider highlighting in first-value flow.",
        })
    for b in blocks:
        suggestions.append({
            "kind": "document_blocker",
            "source_ref": b.get("source_ref", ""),
            "cause_code": b.get("cause_code", ""),
            "detail": f"Recurring block (count={b.get('count', 0)}); consider documenting in pack trust notes.",
        })
    return suggestions[:15]


def next_run_recommendations(
    repo_root: Path | str | None = None,
    pack_id: str | None = None,
) -> list[dict[str, Any]]:
    """Recommend next run: e.g. run high-value job again, resolve blocker before retry. No side effects."""
    root = _repo_root(repo_root)
    signals = generate_improvement_signals(repo_root=root)
    recs: list[dict[str, Any]] = []
    for s in signals.get("macro_or_job_highly_useful", [])[:5]:
        if pack_id and s.get("pack_id") != pack_id:
            continue
        recs.append({
            "kind": "next_run",
            "title": f"Run again: {s.get('source_ref', '')}",
            "detail": f"High value in pack {s.get('pack_id', '')}; consider workflow-dataset jobs run --id {s.get('source_ref', '')} --mode simulate",
            "ref": s.get("source_ref", ""),
        })
    for b in signals.get("recurring_blockers", [])[:3]:
        recs.append({
            "kind": "resolve_before_retry",
            "title": f"Resolve blocker: {b.get('cause_code', '')}",
            "detail": f"source_ref={b.get('source_ref', '')}; add approval or fix config then retry.",
            "ref": b.get("source_ref", ""),
        })
    return recs
