"""
M42I–M42L: Benchmark board report — next candidate awaiting decision, latest promoted, quarantined, rollback-ready, next action.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.benchmark_board.store import (
    list_scorecards,
    get_quarantined,
    get_latest_promoted,
    list_promotion_history,
    list_rollback_history,
)
from workflow_dataset.benchmark_board.shadow import build_shadow_report
from workflow_dataset.benchmark_board.tracks import scope_to_track_id
from workflow_dataset.eval.board import list_runs


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_benchmark_board_report(repo_root: Path | str | None = None) -> dict[str, Any]:
    """
    Build report: top_candidate_awaiting_decision, latest_promoted_id, latest_promoted_scope,
    quarantined_count, rollback_ready_promoted_id (latest promoted that has a rollback available),
    next_benchmark_review_action.
    """
    root = _repo_root(repo_root)
    scorecards = list_scorecards(limit=30, repo_root=root)
    quarantined = get_quarantined(repo_root=root)
    latest_id, latest_scope = get_latest_promoted(repo_root=root)
    promos = list_promotion_history(limit=10, repo_root=root)
    rollbacks = list_rollback_history(limit=10, repo_root=root)

    # Top candidate awaiting decision: most recent scorecard whose candidate is not yet promoted/quarantined
    awaiting_id = ""
    for sc in scorecards:
        cid = sc.get("candidate_id", "")
        if cid and cid not in quarantined and cid != latest_id:
            rec = sc.get("recommendation", "")
            if rec in ("promote", "hold", "refine", "revert"):
                awaiting_id = cid
                break

    # If we have runs but no scorecard, "next" could be run a compare
    runs = list_runs(limit=5, root=root)
    next_action = "workflow-dataset benchmarks compare --baseline previous --candidate latest"
    if awaiting_id:
        next_action = f"workflow-dataset models promote --id {awaiting_id}  # or quarantine/rollback"
    elif not scorecards and runs:
        next_action = "workflow-dataset benchmarks compare --baseline previous --candidate latest"
    elif not runs:
        next_action = "workflow-dataset eval run-suite <suite>  # then benchmarks compare"

    # Rollback-ready: latest promoted has rollback history entry or prior_id available
    rollback_ready_id = ""
    if latest_id and latest_scope in ("production_safe", "limited_cohort"):
        if rollbacks:
            rollback_ready_id = latest_id

    return {
        "top_candidate_awaiting_decision": awaiting_id,
        "latest_promoted_id": latest_id,
        "latest_promoted_scope": latest_scope,
        "quarantined_count": len(quarantined),
        "quarantined_ids": quarantined[:10],
        "rollback_ready_promoted_id": rollback_ready_id,
        "scorecards_count": len(scorecards),
        "next_benchmark_review_action": next_action,
    }


def build_production_vs_candidate_comparison(
    candidate_id: str | None = None,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Operator-facing comparison: current production route vs candidate route.
    Includes latest scorecard for candidate, shadow report if any, and a short operator summary.
    """
    root = _repo_root(repo_root)
    prod_id, prod_scope = get_latest_promoted(repo_root=root)
    scorecards = list_scorecards(limit=50, repo_root=root)
    quarantined = get_quarantined(repo_root=root)

    # Resolve candidate: use provided or top awaiting
    cid = candidate_id
    if not cid:
        for sc in scorecards:
            cid = sc.get("candidate_id", "")
            if cid and cid not in quarantined and cid != prod_id:
                break
        if not cid:
            cid = ""

    scorecard_summary: dict[str, Any] = {}
    for sc in scorecards:
        if sc.get("candidate_id") == cid:
            scorecard_summary = {
                "scorecard_id": sc.get("scorecard_id"),
                "recommendation": sc.get("recommendation"),
                "thresholds_passed": sc.get("thresholds_passed"),
                "regressions": sc.get("regressions", []),
                "improvements": sc.get("improvements", []),
            }
            break

    shadow_summary: dict[str, Any] = {}
    if cid:
        shadow_summary = build_shadow_report(cid, repo_root=root)

    prod_track = scope_to_track_id(prod_scope) if prod_scope else ""
    operator_summary_parts = [
        f"Production route: {prod_id or '(none)'}  scope={prod_scope or '—'}  track={prod_track or '—'}.",
    ]
    if cid:
        operator_summary_parts.append(
            f"Candidate: {cid}; scorecard recommendation={scorecard_summary.get('recommendation', '—')}; "
            f"shadow runs={shadow_summary.get('total_runs', 0)}."
        )
        if shadow_summary.get("operator_summary"):
            operator_summary_parts.append(shadow_summary["operator_summary"])
    else:
        operator_summary_parts.append("No candidate selected for comparison.")

    return {
        "current_production_route_id": prod_id,
        "current_production_scope": prod_scope,
        "current_production_track_id": prod_track,
        "candidate_id": cid,
        "scorecard_summary": scorecard_summary,
        "shadow_summary": shadow_summary,
        "operator_summary_text": " ".join(operator_summary_parts),
    }


def build_memory_compare_report(repo_root: Path | str | None = None) -> dict[str, Any]:
    """M43: Report of scorecards that used memory-backed slices and list of available memory slices for benchmarks."""
    root = _repo_root(repo_root)
    scorecards = list_scorecards(limit=50, repo_root=root)
    with_memory: list[dict[str, Any]] = []
    for sc in scorecards:
        mem_ids = sc.get("memory_slice_ids") or []
        if mem_ids:
            with_memory.append({
                "scorecard_id": sc.get("scorecard_id"),
                "baseline_id": sc.get("baseline_id"),
                "candidate_id": sc.get("candidate_id"),
                "memory_slice_ids": mem_ids,
                "recommendation": sc.get("recommendation"),
            })
    try:
        from workflow_dataset.memory_substrate.slices import list_memory_slices
        memory_slices = [s.to_dict() for s in list_memory_slices(repo_root=root, limit=20)]
    except Exception:
        memory_slices = []
    return {
        "scorecards_with_memory_slices": with_memory,
        "scorecards_with_memory_count": len(with_memory),
        "available_memory_slices": memory_slices,
        "usage_note": "Use memory_slice_ids in compare result or when building scorecard to tag memory-aware comparisons.",
    }
