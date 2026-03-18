"""
M42E–M42H: Create candidate model from evidence source (issue cluster, adaptation, correction set, etc.).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.candidate_model_studio.models import (
    CandidateModel,
    ExperimentLineage,
    SupportedExperimentalBoundary,
    StudioEvidenceBundle,
    BOUNDARY_EXPERIMENTAL,
    CANDIDATE_STATUS_DRAFT,
)
from workflow_dataset.candidate_model_studio.dataset_slice import (
    build_slice_from_issue_cluster,
    build_slice_from_corrections,
    build_slice_from_accepted_adaptations,
    build_slice_from_vertical_failures,
    build_slice_from_council_disagreement,
    build_slice_production_safe_exemplars,
    build_studio_evidence_bundle,
)
from workflow_dataset.candidate_model_studio.store import save_candidate, save_slice
from workflow_dataset.candidate_model_studio.training_paths import PATH_PROMPT_CONFIG_ONLY, get_path_descriptor
from workflow_dataset.candidate_model_studio.templates import get_template

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:12]


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def create_candidate_from_issue_cluster(
    cluster_id: str,
    cohort_id: str = "",
    name: str = "",
    training_path_id: str = PATH_PROMPT_CONFIG_ONLY,
    template_id: str = "",
    safety_profile_id: str = "",
    repo_root: Path | str | None = None,
) -> CandidateModel | None:
    """Create a candidate model from an issue cluster. Slice = cluster's issues/evidence."""
    root = _root(repo_root)
    t = get_template(template_id) if template_id else None
    if t:
        training_path_id = t.default_training_path_id or training_path_id
        if not safety_profile_id:
            safety_profile_id = t.default_safety_profile_id or ""
    candidate_id = stable_id("cand", "cluster", cluster_id, utc_now_iso(), prefix="cand_")
    slice_obj = build_slice_from_issue_cluster(
        candidate_id=candidate_id,
        cluster_id=cluster_id,
        cohort_id=cohort_id,
        name=name,
        repo_root=root,
    )
    save_slice(slice_obj, repo_root)
    evidence = build_studio_evidence_bundle(cluster_ids=[cluster_id])
    lineage = ExperimentLineage(
        candidate_id=candidate_id,
        evidence_source_type="issue_cluster",
        evidence_source_id=cluster_id,
        created_at_utc=utc_now_iso(),
        created_by="cli",
    )
    boundary = SupportedExperimentalBoundary(
        candidate_id=candidate_id,
        boundary=t.default_boundary if t else BOUNDARY_EXPERIMENTAL,
        summary="Created from issue cluster; experimental until promoted",
    )
    candidate = CandidateModel(
        candidate_id=candidate_id,
        name=name or f"Candidate from cluster {cluster_id}",
        summary=f"From issue cluster {cluster_id}; slice row_count={slice_obj.row_count}",
        status=CANDIDATE_STATUS_DRAFT,
        evidence=evidence,
        dataset_slice_id=slice_obj.slice_id,
        training_path_id=training_path_id,
        template_id=template_id,
        safety_profile_id=safety_profile_id,
        lineage=lineage,
        boundary=boundary,
        cohort_id=cohort_id,
        created_at_utc=utc_now_iso(),
        updated_at_utc=utc_now_iso(),
    )
    save_candidate(candidate, repo_root)
    return candidate


def create_candidate_from_adaptation(
    adaptation_id: str,
    cohort_id: str = "",
    name: str = "",
    training_path_id: str = PATH_PROMPT_CONFIG_ONLY,
    template_id: str = "",
    safety_profile_id: str = "",
    repo_root: Path | str | None = None,
) -> CandidateModel | None:
    """Create a candidate model from one accepted adaptation (evidence from its bundle)."""
    root = _root(repo_root)
    t = get_template(template_id) if template_id else None
    if t:
        training_path_id = t.default_training_path_id or training_path_id
        if not safety_profile_id:
            safety_profile_id = t.default_safety_profile_id or ""
    try:
        from workflow_dataset.safe_adaptation.store import load_candidate as load_adapt
        adapt = load_adapt(adaptation_id, repo_root=root)
        if not adapt:
            return None
        ev = adapt.evidence
    except Exception:
        return None
    candidate_id = stable_id("cand", "adapt", adaptation_id, utc_now_iso(), prefix="cand_")
    slice_obj = build_slice_from_accepted_adaptations(
        candidate_id=candidate_id,
        adaptation_ids=[adaptation_id],
        name=name,
        repo_root=root,
    )
    save_slice(slice_obj, repo_root)
    evidence = build_studio_evidence_bundle(
        evidence_ids=list(ev.evidence_ids),
        correction_ids=list(ev.correction_ids),
        adaptation_ids=[adaptation_id],
        session_ids=list(ev.session_ids),
    )
    lineage = ExperimentLineage(
        candidate_id=candidate_id,
        evidence_source_type="adaptation",
        evidence_source_id=adaptation_id,
        created_at_utc=utc_now_iso(),
        created_by="cli",
    )
    boundary = SupportedExperimentalBoundary(
        candidate_id=candidate_id,
        boundary=t.default_boundary if t else BOUNDARY_EXPERIMENTAL,
        summary="From adaptation; experimental until promoted",
    )
    candidate = CandidateModel(
        candidate_id=candidate_id,
        name=name or f"Candidate from adaptation {adaptation_id}",
        summary=f"From adaptation {adaptation_id}; evidence_count={evidence.evidence_count}",
        status=CANDIDATE_STATUS_DRAFT,
        evidence=evidence,
        dataset_slice_id=slice_obj.slice_id,
        training_path_id=training_path_id,
        template_id=template_id,
        safety_profile_id=safety_profile_id,
        lineage=lineage,
        boundary=boundary,
        cohort_id=cohort_id or getattr(adapt, "cohort_id", ""),
        created_at_utc=utc_now_iso(),
        updated_at_utc=utc_now_iso(),
    )
    save_candidate(candidate, repo_root)
    return candidate


