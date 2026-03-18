"""
M41E–M41H: Council review storage — save/load/list by subject.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_dataset.council.models import CouncilReview, CouncilSubject, CriterionScore, EvidenceSummary


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


COUNCIL_DIR = "data/local/council"
REVIEWS_DIR = "reviews"


def _council_root(repo_root: Path | str | None) -> Path:
    return _repo_root(repo_root) / COUNCIL_DIR


def _reviews_dir(repo_root: Path | str | None) -> Path:
    return _council_root(repo_root) / REVIEWS_DIR


def _review_path(review_id: str, repo_root: Path | str | None) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in (review_id or "").strip())
    return _reviews_dir(repo_root) / f"{safe}.json"


def _dict_to_subject(d: dict[str, Any]) -> CouncilSubject:
    return CouncilSubject(
        subject_id=d.get("subject_id", ""),
        subject_type=d.get("subject_type", ""),
        ref=d.get("ref", ""),
        summary=d.get("summary", ""),
        extra=d.get("extra", {}),
    )


def _dict_to_criterion(d: dict[str, Any]) -> CriterionScore:
    return CriterionScore(
        perspective_id=d.get("perspective_id", ""),
        score=float(d.get("score", 0)),
        label=d.get("label", ""),
        detail=d.get("detail", ""),
        pass_threshold=bool(d.get("pass_threshold", False)),
    )


def save_review(review: CouncilReview, repo_root: Path | str | None = None) -> Path:
    """Persist CouncilReview to council/reviews/<review_id>.json. Returns path."""
    root = _repo_root(repo_root)
    path = _review_path(review.review_id, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(review.to_dict(), indent=2), encoding="utf-8")
    return path


def load_review(review_id: str, repo_root: Path | str | None = None) -> CouncilReview | None:
    """Load CouncilReview by review_id."""
    path = _review_path(review_id, repo_root)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return _dict_to_review(data)
    except Exception:
        return None


def _dict_to_review(d: dict[str, Any]) -> CouncilReview:
    from workflow_dataset.council.models import DisagreementNote, UncertaintyNote, PromotionRecommendation, QuarantineRecommendation
    sub = d.get("subject", {})
    subject = _dict_to_subject(sub) if isinstance(sub, dict) else sub
    scores = [_dict_to_criterion(c) for c in d.get("criterion_scores", [])]
    disagreements = [
        DisagreementNote(
            note_id=x.get("note_id", ""),
            description=x.get("description", ""),
            perspective_ids=x.get("perspective_ids", []),
            severity=x.get("severity", "medium"),
        )
        for x in d.get("disagreement_notes", [])
    ]
    uncertainties = [
        UncertaintyNote(
            note_id=x.get("note_id", ""),
            description=x.get("description", ""),
            perspective_id=x.get("perspective_id", ""),
            suggested_action=x.get("suggested_action", ""),
        )
        for x in d.get("uncertainty_notes", [])
    ]
    ev = d.get("evidence_summary", {})
    evidence_summary = EvidenceSummary(
        source_ids=ev.get("source_ids", []),
        summary=ev.get("summary", ""),
        evidence_count=ev.get("evidence_count", 0),
    )
    prom = d.get("promotion_recommendation")
    promotion = PromotionRecommendation(
        recommend=prom.get("recommend", False),
        scope=prom.get("scope", "full"),
        reason=prom.get("reason", ""),
    ) if prom else None
    quar = d.get("quarantine_recommendation")
    quarantine = QuarantineRecommendation(
        recommend=quar.get("recommend", False),
        reason=quar.get("reason", ""),
        review_by_hint=quar.get("review_by_hint", ""),
    ) if quar else None
    return CouncilReview(
        review_id=d.get("review_id", ""),
        subject=subject,
        at_iso=d.get("at_iso", ""),
        criterion_scores=scores,
        disagreement_notes=disagreements,
        uncertainty_notes=uncertainties,
        evidence_summary=evidence_summary,
        synthesis_decision=d.get("synthesis_decision", ""),
        synthesis_reason=d.get("synthesis_reason", ""),
        promotion_recommendation=promotion,
        quarantine_recommendation=quarantine,
    )


def list_reviews(repo_root: Path | str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """List reviews (newest first by mtime). Returns list of review dicts (minimal: review_id, subject_id, at_iso, synthesis_decision)."""
    root = _repo_root(repo_root)
    dir_path = _reviews_dir(root)
    if not dir_path.exists():
        return []
    out = []
    for p in sorted(dir_path.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if not p.is_file() or p.suffix != ".json":
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            out.append({
                "review_id": data.get("review_id", ""),
                "subject_id": data.get("subject", {}).get("subject_id", ""),
                "subject_type": data.get("subject", {}).get("subject_type", ""),
                "at_iso": data.get("at_iso", ""),
                "synthesis_decision": data.get("synthesis_decision", ""),
            })
        except Exception:
            pass
        if len(out) >= limit:
            break
    return out


def get_review_by_subject(subject_id: str, repo_root: Path | str | None = None) -> CouncilReview | None:
    """Return most recent review for subject_id, or None."""
    for r in list_reviews(repo_root, limit=100):
        if r.get("subject_id") == subject_id:
            return load_review(r["review_id"], repo_root)
    return None
