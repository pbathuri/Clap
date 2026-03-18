"""
M22A / M23W: Incubator promotion gates — evaluate candidate and produce recommendation. Local-only; no side effects beyond report.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.incubator.registry import get_candidate, _incubator_root


def evaluate_gates(candidate_id: str, root: Path | str | None = None) -> dict[str, Any]:
    """
    Run promotion gates for a candidate. Returns dict with gates_passed, gates_total, recommendation, error (if any).
    Does not modify candidate unless caller attaches result via update_candidate.
    """
    c = get_candidate(candidate_id, root)
    if not c:
        return {"error": f"Candidate not found: {candidate_id}", "gates_passed": 0, "gates_total": 0, "recommendation": "reject"}
    # Minimal gates: stage and evidence presence
    gates_total = 2
    gates_passed = 0
    if c.get("stage") in ("benchmarked", "cohort_tested", "promoted"):
        gates_passed += 1
    if c.get("evidence_refs"):
        gates_passed += 1
    if gates_passed >= 2:
        recommendation = "promote"
    elif gates_passed >= 1:
        recommendation = "hold"
    else:
        recommendation = "reject"
    return {
        "gates_passed": gates_passed,
        "gates_total": gates_total,
        "recommendation": recommendation,
        "stage": c.get("stage"),
        "evidence_count": len(c.get("evidence_refs", [])),
    }


def promotion_report(candidate_id: str, result: dict[str, Any], root: Path | str | None = None) -> str:
    """Format a one-block promotion report for console."""
    err = result.get("error")
    if err:
        return f"Candidate: {candidate_id}\n  Error: {err}"
    gp = result.get("gates_passed", 0)
    gt = result.get("gates_total", 0)
    rec = result.get("recommendation", "reject")
    lines = [
        f"Candidate: {candidate_id}",
        f"  Gates: {gp} / {gt} passed",
        f"  Recommendation: {rec}",
    ]
    return "\n".join(lines)
