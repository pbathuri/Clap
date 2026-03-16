"""
M23M: Correction-to-eval advisory bridge. Surface 'review trust' / 'review benchmark' from repeated corrections.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from collections import Counter

from workflow_dataset.corrections.store import list_corrections


def advisory_review_for_corrections(
    repo_root: Path | str | None = None,
    limit: int = 100,
    min_count: int = 2,
) -> list[dict[str, Any]]:
    """
    Return advisory list: jobs/routines with repeated corrections that suggest trust or benchmark review.
    Does NOT auto-downgrade or auto-upgrade trust.
    """
    corrections = list_corrections(limit=limit, repo_root=repo_root)
    by_ref: Counter[str] = Counter()
    categories_by_ref: dict[str, set[str]] = {}
    for c in corrections:
        ref = c.source_reference_id or ""
        if not ref:
            continue
        by_ref[ref] += 1
        if ref not in categories_by_ref:
            categories_by_ref[ref] = set()
        categories_by_ref[ref].add(c.correction_category)

    advisories: list[dict[str, Any]] = []
    for ref, count in by_ref.items():
        if count < min_count:
            continue
        cats = categories_by_ref.get(ref, set())
        recommendation = None
        reason = f"Repeated corrections ({count}) for {ref}"
        if "trust_level_too_high" in cats or "trust_level_too_low" in cats:
            recommendation = "review_trust"
            reason = f"Trust-level corrections ({count}) for {ref}; review job trust_level and trust_notes."
        elif "bad_job_parameter_default" in cats or "output_style_correction" in cats or "artifact_content_correction" in cats:
            recommendation = "review_benchmark"
            reason = f"Output/param corrections ({count}) for {ref}; consider benchmark or template review."
        elif "context_trigger_false_positive" in cats or "context_trigger_false_negative" in cats:
            recommendation = "review_trigger_policy"
            reason = f"Trigger corrections ({count}) for {ref}; consider trigger policy tuning."
        else:
            recommendation = "review_recommended"
        advisories.append({
            "job_or_routine_id": ref,
            "correction_count": count,
            "recommendation": recommendation,
            "reason": reason,
        })
    return advisories
