"""
M38I–M38L: Adaptation review and application flow — inspect, accept/reject/quarantine,
apply within boundaries, record rationale and behavior delta.
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
    CohortBoundaryCheck,
    ReviewDecision,
    QuarantineState,
    ReviewDecisionKind,
    ADAPTATION_STATUS_ACCEPTED,
    ADAPTATION_STATUS_REJECTED,
    ADAPTATION_STATUS_QUARANTINED,
    ADAPTATION_STATUS_BLOCKED,
)
from workflow_dataset.safe_adaptation.boundary import (
    evaluate_boundary_check,
    classify_adaptation,
    safe_for_cohort,
    must_quarantine,
)
from workflow_dataset.safe_adaptation.store import (
    load_candidate,
    save_candidate,
    update_review_status,
    append_decision,
    append_quarantine,
    list_recent_decisions,
)


def inspect_candidate(
    adaptation_id: str,
    cohort_id: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Load candidate and boundary check; return inspect payload: candidate dict,
    boundary_check dict, safe_for_cohort, classification hint.
    """
    candidate = load_candidate(adaptation_id, repo_root)
    if not candidate:
        return {"error": "candidate_not_found", "adaptation_id": adaptation_id}
    cid = cohort_id or candidate.cohort_id
    check = evaluate_boundary_check(candidate, cid)
    classification = classify_adaptation(candidate, cid)
    return {
        "candidate": candidate.to_dict(),
        "boundary_check": check.to_dict(),
        "safe_for_cohort": safe_for_cohort(candidate, cid),
        "must_quarantine": must_quarantine(candidate, cid),
        "classification": getattr(classification, "candidate_id", ""),
        "classification_kind": type(classification).__name__,
    }


def _record_decision(
    candidate_id: str,
    decision: str,
    rationale: str,
    behavior_delta_summary: str = "",
    reviewed_by: str = "cli",
    repo_root: Path | str | None = None,
) -> ReviewDecision:
    decision_id = stable_id("dec", candidate_id, decision, utc_now_iso(), prefix="dec_")
    rec = ReviewDecision(
        decision_id=decision_id,
        candidate_id=candidate_id,
        decision=decision,
        rationale=rationale,
        behavior_delta_summary=behavior_delta_summary,
        reviewed_at_utc=utc_now_iso(),
        reviewed_by=reviewed_by,
    )
    append_decision(rec, repo_root)
    return rec


def accept_candidate(
    adaptation_id: str,
    rationale: str = "",
    behavior_delta_summary: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Accept candidate: boundary check must pass (safe_for_cohort); then update status
    to accepted, record decision. Does NOT apply; use apply_within_boundaries after.
    """
    candidate = load_candidate(adaptation_id, repo_root)
    if not candidate:
        return {"ok": False, "error": "candidate_not_found"}
    cid = candidate.cohort_id
    if not safe_for_cohort(candidate, cid):
        return {"ok": False, "error": "not_safe_for_cohort", "message": "Run boundary-check first; candidate fails boundary."}
    update_review_status(adaptation_id, ADAPTATION_STATUS_ACCEPTED, repo_root)
    _record_decision(
        adaptation_id, ReviewDecisionKind.ACCEPT.value, rationale,
        behavior_delta_summary=behavior_delta_summary, repo_root=repo_root,
    )
    return {"ok": True, "adaptation_id": adaptation_id, "review_status": ADAPTATION_STATUS_ACCEPTED}


def reject_candidate(
    adaptation_id: str,
    rationale: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Reject candidate: set status rejected, record decision."""
    candidate = load_candidate(adaptation_id, repo_root)
    if not candidate:
        return {"ok": False, "error": "candidate_not_found"}
    update_review_status(adaptation_id, ADAPTATION_STATUS_REJECTED, repo_root)
    _record_decision(adaptation_id, ReviewDecisionKind.REJECT.value, rationale, repo_root=repo_root)
    return {"ok": True, "adaptation_id": adaptation_id, "review_status": ADAPTATION_STATUS_REJECTED}


def quarantine_candidate(
    adaptation_id: str,
    reason: str = "",
    notes: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Quarantine candidate: set status quarantined, append quarantine record, record decision."""
    candidate = load_candidate(adaptation_id, repo_root)
    if not candidate:
        return {"ok": False, "error": "candidate_not_found"}
    update_review_status(adaptation_id, ADAPTATION_STATUS_QUARANTINED, repo_root)
    state = QuarantineState(
        candidate_id=adaptation_id,
        reason=reason or "operator_quarantine",
        quarantined_at_utc=utc_now_iso(),
        notes=notes,
    )
    append_quarantine(state, repo_root)
    _record_decision(
        adaptation_id, ReviewDecisionKind.QUARANTINE.value,
        rationale=reason or "Quarantined for review.", repo_root=repo_root,
    )
    return {"ok": True, "adaptation_id": adaptation_id, "review_status": ADAPTATION_STATUS_QUARANTINED}


def apply_within_boundaries(
    adaptation_id: str,
    behavior_delta_summary: str = "",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Apply accepted candidate only within allowed cohort/surface boundaries.
    First draft: records the application (decision with behavior_delta_summary);
    does not mutate pack/correction/preference state — that can be wired to
    personal_adaptation or corrections in a later pass.
    """
    candidate = load_candidate(adaptation_id, repo_root)
    if not candidate:
        return {"ok": False, "error": "candidate_not_found"}
    if candidate.review_status != ADAPTATION_STATUS_ACCEPTED:
        return {"ok": False, "error": "not_accepted", "message": "Only accepted candidates can be applied."}
    cid = candidate.cohort_id
    if not safe_for_cohort(candidate, cid):
        return {"ok": False, "error": "boundary_violation", "message": "Candidate no longer safe for cohort."}
    classification = classify_adaptation(candidate, cid)
    if hasattr(classification, "blocked_surface_ids") and getattr(classification, "blocked_surface_ids", None):
        return {"ok": False, "error": "blocked", "message": getattr(classification, "reason", "Blocked.")}
    delta = behavior_delta_summary or f"Applied {candidate.target_type} for {candidate.target_id} (surfaces: {candidate.affected_surface_ids})"
    _record_decision(
        adaptation_id, "apply", rationale="Applied within boundaries.",
        behavior_delta_summary=delta, reviewed_by="cli", repo_root=repo_root,
    )
    return {
        "ok": True,
        "adaptation_id": adaptation_id,
        "behavior_delta_summary": delta,
        "allowed_surfaces": getattr(classification, "surface_ids", candidate.affected_surface_ids),
    }


def record_rationale_and_delta(
    adaptation_id: str,
    rationale: str,
    behavior_delta_summary: str = "",
    repo_root: Path | str | None = None,
) -> bool:
    """Append a decision record with rationale and optional behavior delta (e.g. after manual apply)."""
    _record_decision(
        adaptation_id, "note", rationale=rationale,
        behavior_delta_summary=behavior_delta_summary, repo_root=repo_root,
    )
    return True
