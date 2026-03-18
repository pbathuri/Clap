"""
M42I–M42L: Baseline vs candidate comparison — uses eval compare_runs; produces comparison result for scorecard.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workflow_dataset.eval.board import compare_runs, get_run, resolve_run_id

def _run_total_score(manifest: dict[str, Any]) -> float:
    cases = manifest.get("cases") or []
    if not cases:
        return 0.0
    totals: list[float] = []
    for c in cases:
        scores = (c.get("scores") or {}).get("artifacts") or {}
        if not scores:
            totals.append(0.0)
            continue
        vals: list[float] = []
        for art_s in scores.values():
            if isinstance(art_s, dict):
                vals.extend(v for v in art_s.values() if isinstance(v, (int, float)))
        totals.append(sum(vals) / len(vals) if vals else 0.0)
    return sum(totals) / len(totals) if totals else 0.0
from workflow_dataset.utils.hashes import stable_id


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def run_baseline_vs_candidate(
    baseline_id: str,
    candidate_id: str,
    slice_ids: list[str] | None = None,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Compare baseline run vs candidate run. baseline_id and candidate_id can be run_id or alias (latest, previous).
    Uses eval compare_runs; returns comparison dict with run_a, run_b, regressions, improvements, recommendation.
    """
    root = _repo_root(repo_root)
    base_run = resolve_run_id(baseline_id, root) or baseline_id
    cand_run = resolve_run_id(candidate_id, root) or candidate_id

    if get_run(base_run, root) is None:
        return {"error": f"Baseline run not found: {baseline_id}", "baseline_id": baseline_id, "candidate_id": candidate_id}
    if get_run(cand_run, root) is None:
        return {"error": f"Candidate run not found: {candidate_id}", "baseline_id": baseline_id, "candidate_id": candidate_id}

    comparison = compare_runs(base_run, cand_run, root)
    if comparison.get("error"):
        return comparison

    ma = get_run(base_run, root)
    mb = get_run(cand_run, root)
    if ma:
        comparison["run_a_score"] = _run_total_score(ma)
    if mb:
        comparison["run_b_score"] = _run_total_score(mb)
    comparison["baseline_id"] = baseline_id
    comparison["candidate_id"] = candidate_id
    comparison["baseline_resolved_run_id"] = base_run
    comparison["candidate_resolved_run_id"] = cand_run
    comparison["slice_ids"] = slice_ids or []
    comparison["at_iso"] = datetime.now(timezone.utc).isoformat()[:19] + "Z"
    return comparison
