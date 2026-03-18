"""
M42E–M42H: Persist and list candidate models, dataset slices, lineage. data/local/candidate_model_studio/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.candidate_model_studio.models import (
    CandidateModel,
    DatasetSlice,
    StudioEvidenceBundle,
    ExperimentLineage,
    PromotionEligibility,
    RollbackPath,
    SupportedExperimentalBoundary,
)


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


STUDIO_DIR = "data/local/candidate_model_studio"
CANDIDATES_DIR = "candidates"
SLICES_DIR = "slices"


def _studio_root(repo_root: Path | str | None) -> Path:
    return _root(repo_root) / STUDIO_DIR


def _candidate_path(candidate_id: str, repo_root: Path | str | None) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in (candidate_id or "").strip())
    return _studio_root(repo_root) / CANDIDATES_DIR / f"{safe}.json"


def _slice_path(slice_id: str, repo_root: Path | str | None) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in (slice_id or "").strip())
    return _studio_root(repo_root) / SLICES_DIR / f"{safe}.json"


def _dict_to_evidence(d: dict[str, Any]) -> StudioEvidenceBundle:
    return StudioEvidenceBundle(
        evidence_ids=d.get("evidence_ids", []),
        correction_ids=d.get("correction_ids", []),
        adaptation_ids=d.get("adaptation_ids", []),
        cluster_ids=d.get("cluster_ids", []),
        session_ids=d.get("session_ids", []),
        summary=d.get("summary", ""),
        evidence_count=d.get("evidence_count", 0),
    )


def _dict_to_lineage(d: dict[str, Any]) -> ExperimentLineage:
    return ExperimentLineage(
        candidate_id=d.get("candidate_id", ""),
        parent_candidate_ids=d.get("parent_candidate_ids", []),
        evidence_source_type=d.get("evidence_source_type", ""),
        evidence_source_id=d.get("evidence_source_id", ""),
        created_at_utc=d.get("created_at_utc", ""),
        created_by=d.get("created_by", ""),
    )


def _dict_to_promotion(d: dict[str, Any]) -> PromotionEligibility:
    return PromotionEligibility(
        candidate_id=d.get("candidate_id", ""),
        eligible=d.get("eligible", False),
        required_evals_done=d.get("required_evals_done", []),
        required_evals_pending=d.get("required_evals_pending", []),
        council_review_id=d.get("council_review_id", ""),
        summary=d.get("summary", ""),
    )


def _dict_to_rollback(d: dict[str, Any]) -> RollbackPath:
    return RollbackPath(
        candidate_id=d.get("candidate_id", ""),
        rollback_target_id=d.get("rollback_target_id", ""),
        rollback_target_kind=d.get("rollback_target_kind", ""),
        notes=d.get("notes", ""),
    )


def _dict_to_boundary(d: dict[str, Any]) -> SupportedExperimentalBoundary:
    return SupportedExperimentalBoundary(
        candidate_id=d.get("candidate_id", ""),
        boundary=d.get("boundary", "experimental"),
        allowed_surface_ids=d.get("allowed_surface_ids", []),
        experimental_only_surface_ids=d.get("experimental_only_surface_ids", []),
        summary=d.get("summary", ""),
    )


def save_candidate(candidate: CandidateModel, repo_root: Path | str | None = None) -> Path:
    """Write candidate to candidates/<candidate_id>.json."""
    root = _studio_root(repo_root)
    (root / CANDIDATES_DIR).mkdir(parents=True, exist_ok=True)
    path = _candidate_path(candidate.candidate_id, repo_root)
    path.write_text(json.dumps(candidate.to_dict(), indent=2), encoding="utf-8")
    return path


def load_candidate(candidate_id: str, repo_root: Path | str | None = None) -> CandidateModel | None:
    """Load one candidate by id."""
    path = _candidate_path(candidate_id, repo_root)
    if not path.exists() or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        ev = data.get("evidence", {})
        lineage = data.get("lineage")
        prom = data.get("promotion_eligibility")
        roll = data.get("rollback_path")
        boundary = data.get("boundary")
        return CandidateModel(
            candidate_id=data.get("candidate_id", ""),
            name=data.get("name", ""),
            summary=data.get("summary", ""),
            status=data.get("status", "draft"),
            evidence=_dict_to_evidence(ev) if isinstance(ev, dict) else StudioEvidenceBundle(),
            dataset_slice_id=data.get("dataset_slice_id", ""),
            training_path_id=data.get("training_path_id", ""),
            runtime_variant_id=data.get("runtime_variant_id", ""),
            template_id=data.get("template_id", ""),
            safety_profile_id=data.get("safety_profile_id", ""),
            lineage=_dict_to_lineage(lineage) if isinstance(lineage, dict) else None,
            promotion_eligibility=_dict_to_promotion(prom) if isinstance(prom, dict) else None,
            rollback_path=_dict_to_rollback(roll) if isinstance(roll, dict) else None,
            boundary=_dict_to_boundary(boundary) if isinstance(boundary, dict) else None,
            cohort_id=data.get("cohort_id", ""),
            created_at_utc=data.get("created_at_utc", ""),
            updated_at_utc=data.get("updated_at_utc", ""),
            extra=data.get("extra", {}),
        )
    except Exception:
        return None


def list_candidates(
    repo_root: Path | str | None = None,
    status: str = "",
    cohort_id: str = "",
    limit: int = 50,
) -> list[CandidateModel]:
    """List candidate models newest first; optional filter by status and cohort_id."""
    root = _studio_root(repo_root) / CANDIDATES_DIR
    if not root.exists():
        return []
    out: list[CandidateModel] = []
    for path in sorted(root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not path.is_file() or path.suffix != ".json":
            continue
        c = load_candidate(path.stem, repo_root)
        if not c:
            continue
        if status and c.status != status:
            continue
        if cohort_id and c.cohort_id != cohort_id:
            continue
        out.append(c)
        if len(out) >= limit:
            break
    return out


def save_slice(slice_obj: DatasetSlice, repo_root: Path | str | None = None) -> Path:
    """Write dataset slice to slices/<slice_id>.json."""
    root = _studio_root(repo_root)
    (root / SLICES_DIR).mkdir(parents=True, exist_ok=True)
    path = _slice_path(slice_obj.slice_id, repo_root)
    path.write_text(json.dumps(slice_obj.to_dict(), indent=2), encoding="utf-8")
    return path


def load_slice(slice_id: str, repo_root: Path | str | None = None) -> DatasetSlice | None:
    """Load one dataset slice by id."""
    path = _slice_path(slice_id, repo_root)
    if not path.exists() or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return DatasetSlice(
            slice_id=data.get("slice_id", ""),
            candidate_id=data.get("candidate_id", ""),
            name=data.get("name", ""),
            provenance_source=data.get("provenance_source", ""),
            provenance_refs=data.get("provenance_refs", []),
            included_evidence_ids=data.get("included_evidence_ids", []),
            included_correction_ids=data.get("included_correction_ids", []),
            exclusion_rule_summary=data.get("exclusion_rule_summary", ""),
            excluded_ids=data.get("excluded_ids", []),
            created_at_utc=data.get("created_at_utc", ""),
            row_count=data.get("row_count", 0),
            memory_slice_id=data.get("memory_slice_id", ""),
        )
    except Exception:
        return None


def list_slices_for_candidate(
    candidate_id: str,
    repo_root: Path | str | None = None,
) -> list[DatasetSlice]:
    """List all slices for a candidate (by candidate_id in slice)."""
    root = _studio_root(repo_root) / SLICES_DIR
    if not root.exists():
        return []
    out: list[DatasetSlice] = []
    for path in root.iterdir():
        if not path.is_file() or path.suffix != ".json":
            continue
        s = load_slice(path.stem, repo_root)
        if s and s.candidate_id == candidate_id:
            out.append(s)
    return out
