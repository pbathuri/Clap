"""
M42E–M42H: Candidate model report and lineage summary.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.candidate_model_studio.store import (
    load_candidate,
    load_slice,
    list_slices_for_candidate,
    list_candidates,
)
from workflow_dataset.candidate_model_studio.training_paths import get_path_descriptor


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_lineage_summary(
    candidate_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Lineage summary for a candidate: source, parents, created_by."""
    c = load_candidate(candidate_id, repo_root)
    if not c:
        return {"candidate_id": candidate_id, "found": False}
    out: dict[str, Any] = {
        "candidate_id": candidate_id,
        "found": True,
        "name": c.name,
        "status": c.status,
        "created_at_utc": c.created_at_utc,
        "lineage": None,
        "evidence_source_type": None,
        "evidence_source_id": None,
        "parent_candidate_ids": [],
    }
    if c.lineage:
        out["lineage"] = c.lineage.to_dict()
        out["evidence_source_type"] = c.lineage.evidence_source_type
        out["evidence_source_id"] = c.lineage.evidence_source_id
        out["parent_candidate_ids"] = list(c.lineage.parent_candidate_ids)
    return out


def build_candidate_report(
    candidate_id: str,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Full report for one candidate: model, slice(s), path descriptor, lineage, eligibility, rollback."""
    c = load_candidate(candidate_id, repo_root)
    if not c:
        return {"candidate_id": candidate_id, "found": False}
    slices = list_slices_for_candidate(candidate_id, repo_root)
    path_desc = get_path_descriptor(c.training_path_id) if c.training_path_id else None
    out: dict[str, Any] = {
        "candidate_id": c.candidate_id,
        "found": True,
        "name": c.name,
        "summary": c.summary,
        "status": c.status,
        "cohort_id": c.cohort_id,
        "evidence": c.evidence.to_dict(),
        "evidence_count": c.evidence.evidence_count,
        "dataset_slice_id": c.dataset_slice_id,
        "slices": [s.to_dict() for s in slices],
        "training_path_id": c.training_path_id,
        "training_path": path_desc.to_dict() if path_desc else None,
        "template_id": c.template_id,
        "safety_profile_id": c.safety_profile_id,
        "runtime_variant_id": c.runtime_variant_id,
        "lineage": build_lineage_summary(candidate_id, repo_root),
        "promotion_eligibility": c.promotion_eligibility.to_dict() if c.promotion_eligibility else None,
        "rollback_path": c.rollback_path.to_dict() if c.rollback_path else None,
        "boundary": c.boundary.to_dict() if c.boundary else None,
        "created_at_utc": c.created_at_utc,
        "updated_at_utc": c.updated_at_utc,
    }
    return out


def get_mission_control_candidate_studio_state(
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """State for mission control: top candidate, latest slice, quarantined, lineage summary, next eval step."""
    root = _root(repo_root)
    candidates = list_candidates(repo_root=root, limit=20)
    top_candidate = candidates[0].to_dict() if candidates else None
    quarantined = [c for c in candidates if c.status == "quarantined"]
    latest_slice = None
    slice_candidate_id = None
    for c in candidates:
        slices = list_slices_for_candidate(c.candidate_id, repo_root=root)
        if slices:
            latest_slice = slices[0].to_dict()
            slice_candidate_id = c.candidate_id
            break
    next_eval_step = None
    if candidates:
        c = candidates[0]
        path_desc = get_path_descriptor(c.training_path_id) if c.training_path_id else None
        if path_desc and path_desc.required_evaluation_before_promotion:
            next_eval_step = path_desc.required_evaluation_before_promotion[0]
    return {
        "top_candidate": top_candidate,
        "candidates_count": len(candidates),
        "latest_slice": latest_slice,
        "latest_slice_candidate_id": slice_candidate_id,
        "quarantined_count": len(quarantined),
        "quarantined_ids": [c.candidate_id for c in quarantined[:5]],
        "lineage_summary": build_lineage_summary(candidates[0].candidate_id, root) if candidates else None,
        "next_required_evaluation_step": next_eval_step,
    }
