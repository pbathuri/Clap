"""
M38I–M38L: Boundary-aware adaptation evaluation — supported/experimental/blocked,
cohort safety, trust posture, quarantine.
"""

from __future__ import annotations

from workflow_dataset.cohort.surface_matrix import (
    get_matrix,
    get_supported_surfaces,
    get_experimental_surfaces,
    get_blocked_surfaces,
)
from workflow_dataset.cohort.models import SUPPORT_BLOCKED, SUPPORT_EXPERIMENTAL, SUPPORT_SUPPORTED
from workflow_dataset.safe_adaptation.models import (
    AdaptationCandidate,
    CohortBoundaryCheck,
    BlockedAdaptation,
    SupportedSurfaceAdaptation,
    ExperimentalSurfaceAdaptation,
)


# Target types that imply trust/authority change (quarantine or reject unless explicitly reviewed)
TRUST_RELATED_TARGET_TYPES = frozenset({
    "trust_tier", "approval_scope", "routine_contract", "authority_scope",
    "allowed_trust_tier_ids", "required_approvals",
})


def affects_supported_surface(candidate: AdaptationCandidate, cohort_id: str) -> bool:
    """True if any of the candidate's affected surfaces are supported for this cohort."""
    supported = set(get_supported_surfaces(cohort_id or candidate.cohort_id))
    return bool(supported & set(candidate.affected_surface_ids))


def affects_experimental_surface(candidate: AdaptationCandidate, cohort_id: str) -> bool:
    """True if any affected surface is experimental for this cohort."""
    experimental = set(get_experimental_surfaces(cohort_id or candidate.cohort_id))
    return bool(experimental & set(candidate.affected_surface_ids))


def affects_blocked_surface(candidate: AdaptationCandidate, cohort_id: str) -> bool:
    """True if any affected surface is blocked for this cohort."""
    blocked = set(get_blocked_surfaces(cohort_id or candidate.cohort_id))
    return bool(blocked & set(candidate.affected_surface_ids))


def changes_trust_posture(candidate: AdaptationCandidate) -> bool:
    """True if adaptation touches trust/authority (from target_type or extra)."""
    if candidate.target_type in TRUST_RELATED_TARGET_TYPES:
        return True
    return bool(candidate.extra.get("changes_trust_posture", False))


def experimental_only(candidate: AdaptationCandidate, cohort_id: str) -> bool:
    """True if candidate affects only experimental surfaces (none supported, none blocked)."""
    cid = cohort_id or candidate.cohort_id
    if affects_blocked_surface(candidate, cid):
        return False
    if affects_supported_surface(candidate, cid):
        return False
    return affects_experimental_surface(candidate, cid)


def must_quarantine(candidate: AdaptationCandidate, cohort_id: str) -> bool:
    """
    True if candidate should be quarantined: touches trust, or high risk + supported,
    or low evidence + supported surface.
    """
    cid = cohort_id or candidate.cohort_id
    if changes_trust_posture(candidate):
        return True
    if candidate.risk_level == "high" and affects_supported_surface(candidate, cid):
        return True
    evidence_count = (candidate.evidence.evidence_count or
                      len(candidate.evidence.evidence_ids) + len(candidate.evidence.correction_ids))
    if evidence_count < 2 and affects_supported_surface(candidate, cid):
        return True
    return False


def safe_for_cohort(candidate: AdaptationCandidate, cohort_id: str) -> bool:
    """
    True if candidate can be applied within cohort boundaries: no blocked surface,
    and not forced to quarantine.
    """
    cid = cohort_id or candidate.cohort_id
    if affects_blocked_surface(candidate, cid):
        return False
    if must_quarantine(candidate, cid):
        return False
    return True


def evaluate_boundary_check(
    candidate: AdaptationCandidate,
    cohort_id: str | None = None,
) -> CohortBoundaryCheck:
    """
    Full boundary evaluation for a candidate. Returns CohortBoundaryCheck with
    affects_*, safe_for_cohort, changes_trust_posture, experimental_only, must_quarantine, reasons.
    """
    cid = cohort_id or candidate.cohort_id
    matrix = get_matrix(cid) if cid else {}
    supported = set(get_supported_surfaces(cid))
    experimental = set(get_experimental_surfaces(cid))
    blocked = set(get_blocked_surfaces(cid))
    affected = set(candidate.affected_surface_ids)

    affects_supp = bool(affected & supported)
    affects_exp = bool(affected & experimental)
    affects_blk = bool(affected & blocked)
    trust_change = changes_trust_posture(candidate)
    exp_only = affects_exp and not affects_supp and not affects_blk
    quarantine = must_quarantine(candidate, cid)
    safe = not affects_blk and not quarantine

    reasons: list[str] = []
    if affects_blk:
        reasons.append("affects_blocked_surface")
    if trust_change:
        reasons.append("changes_trust_posture")
    if candidate.risk_level == "high" and affects_supp:
        reasons.append("high_risk_supported_surface")
    evidence_count = (candidate.evidence.evidence_count or
                      len(candidate.evidence.evidence_ids) + len(candidate.evidence.correction_ids))
    if evidence_count < 2 and affects_supp:
        reasons.append("low_evidence_supported_surface")
    if not reasons and affects_supp:
        reasons.append("supported_surface_ok_with_review")
    if exp_only:
        reasons.append("experimental_only")

    allowed = list((affected & supported) | (affected & experimental))
    blocked_list = list(affected & blocked)

    return CohortBoundaryCheck(
        candidate_id=candidate.adaptation_id,
        cohort_id=cid,
        affects_supported_surface=affects_supp,
        affects_experimental_surface=affects_exp,
        affects_blocked_surface=affects_blk,
        safe_for_cohort=safe,
        changes_trust_posture=trust_change,
        experimental_only=exp_only,
        must_quarantine=quarantine,
        reasons=reasons,
        allowed_surfaces=allowed,
        blocked_surfaces=blocked_list,
    )


def classify_adaptation(
    candidate: AdaptationCandidate,
    cohort_id: str | None = None,
) -> BlockedAdaptation | SupportedSurfaceAdaptation | ExperimentalSurfaceAdaptation:
    """
    Classify candidate as blocked, supported-surface only, or experimental-surface only.
    Uses evaluate_boundary_check; if blocked, returns BlockedAdaptation; else splits
    allowed_surfaces into supported vs experimental and returns the appropriate wrapper.
    """
    check = evaluate_boundary_check(candidate, cohort_id)
    cid = cohort_id or candidate.cohort_id
    supported = set(get_supported_surfaces(cid))
    if check.affects_blocked_surface or check.must_quarantine:
        return BlockedAdaptation(
            candidate_id=candidate.adaptation_id,
            reason="; ".join(check.reasons) or "boundary_check_failed",
            blocked_surface_ids=check.blocked_surfaces,
        )
    supported_here = [s for s in check.allowed_surfaces if s in supported]
    experimental_here = [s for s in check.allowed_surfaces if s not in supported]
    if supported_here:
        return SupportedSurfaceAdaptation(
            candidate_id=candidate.adaptation_id,
            surface_ids=supported_here,
            summary=candidate.summary or f"Supported-surface adaptation for {candidate.target_type}",
        )
    return ExperimentalSurfaceAdaptation(
        candidate_id=candidate.adaptation_id,
        surface_ids=experimental_here,
        summary=candidate.summary or f"Experimental-surface adaptation for {candidate.target_type}",
    )
