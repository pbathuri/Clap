"""
M41E–M41H: Council review flow — run full council review for a subject, persist, return review.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workflow_dataset.council.models import (
    CouncilReview,
    CouncilSubject,
    CriterionScore,
    EvidenceSummary,
    DEFAULT_PERSPECTIVE_IDS,
)
from workflow_dataset.council.perspectives import get_default_council, score_subject_from_perspective
from workflow_dataset.council.synthesis import synthesize_decision
from workflow_dataset.council.store import save_review
from workflow_dataset.council.presets import get_preset, get_default_preset
from workflow_dataset.council.promotion_policy import get_effective_policy, apply_policy_outcome


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _stable_id(*parts: str, prefix: str = "") -> str:
    import hashlib
    h = hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:12]
    return f"{prefix}{h}"


def run_council_review(
    subject_id: str,
    subject_type: str,
    ref: str = "",
    summary: str = "",
    repo_root: Path | str | None = None,
    persist: bool = True,
    preset_id: str = "",
    cohort_id: str = "",
) -> CouncilReview:
    """
    Run council review for subject: score from each perspective, build evidence summary, synthesize decision.
    If preset_id is set, use that council preset; else default. If cohort_id is set, effective promotion
    policy is applied for clearer limited vs quarantine vs reject.
    If persist=True, save to data/local/council/reviews/.
    """
    root = _repo_root(repo_root)
    preset = get_preset(preset_id) if preset_id else get_default_preset()
    policy = get_effective_policy(cohort_id=cohort_id, repo_root=root)
    now = datetime.now(timezone.utc)
    at_iso = now.isoformat()[:19] + "Z"
    review_id = _stable_id("council", subject_id, subject_type, at_iso, prefix="cr_")
    ref = ref or subject_id

    subject = CouncilSubject(
        subject_id=subject_id,
        subject_type=subject_type,
        ref=ref,
        summary=summary or f"{subject_type} {subject_id}",
    )

    council = get_default_council()
    criterion_scores: list[CriterionScore] = []
    for pid in DEFAULT_PERSPECTIVE_IDS:
        sc = score_subject_from_perspective(subject_id, subject_type, ref, pid, root)
        criterion_scores.append(sc)

    # Evidence summary from subject type
    source_ids: list[str] = [subject_id, ref]
    evidence_count = 0
    if subject_type == "adaptation" and ref:
        try:
            from workflow_dataset.safe_adaptation.store import load_candidate
            cand = load_candidate(ref, root)
            if cand:
                evidence_count = cand.evidence.evidence_count or len(cand.evidence.evidence_ids) + len(cand.evidence.correction_ids)
                source_ids.extend(cand.evidence.evidence_ids[:5])
        except Exception:
            pass
    evidence_summary = EvidenceSummary(
        source_ids=source_ids[:20],
        summary=f"subject_type={subject_type} ref={ref}",
        evidence_count=evidence_count or 1,
    )

    # Policy context for adaptation subjects (boundary conditions)
    policy_context: dict[str, Any] = {}
    if subject_type == "adaptation" and ref:
        try:
            from workflow_dataset.safe_adaptation.store import load_candidate
            from workflow_dataset.safe_adaptation.boundary import (
                affects_supported_surface,
                affects_experimental_surface,
                experimental_only,
                changes_trust_posture,
            )
            cand = load_candidate(ref, root)
            if cand:
                cid = cohort_id or cand.cohort_id
                policy_context["affects_supported_surface"] = affects_supported_surface(cand, cid)
                policy_context["affects_experimental_only"] = experimental_only(cand, cid)
                policy_context["affects_experimental_surface"] = affects_experimental_surface(cand, cid)
                policy_context["changes_trust_posture"] = changes_trust_posture(cand)
                policy_context["risk_level"] = cand.risk_level or "low"
        except Exception:
            pass
    policy_outcome = apply_policy_outcome(policy, policy_context)

    review = CouncilReview(
        review_id=review_id,
        subject=subject,
        at_iso=at_iso,
        criterion_scores=criterion_scores,
        disagreement_notes=[],
        uncertainty_notes=[],
        evidence_summary=evidence_summary,
        synthesis_decision="",
        synthesis_reason="",
    )
    review = synthesize_decision(review, preset=preset, policy_outcome_override=policy_outcome)

    if persist:
        save_review(review, root)
    return review


def build_disagreement_report(review: CouncilReview) -> dict[str, Any]:
    """Build report focused on disagreement and uncertainty (visible, not collapsed)."""
    return {
        "review_id": review.review_id,
        "subject_id": review.subject.subject_id,
        "synthesis_decision": review.synthesis_decision,
        "synthesis_reason": review.synthesis_reason,
        "disagreement_notes": [d.to_dict() for d in review.disagreement_notes],
        "uncertainty_notes": [u.to_dict() for u in review.uncertainty_notes],
        "scores_below_threshold": [
            {"perspective_id": s.perspective_id, "score": s.score, "detail": s.detail}
            for s in review.criterion_scores if not s.pass_threshold
        ],
    }
