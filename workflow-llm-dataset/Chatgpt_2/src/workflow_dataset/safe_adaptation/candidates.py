"""
M38I–M38L: Create adaptation candidates from evidence (triage, corrections).
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

from workflow_dataset.safe_adaptation.models import (
    AdaptationCandidate,
    AdaptationEvidenceBundle,
    ADAPTATION_STATUS_PENDING,
    ADAPTATION_SURFACE_EXPERIMENTAL,
    ADAPTATION_SURFACE_SUPPORTED,
)
from workflow_dataset.safe_adaptation.evidence_bundle import build_evidence_bundle
from workflow_dataset.safe_adaptation.store import save_candidate
from workflow_dataset.cohort.surface_matrix import get_supported_surfaces


def create_candidate(
    cohort_id: str,
    affected_surface_ids: list[str],
    target_type: str,
    target_id: str,
    after_value: Any,
    before_value: Any = None,
    evidence_ids: list[str] | None = None,
    correction_ids: list[str] | None = None,
    risk_level: str = "low",
    summary: str = "",
    repo_root: Path | str | None = None,
) -> AdaptationCandidate:
    """
    Create and persist one adaptation candidate. surface_type is inferred from
    cohort matrix (if any surface is supported -> supported, else experimental).
    """
    supported = set(get_supported_surfaces(cohort_id))
    affected_set = set(affected_surface_ids)
    surface_type = ADAPTATION_SURFACE_SUPPORTED if (affected_set & supported) else ADAPTATION_SURFACE_EXPERIMENTAL

    evidence = build_evidence_bundle(
        cohort_id=cohort_id,
        evidence_ids=evidence_ids,
        correction_ids=correction_ids or [],
        repo_root=repo_root,
    )
    adaptation_id = stable_id("adapt", cohort_id, target_type, target_id, utc_now_iso(), prefix="adapt_")
    now = utc_now_iso()
    candidate = AdaptationCandidate(
        adaptation_id=adaptation_id,
        cohort_id=cohort_id,
        affected_surface_ids=list(affected_surface_ids),
        surface_type=surface_type,
        target_type=target_type,
        target_id=target_id,
        before_value=before_value,
        after_value=after_value,
        evidence=evidence,
        risk_level=risk_level,
        review_status=ADAPTATION_STATUS_PENDING,
        created_at_utc=now,
        updated_at_utc=now,
        summary=summary or f"{target_type} -> {target_id}",
    )
    save_candidate(candidate, repo_root)
    return candidate
