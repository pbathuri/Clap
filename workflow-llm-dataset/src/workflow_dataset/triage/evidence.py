"""
M38E–M38H: Create evidence from session, reliability, readiness.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

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

from workflow_dataset.triage.models import CohortEvidenceItem, EvidenceKind
from workflow_dataset.triage.store import append_evidence


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def create_evidence_from_session(
    session_id: str,
    cohort_id: str = "",
    project_id: str = "",
    blocking_issues: list[str] | None = None,
    warnings: list[str] | None = None,
    degraded_mode: bool = False,
    disposition: str = "",
    summary: str = "",
    repo_root: Path | str | None = None,
) -> CohortEvidenceItem:
    """Create and persist one evidence item from pilot session data."""
    now = utc_now_iso()
    blocking_issues = blocking_issues or []
    warnings = warnings or []
    kind = EvidenceKind.DEGRADED_MODE if degraded_mode else EvidenceKind.SESSION_FEEDBACK
    if not summary:
        summary = f"Session {session_id}: blocking={len(blocking_issues)} warnings={len(warnings)} degraded={degraded_mode} disposition={disposition}"
    evidence_id = stable_id("ev", "session", session_id, now, prefix="ev_")
    item = CohortEvidenceItem(
        evidence_id=evidence_id,
        cohort_id=cohort_id,
        session_id=session_id,
        project_id=project_id,
        kind=kind,
        source_ref=session_id,
        summary=summary[:500],
        created_at_utc=now,
        extra={"blocking_count": len(blocking_issues), "warnings_count": len(warnings), "disposition": disposition},
    )
    append_evidence(item, repo_root)
    return item


def create_evidence_from_reliability(
    run_id: str,
    path_id: str,
    outcome: str,
    subsystem: str = "",
    reasons: list[str] | None = None,
    cohort_id: str = "",
    repo_root: Path | str | None = None,
) -> CohortEvidenceItem:
    """Create evidence from reliability run result."""
    now = utc_now_iso()
    reasons = reasons or []
    kind = EvidenceKind.RELIABILITY_FAILURE if outcome in ("fail", "blocked", "degraded") else EvidenceKind.OTHER
    summary = f"Reliability {outcome}: path={path_id}" + (f" subsystem={subsystem}" if subsystem else "") + (f" reasons={reasons[:3]}" if reasons else "")
    evidence_id = stable_id("ev", "rel", run_id, now, prefix="ev_")
    item = CohortEvidenceItem(
        evidence_id=evidence_id,
        cohort_id=cohort_id,
        session_id="",
        source_ref=run_id,
        kind=kind,
        summary=summary[:500],
        created_at_utc=now,
        extra={"path_id": path_id, "outcome": outcome, "subsystem": subsystem, "reasons": reasons},
    )
    append_evidence(item, repo_root)
    return item


def create_evidence_from_readiness_blocker(
    blocker_summary: str,
    cohort_id: str = "",
    repo_root: Path | str | None = None,
) -> CohortEvidenceItem:
    """Create evidence from release readiness blocker."""
    now = utc_now_iso()
    evidence_id = stable_id("ev", "readiness", blocker_summary[:80], now, prefix="ev_")
    item = CohortEvidenceItem(
        evidence_id=evidence_id,
        cohort_id=cohort_id,
        kind=EvidenceKind.READINESS_BLOCKER,
        source_ref="readiness",
        summary=blocker_summary[:500],
        created_at_utc=now,
    )
    append_evidence(item, repo_root)
    return item
