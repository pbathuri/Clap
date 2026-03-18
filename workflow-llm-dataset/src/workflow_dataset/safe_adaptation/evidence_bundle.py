"""
M38I–M38L: Build adaptation evidence bundle from triage evidence and optional corrections.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.safe_adaptation.models import AdaptationEvidenceBundle


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_evidence_bundle(
    cohort_id: str = "",
    evidence_ids: list[str] | None = None,
    correction_ids: list[str] | None = None,
    session_ids: list[str] | None = None,
    limit_evidence: int = 50,
    repo_root: Path | str | None = None,
) -> AdaptationEvidenceBundle:
    """
    Build an evidence bundle for an adaptation candidate. If evidence_ids provided,
    only those are included; else recent evidence for cohort is used (up to limit).
    correction_ids and session_ids are passed through.
    """
    evidence_ids = evidence_ids or []
    correction_ids = correction_ids or []
    session_ids = session_ids or []
    root = _root(repo_root)

    if not evidence_ids:
        try:
            from workflow_dataset.triage.store import list_evidence
            evidence = list_evidence(
                repo_root=root,
                cohort_id=cohort_id,
                limit=limit_evidence,
            )
            evidence_ids = [e.evidence_id for e in evidence[:limit_evidence]]
        except Exception:
            evidence_ids = []

    session_set: set[str] = set(session_ids)
    try:
        from workflow_dataset.triage.store import list_evidence
        evidence = list_evidence(repo_root=root, cohort_id=cohort_id, limit=500)
        for e in evidence:
            if e.evidence_id in evidence_ids and e.session_id:
                session_set.add(e.session_id)
    except Exception:
        pass

    summary_parts = [f"{len(evidence_ids)} evidence", f"{len(correction_ids)} corrections"]
    if session_set:
        summary_parts.append(f"{len(session_set)} sessions")
    summary = "; ".join(summary_parts)

    return AdaptationEvidenceBundle(
        evidence_ids=list(evidence_ids),
        correction_ids=list(correction_ids),
        session_ids=list(session_set),
        summary=summary,
        evidence_count=len(evidence_ids) + len(correction_ids),
    )


def build_bundle_from_session_feedback(
    cohort_id: str,
    session_id: str,
    evidence_id: str = "",
    repo_root: Path | str | None = None,
) -> AdaptationEvidenceBundle:
    """
    One-off: build a minimal bundle from a single session (e.g. for creating
    a candidate from one accepted session pattern).
    """
    evidence_ids = [evidence_id] if evidence_id else []
    return build_evidence_bundle(
        cohort_id=cohort_id,
        evidence_ids=evidence_ids if evidence_ids else None,
        session_ids=[session_id],
        limit_evidence=10,
        repo_root=repo_root,
    )
