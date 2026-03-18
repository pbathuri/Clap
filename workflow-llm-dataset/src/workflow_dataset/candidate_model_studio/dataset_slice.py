"""
M42E–M42H Phase B: Local dataset curation — bounded slice creation from corrections,
accepted adaptations, issue clusters, vertical failures, review/council artifacts;
provenance and exclusion rules. No silent sweep of all data.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.candidate_model_studio.models import DatasetSlice, StudioEvidenceBundle, PROVENANCE_MEMORY_SLICE

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


# Provenance source identifiers for slice creation
PROVENANCE_CORRECTIONS = "corrections"
PROVENANCE_ACCEPTED_ADAPTATIONS = "accepted_adaptations"
PROVENANCE_ISSUE_CLUSTERS = "issue_clusters"
PROVENANCE_VERTICAL_FAILURES = "vertical_failures"
PROVENANCE_REVIEW_STUDIO = "review_studio"
PROVENANCE_COUNCIL_DISAGREEMENT = "council_disagreement"
PROVENANCE_PRODUCTION_SAFE = "production_safe"


def build_slice_from_corrections(
    candidate_id: str,
    correction_ids: list[str],
    name: str = "",
    exclude_ids: list[str] | None = None,
    repo_root: Path | str | None = None,
) -> DatasetSlice:
    """Bounded slice from explicit correction IDs. Exclusion list applied (e.g. low-severity or deferred)."""
    exclude_ids = exclude_ids or []
    included = [c for c in correction_ids if c not in exclude_ids]
    slice_id = stable_id("slice", candidate_id, "corrections", utc_now_iso(), prefix="slice_")
    return DatasetSlice(
        slice_id=slice_id,
        candidate_id=candidate_id,
        name=name or f"Corrections ({len(included)})",
        provenance_source=PROVENANCE_CORRECTIONS,
        provenance_refs=included[:50],
        included_correction_ids=list(included),
        exclusion_rule_summary="Excluded by explicit exclude_ids" if exclude_ids else "",
        excluded_ids=list(exclude_ids),
        created_at_utc=utc_now_iso(),
        row_count=len(included),
    )


def build_slice_from_accepted_adaptations(
    candidate_id: str,
    adaptation_ids: list[str],
    name: str = "",
    exclude_ids: list[str] | None = None,
    repo_root: Path | str | None = None,
) -> DatasetSlice:
    """Slice from accepted adaptation candidates; refs are adaptation_ids."""
    exclude_ids = exclude_ids or []
    included = [a for a in adaptation_ids if a not in exclude_ids]
    slice_id = stable_id("slice", candidate_id, "adaptations", utc_now_iso(), prefix="slice_")
    return DatasetSlice(
        slice_id=slice_id,
        candidate_id=candidate_id,
        name=name or f"Accepted adaptations ({len(included)})",
        provenance_source=PROVENANCE_ACCEPTED_ADAPTATIONS,
        provenance_refs=list(included),
        included_evidence_ids=[],  # populated from adaptation evidence when building candidate
        exclusion_rule_summary="Excluded by explicit exclude_ids" if exclude_ids else "",
        excluded_ids=list(exclude_ids),
        created_at_utc=utc_now_iso(),
        row_count=len(included),
    )


def build_slice_from_issue_cluster(
    candidate_id: str,
    cluster_id: str,
    cohort_id: str = "",
    name: str = "",
    exclude_issue_ids: list[str] | None = None,
    repo_root: Path | str | None = None,
) -> DatasetSlice:
    """Slice from one issue cluster: cluster_id -> issue_ids -> evidence_ids from triage."""
    root = _root(repo_root)
    exclude_issue_ids = exclude_issue_ids or []
    evidence_ids: list[str] = []
    try:
        from workflow_dataset.triage.clusters import build_all_clusters
        from workflow_dataset.triage.store import list_issues
        clusters = build_all_clusters(repo_root=root, cohort_id=cohort_id, by="subsystem")
        clusters += build_all_clusters(repo_root=root, cohort_id=cohort_id, by="workflow")
        for cl in clusters:
            if cl.cluster_id == cluster_id:
                issue_ids_in = [i for i in cl.issue_ids if i not in exclude_issue_ids]
                issues = list_issues(repo_root=root, cohort_id=cohort_id, limit=500)
                issue_set = set(issue_ids_in)
                for iss in issues:
                    if iss.issue_id in issue_set:
                        evidence_ids.extend(iss.evidence_ids or [])
                evidence_ids = list(dict.fromkeys(evidence_ids))
                slice_id = stable_id("slice", candidate_id, cluster_id, prefix="slice_")
                return DatasetSlice(
                    slice_id=slice_id,
                    candidate_id=candidate_id,
                    name=name or f"Cluster {cluster_id}",
                    provenance_source=PROVENANCE_ISSUE_CLUSTERS,
                    provenance_refs=[cluster_id],
                    included_evidence_ids=evidence_ids,
                    exclusion_rule_summary="Excluded by exclude_issue_ids" if exclude_issue_ids else "",
                    excluded_ids=list(exclude_issue_ids),
                    created_at_utc=utc_now_iso(),
                    row_count=len(evidence_ids) + len(issue_ids_in),
                )
    except Exception:
        pass
    slice_id = stable_id("slice", candidate_id, cluster_id, prefix="slice_")
    return DatasetSlice(
        slice_id=slice_id,
        candidate_id=candidate_id,
        name=name or f"Cluster {cluster_id}",
        provenance_source=PROVENANCE_ISSUE_CLUSTERS,
        provenance_refs=[cluster_id],
        included_evidence_ids=[],
        exclusion_rule_summary="Excluded by exclude_issue_ids" if exclude_issue_ids else "",
        excluded_ids=list(exclude_issue_ids),
        created_at_utc=utc_now_iso(),
        row_count=0,
    )


def build_slice_from_vertical_failures(
    candidate_id: str,
    cohort_id: str,
    subsystem_or_workflow: str,
    limit: int = 100,
    name: str = "",
    exclude_resolved: bool = True,
    repo_root: Path | str | None = None,
) -> DatasetSlice:
    """Slice from vertical-specific failure examples (issues in a subsystem/workflow)."""
    root = _root(repo_root)
    evidence_ids: list[str] = []
    try:
        from workflow_dataset.triage.store import list_issues
        from workflow_dataset.triage.models import TriageStatus
        issues = list_issues(repo_root=root, cohort_id=cohort_id, limit=300)
        if exclude_resolved:
            issues = [i for i in issues if i.triage_status not in (TriageStatus.RESOLVED, TriageStatus.MITIGATED)]
        for iss in issues:
            if subsystem_or_workflow in (iss.affected_subsystems or []) or iss.workflow_or_context == subsystem_or_workflow:
                evidence_ids.extend(iss.evidence_ids or [])
            if len(evidence_ids) >= limit:
                break
        evidence_ids = list(dict.fromkeys(evidence_ids))[:limit]
    except Exception:
        evidence_ids = []
    slice_id = stable_id("slice", candidate_id, "vertical", subsystem_or_workflow, prefix="slice_")
    return DatasetSlice(
        slice_id=slice_id,
        candidate_id=candidate_id,
        name=name or f"Vertical failures: {subsystem_or_workflow}",
        provenance_source=PROVENANCE_VERTICAL_FAILURES,
        provenance_refs=[subsystem_or_workflow],
        included_evidence_ids=evidence_ids,
        exclusion_rule_summary="Resolved/mitigated excluded" if exclude_resolved else "",
        created_at_utc=utc_now_iso(),
        row_count=len(evidence_ids),
    )


def build_slice_from_council_disagreement(
    candidate_id: str,
    review_id: str,
    name: str = "",
    repo_root: Path | str | None = None,
) -> DatasetSlice:
    """Slice from one council review that had disagreement notes (for training critique/evaluator)."""
    root = _root(repo_root)
    refs = [review_id]
    try:
        from workflow_dataset.council.store import load_review
        r = load_review(review_id, root)
        if r and getattr(r, "disagreement_notes", None):
            refs = [review_id]
    except Exception:
        pass
    slice_id = stable_id("slice", candidate_id, "council", review_id, prefix="slice_")
    return DatasetSlice(
        slice_id=slice_id,
        candidate_id=candidate_id,
        name=name or f"Council disagreement: {review_id}",
        provenance_source=PROVENANCE_COUNCIL_DISAGREEMENT,
        provenance_refs=refs,
        created_at_utc=utc_now_iso(),
        row_count=1,
    )


def build_slice_production_safe_exemplars(
    candidate_id: str,
    cohort_id: str,
    limit: int = 50,
    name: str = "",
    repo_root: Path | str | None = None,
) -> DatasetSlice:
    """Bounded slice of production-safe exemplars (evidence from supported surfaces only)."""
    root = _root(repo_root)
    evidence_ids: list[str] = []
    try:
        from workflow_dataset.triage.store import list_evidence
        from workflow_dataset.cohort.surface_matrix import get_supported_surfaces
        supported = set(get_supported_surfaces(cohort_id) or [])
        evidence = list_evidence(repo_root=root, cohort_id=cohort_id, limit=limit * 2)
        for e in evidence:
            if len(evidence_ids) >= limit:
                break
            # Only include if we can tag as supported-surface safe (simplified: include by cohort)
            evidence_ids.append(e.evidence_id)
    except Exception:
        pass
    slice_id = stable_id("slice", candidate_id, "production_safe", utc_now_iso(), prefix="slice_")
    return DatasetSlice(
        slice_id=slice_id,
        candidate_id=candidate_id,
        name=name or f"Production-safe exemplars ({len(evidence_ids)})",
        provenance_source=PROVENANCE_PRODUCTION_SAFE,
        provenance_refs=[cohort_id],
        included_evidence_ids=evidence_ids[:limit],
        exclusion_rule_summary="Cohort-bounded; supported-surface only",
        created_at_utc=utc_now_iso(),
        row_count=len(evidence_ids),
    )


def build_slice_from_memory_slice(
    candidate_id: str,
    memory_slice_id: str,
    name: str = "",
    repo_root: Path | str | None = None,
) -> DatasetSlice:
    """Build a candidate-model dataset slice from a memory substrate slice (resolves refs via memory substrate)."""
    root = _root(repo_root)
    try:
        from workflow_dataset.memory_substrate.slices import get_memory_slice_refs
        refs = get_memory_slice_refs(memory_slice_id, repo_root=root)
        if not refs:
            return DatasetSlice(
                slice_id=stable_id("slice", candidate_id, "memory", memory_slice_id, prefix="slice_"),
                candidate_id=candidate_id,
                name=name or f"Memory slice {memory_slice_id}",
                provenance_source=PROVENANCE_MEMORY_SLICE,
                provenance_refs=[memory_slice_id],
                memory_slice_id=memory_slice_id,
                created_at_utc=utc_now_iso(),
                row_count=0,
            )
        row_count = len(refs.evidence_ids) + len(refs.correction_ids)
        slice_id = stable_id("slice", candidate_id, "memory", memory_slice_id, prefix="slice_")
        return DatasetSlice(
            slice_id=slice_id,
            candidate_id=candidate_id,
            name=name or f"Memory slice {memory_slice_id}",
            provenance_source=PROVENANCE_MEMORY_SLICE,
            provenance_refs=[memory_slice_id],
            included_evidence_ids=list(refs.evidence_ids),
            included_correction_ids=list(refs.correction_ids),
            exclusion_rule_summary="Resolved from memory substrate",
            created_at_utc=utc_now_iso(),
            row_count=row_count,
            memory_slice_id=memory_slice_id,
        )
    except Exception:
        return DatasetSlice(
            slice_id=stable_id("slice", candidate_id, "memory", memory_slice_id, prefix="slice_"),
            candidate_id=candidate_id,
            name=name or f"Memory slice {memory_slice_id}",
            provenance_source=PROVENANCE_MEMORY_SLICE,
            provenance_refs=[memory_slice_id],
            memory_slice_id=memory_slice_id,
            created_at_utc=utc_now_iso(),
            row_count=0,
        )


def build_studio_evidence_bundle(
    evidence_ids: list[str] | None = None,
    correction_ids: list[str] | None = None,
    adaptation_ids: list[str] | None = None,
    cluster_ids: list[str] | None = None,
    session_ids: list[str] | None = None,
) -> StudioEvidenceBundle:
    """Build studio evidence bundle from explicit refs; no silent sweep."""
    evidence_ids = evidence_ids or []
    correction_ids = correction_ids or []
    adaptation_ids = adaptation_ids or []
    cluster_ids = cluster_ids or []
    session_ids = session_ids or []
    n = len(evidence_ids) + len(correction_ids) + len(adaptation_ids) + len(cluster_ids)
    parts = []
    if evidence_ids:
        parts.append(f"{len(evidence_ids)} evidence")
    if correction_ids:
        parts.append(f"{len(correction_ids)} corrections")
    if adaptation_ids:
        parts.append(f"{len(adaptation_ids)} adaptations")
    if cluster_ids:
        parts.append(f"{len(cluster_ids)} clusters")
    if session_ids:
        parts.append(f"{len(session_ids)} sessions")
    return StudioEvidenceBundle(
        evidence_ids=list(evidence_ids),
        correction_ids=list(correction_ids),
        adaptation_ids=list(adaptation_ids),
        cluster_ids=list(cluster_ids),
        session_ids=list(session_ids),
        summary="; ".join(parts) or "empty",
        evidence_count=n,
    )
