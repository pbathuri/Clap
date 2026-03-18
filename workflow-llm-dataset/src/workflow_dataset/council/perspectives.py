"""
M41E–M41H: Council perspectives — score a subject from each evaluation dimension using existing subsystems.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.council.models import (
    CriterionScore,
    EvaluationPerspective,
    CouncilMember,
    EvaluationCouncil,
    DEFAULT_PERSPECTIVE_IDS,
    PERSPECTIVE_PRODUCT_VALUE,
    PERSPECTIVE_SAFETY_TRUST,
    PERSPECTIVE_SUPPORTABILITY,
    PERSPECTIVE_RELIABILITY,
    PERSPECTIVE_VERTICAL_FIT,
    PERSPECTIVE_OPERATOR_BURDEN,
    PERSPECTIVE_ADAPTATION_RISK,
)


PERSPECTIVE_LABELS: dict[str, str] = {
    PERSPECTIVE_PRODUCT_VALUE: "Product value",
    PERSPECTIVE_SAFETY_TRUST: "Safety / trust",
    PERSPECTIVE_SUPPORTABILITY: "Supportability",
    PERSPECTIVE_RELIABILITY: "Reliability",
    PERSPECTIVE_VERTICAL_FIT: "Vertical fit",
    PERSPECTIVE_OPERATOR_BURDEN: "Operator burden",
    PERSPECTIVE_ADAPTATION_RISK: "Adaptation risk",
}


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def get_default_council() -> EvaluationCouncil:
    """Default council: one member per perspective, equal weight."""
    members = [
        CouncilMember(member_id=f"member_{pid}", perspective_id=pid, label=PERSPECTIVE_LABELS.get(pid, pid))
        for pid in DEFAULT_PERSPECTIVE_IDS
    ]
    return EvaluationCouncil(
        council_id="default",
        label="Default evaluation council",
        members=members,
        min_score_to_promote=0.6,
        description="Multi-perspective evaluation for safe improvement decisions.",
    )


def get_perspective(perspective_id: str) -> EvaluationPerspective:
    """Return EvaluationPerspective for perspective_id."""
    return EvaluationPerspective(
        perspective_id=perspective_id,
        label=PERSPECTIVE_LABELS.get(perspective_id, perspective_id),
        description="",
    )


def score_subject_from_perspective(
    subject_id: str,
    subject_type: str,
    ref: str,
    perspective_id: str,
    repo_root: Path | str | None = None,
) -> CriterionScore:
    """
    Score one perspective for a subject. Uses existing subsystems (reliability, triage, safe_adaptation, trust, release_readiness).
    Returns CriterionScore with score 0.0–1.0, detail, pass_threshold.
    """
    root = _repo_root(repo_root)
    label = PERSPECTIVE_LABELS.get(perspective_id, perspective_id)
    score = 0.5
    detail = ""
    pass_threshold = True

    if subject_type == "adaptation" and ref:
        try:
            from workflow_dataset.safe_adaptation.store import load_candidate
            from workflow_dataset.safe_adaptation.boundary import (
                evaluate_boundary_check,
                safe_for_cohort,
                must_quarantine,
                changes_trust_posture,
                experimental_only,
            )
            cand = load_candidate(ref, root)
            if not cand:
                return CriterionScore(perspective_id=perspective_id, score=0.0, label=label, detail="candidate_not_found", pass_threshold=False)
            cid = cand.cohort_id or ""
            check = evaluate_boundary_check(cand, cid)
            if perspective_id == PERSPECTIVE_SAFETY_TRUST:
                if changes_trust_posture(cand):
                    score = 0.3
                    detail = "changes_trust_posture; review required"
                    pass_threshold = False
                else:
                    score = 0.8
                    detail = "no trust posture change"
            elif perspective_id == PERSPECTIVE_ADAPTATION_RISK:
                if must_quarantine(cand, cid):
                    score = 0.2
                    detail = "must_quarantine true"
                    pass_threshold = False
                elif check.safe_for_cohort:
                    score = 0.8
                    detail = "safe_for_cohort"
                else:
                    score = 0.4
                    detail = "boundary check not safe"
            elif perspective_id == PERSPECTIVE_SUPPORTABILITY:
                score = 0.7 if check.affects_supported_surface else 0.8
                detail = f"supported={check.affects_supported_surface} experimental={check.affects_experimental_surface}"
            elif perspective_id == PERSPECTIVE_PRODUCT_VALUE:
                ev_count = (cand.evidence.evidence_count or len(cand.evidence.evidence_ids) + len(cand.evidence.correction_ids))
                score = min(0.9, 0.4 + ev_count * 0.15)
                detail = f"evidence_count={ev_count}"
            elif perspective_id == PERSPECTIVE_OPERATOR_BURDEN:
                score = 0.6 if experimental_only(cand, cid) else 0.7
                detail = "experimental_only" if experimental_only(cand, cid) else "touches supported"
            else:
                detail = "adaptation; no specific signal"
        except Exception as e:
            detail = str(e)
            score = 0.0
            pass_threshold = False
        return CriterionScore(perspective_id=perspective_id, score=score, label=label, detail=detail, pass_threshold=score >= 0.6)

    # Generic / eval_run / experiment: use repo-wide signals
    if perspective_id == PERSPECTIVE_RELIABILITY:
        try:
            from workflow_dataset.reliability import load_latest_run
            latest = load_latest_run(root)
            outcome = (latest or {}).get("outcome", "")
            if outcome == "pass":
                score, detail = 0.9, "reliability pass"
            elif outcome == "degraded":
                score, detail = 0.6, "reliability degraded"
            else:
                score, detail = 0.3, f"reliability outcome={outcome}"
            pass_threshold = score >= 0.6
        except Exception as e:
            detail = str(e)
            score = 0.0
            pass_threshold = False
    elif perspective_id == PERSPECTIVE_SUPPORTABILITY:
        try:
            from workflow_dataset.release_readiness.readiness import build_release_readiness
            rr = build_release_readiness(root)
            if rr.status == "ready":
                score, detail = 0.8, "readiness ready"
            elif rr.status == "degraded":
                score, detail = 0.5, "readiness degraded"
            else:
                score, detail = 0.2, f"readiness {rr.status}"
            pass_threshold = score >= 0.5
        except Exception as e:
            detail = str(e)
            score = 0.0
            pass_threshold = False
    elif perspective_id == PERSPECTIVE_SAFETY_TRUST:
        try:
            from workflow_dataset.trust.cockpit import build_trust_cockpit
            cockpit = build_trust_cockpit(root)
            reg = (cockpit.get("approval_readiness") or {}).get("registry_exists", False)
            score = 0.8 if reg else 0.4
            detail = "registry_exists" if reg else "no registry"
            pass_threshold = score >= 0.5
        except Exception as e:
            detail = str(e)
            score = 0.0
            pass_threshold = False
    elif perspective_id == PERSPECTIVE_VERTICAL_FIT:
        try:
            from workflow_dataset.vertical_selection import get_active_vertical_id
            vid = get_active_vertical_id(root)
            score = 0.7 if vid else 0.5
            detail = f"vertical={vid or 'none'}"
            pass_threshold = True
        except Exception as e:
            detail = str(e)
            score = 0.5
            pass_threshold = True
    elif perspective_id == PERSPECTIVE_OPERATOR_BURDEN:
        score, detail = 0.6, "generic; no specific burden signal"
        pass_threshold = True
    elif perspective_id == PERSPECTIVE_PRODUCT_VALUE:
        score, detail = 0.5, "generic; run eval board or adaptation for value signal"
        pass_threshold = True
    else:
        detail = "no scorer for perspective"
        pass_threshold = score >= 0.6

    return CriterionScore(perspective_id=perspective_id, score=score, label=label, detail=detail, pass_threshold=pass_threshold)
