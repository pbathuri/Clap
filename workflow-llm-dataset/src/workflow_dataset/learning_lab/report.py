"""
M41D: Learning lab reports — experiment report, comparison output.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.learning_lab.store import get_experiment, list_experiments, get_active_experiment_id
from workflow_dataset.learning_lab.experiments import compare_before_after


def build_experiment_report(
    experiment_id: str,
    repo_root: Any = None,
) -> dict[str, Any]:
    """Build full report for one experiment (for CLI report --id)."""
    exp = get_experiment(experiment_id, repo_root)
    if not exp:
        return {"error": f"Experiment not found: {experiment_id}"}
    comp = compare_before_after(experiment_id, repo_root=repo_root)
    return {
        "experiment_id": exp.experiment_id,
        "source_type": exp.source_type,
        "source_ref": exp.source_ref,
        "label": exp.label,
        "created_at_utc": exp.created_at_utc,
        "status": exp.status,
        "status_reason": exp.status_reason,
        "comparison_summary": comp.get("comparison_summary") or exp.comparison_summary,
        "evidence_summary": exp.evidence_bundle.summary if exp.evidence_bundle else "",
        "slice_description": exp.local_slice.description if exp.local_slice else "",
        "rollbackable_count": len(exp.rollbackable_changes),
        "profile_id": exp.profile_id or "",
        "template_id": exp.template_id or "",
    }


def build_comparison_output(
    experiment_id: str,
    run_before: str | None = None,
    run_after: str | None = None,
    repo_root: Any = None,
) -> dict[str, Any]:
    """Build before/after comparison output (for CLI compare --id)."""
    return compare_before_after(experiment_id, run_before=run_before, run_after=run_after, repo_root=repo_root)