def create_candidate_from_corrections(
    correction_ids: list[str],
    cohort_id: str = "",
    name: str = "",
    training_path_id: str = PATH_PROMPT_CONFIG_ONLY,
    template_id: str = "",
    safety_profile_id: str = "",
    exclude_ids: list[str] | None = None,
    repo_root: Path | str | None = None,
) -> CandidateModel:
    """Create a candidate model from a set of correction IDs."""
    root = _root(repo_root)
    t = get_template(template_id) if template_id else None
    if t:
        training_path_id = t.default_training_path_id or training_path_id
        if not safety_profile_id:
            safety_profile_id = t.default_safety_profile_id or ""
    candidate_id = stable_id("cand", "corrections", utc_now_iso(), prefix="cand_")
    slice_obj = build_slice_from_corrections(
        candidate_id=candidate_id,
        correction_ids=correction_ids,
        name=name,
        exclude_ids=exclude_ids,
        repo_root=root,
    )
    save_slice(slice_obj, repo_root)
    evidence = build_studio_evidence_bundle(correction_ids=slice_obj.included_correction_ids)
    lineage = ExperimentLineage(
        candidate_id=candidate_id,
        evidence_source_type="correction_set",
        evidence_source_id=",".join(slice_obj.provenance_refs[:5]),
        created_at_utc=utc_now_iso(),
        created_by="cli",
    )
    boundary = SupportedExperimentalBoundary(
        candidate_id=candidate_id,
        boundary=t.default_boundary if t else BOUNDARY_EXPERIMENTAL,
        summary="From corrections; experimental until promoted",
    )
    candidate = CandidateModel(
        candidate_id=candidate_id,
        name=name or f"Candidate from {len(slice_obj.included_correction_ids)} corrections",
        summary=f"From corrections; row_count={slice_obj.row_count}",
        status=CANDIDATE_STATUS_DRAFT,
        evidence=evidence,
        dataset_slice_id=slice_obj.slice_id,
        training_path_id=training_path_id,
        template_id=template_id,
        safety_profile_id=safety_profile_id,
        lineage=lineage,
        boundary=boundary,
        cohort_id=cohort_id,
        created_at_utc=utc_now_iso(),
        updated_at_utc=utc_now_iso(),
    )
    save_candidate(candidate, repo_root)
    return candidate


def create_candidate(
    from_source: str,
    cohort_id: str = "",
    name: str = "",
    training_path_id: str = PATH_PROMPT_CONFIG_ONLY,
    template_id: str = "",
    safety_profile_id: str = "",
    repo_root: Path | str | None = None,
) -> CandidateModel | None:
    """
    Create a candidate from a source identifier.
    from_source: issue_cluster_<id>, adaptation_<id>, or comma-separated correction ids (correction_set:<id1>,<id2>).
    template_id: optional template (evaluator, vertical_specialist, routing, calmness) sets default path/boundary/safety.
    """
    root = _root(repo_root)
    if from_source.startswith("issue_cluster_"):
        cluster_id = from_source.replace("issue_cluster_", "", 1).strip()
        return create_candidate_from_issue_cluster(
            cluster_id=cluster_id,
            cohort_id=cohort_id,
            name=name,
            training_path_id=training_path_id,
            template_id=template_id,
            safety_profile_id=safety_profile_id,
            repo_root=root,
        )
    if from_source.startswith("adaptation_"):
        adaptation_id = from_source.replace("adaptation_", "", 1).strip()
        return create_candidate_from_adaptation(
            adaptation_id=adaptation_id,
            cohort_id=cohort_id,
            name=name,
            training_path_id=training_path_id,
            template_id=template_id,
            safety_profile_id=safety_profile_id,
            repo_root=root,
        )
    if from_source.startswith("correction_set:"):
        ids_str = from_source.split(":", 1)[-1].strip()
        correction_ids = [x.strip() for x in ids_str.split(",") if x.strip()]
        return create_candidate_from_corrections(
            correction_ids=correction_ids,
            cohort_id=cohort_id,
            name=name,
            training_path_id=training_path_id,
            template_id=template_id,
            safety_profile_id=safety_profile_id,
            repo_root=root,
        )
    # Allow raw cluster_xxx as shorthand
    if from_source.startswith("cluster_"):
        return create_candidate_from_issue_cluster(
            cluster_id=from_source,
            cohort_id=cohort_id,
            name=name,
            training_path_id=training_path_id,
            template_id=template_id,
            safety_profile_id=safety_profile_id,
            repo_root=root,
        )
    return None
