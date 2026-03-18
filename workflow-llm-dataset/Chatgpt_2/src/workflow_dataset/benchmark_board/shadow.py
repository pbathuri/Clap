"""
M42L.1: Shadow-mode evaluation — candidate runs alongside production; compare without switching route.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.benchmark_board.store import list_shadow_runs


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_shadow_report(
    candidate_id: str,
    repo_root: Path | str | None = None,
    limit_runs: int = 100,
) -> dict[str, Any]:
    """
    Build shadow-mode report for a candidate: aggregate shadow runs (production vs candidate on same slice)
    into counts and averages; operator-facing summary.
    """
    root = _repo_root(repo_root)
    runs = list_shadow_runs(candidate_id=candidate_id, limit=limit_runs, repo_root=root)

    total = len(runs)
    match_count = sum(1 for r in runs if r.get("outcome") == "match")
    candidate_better = sum(1 for r in runs if r.get("outcome") == "candidate_better")
    production_better = sum(1 for r in runs if r.get("outcome") == "production_better")
    disagree = sum(1 for r in runs if r.get("outcome") == "disagree")
    other = total - match_count - candidate_better - production_better - disagree

    prod_scores = [r["production_score"] for r in runs if isinstance(r.get("production_score"), (int, float))]
    cand_scores = [r["candidate_score"] for r in runs if isinstance(r.get("candidate_score"), (int, float))]
    avg_production = sum(prod_scores) / len(prod_scores) if prod_scores else 0.0
    avg_candidate = sum(cand_scores) / len(cand_scores) if cand_scores else 0.0

    if total == 0:
        summary_text = f"No shadow runs for candidate {candidate_id}. Run shadow comparisons to evaluate before promotion."
    else:
        parts = [
            f"Shadow runs: {total} total.",
            f"Match: {match_count}, Candidate better: {candidate_better}, Production better: {production_better}.",
            f"Avg production score: {avg_production:.3f}, Avg candidate score: {avg_candidate:.3f}.",
        ]
        if production_better > candidate_better:
            parts.append("Recommendation: do not promote yet; production outperformed candidate in shadow.")
        elif candidate_better > production_better and production_better == 0:
            parts.append("Recommendation: candidate favorable in shadow; consider next track.")
        else:
            parts.append("Recommendation: review shadow outcomes before promotion.")
        summary_text = " ".join(parts)

    return {
        "candidate_id": candidate_id,
        "total_runs": total,
        "match_count": match_count,
        "candidate_better_count": candidate_better,
        "production_better_count": production_better,
        "disagree_count": disagree,
        "other_count": other,
        "avg_production_score": round(avg_production, 4),
        "avg_candidate_score": round(avg_candidate, 4),
        "operator_summary": summary_text,
        "recent_runs": runs[:10],
    }


def record_shadow_run(
    candidate_id: str,
    production_run_id: str,
    candidate_run_id: str,
    production_score: float,
    candidate_score: float,
    slice_id: str = "",
    repo_root: Path | str | None = None,
) -> None:
    """Record one shadow run (production vs candidate on same slice). Outcome derived from scores."""
    from workflow_dataset.benchmark_board.store import append_shadow_run
    from datetime import datetime, timezone
    if candidate_score > production_score:
        outcome = "candidate_better"
    elif production_score > candidate_score:
        outcome = "production_better"
    else:
        outcome = "match"
    at_iso = datetime.now(timezone.utc).isoformat()[:19] + "Z"
    append_shadow_run(
        candidate_id=candidate_id,
        production_run_id=production_run_id,
        candidate_run_id=candidate_run_id,
        slice_id=slice_id,
        production_score=production_score,
        candidate_score=candidate_score,
        outcome=outcome,
        at_iso=at_iso,
        repo_root=repo_root,
    )
