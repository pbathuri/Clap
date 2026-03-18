"""
M39A: Build vertical candidates from vertical_packs + cohort/release evidence; score and attach reasons.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.vertical_selection.models import VerticalCandidate
from workflow_dataset.vertical_packs.registry import (
    BUILTIN_CURATED_PACKS,
    get_curated_pack,
)


def _gather_evidence(repo_root: Path | None) -> dict[str, Any]:
    """Cohort/release evidence: sessions_count, avg_usefulness, readiness status, triage open count."""
    out: dict[str, Any] = {
        "sessions_count": 0,
        "avg_usefulness": None,
        "readiness_status": "unknown",
        "open_issue_count": 0,
        "cohort_recommendation": None,
    }
    if not repo_root or not repo_root.exists():
        return out
    try:
        from workflow_dataset.release.dashboard_data import get_dashboard_data
        data = get_dashboard_data(repo_root=repo_root)
        co = data.get("cohort", {}) or {}
        out["sessions_count"] = co.get("sessions_count", 0)
        out["avg_usefulness"] = co.get("avg_usefulness")
        out["cohort_recommendation"] = co.get("recommendation")
    except Exception:
        pass
    try:
        from workflow_dataset.release_readiness import build_release_readiness
        status = build_release_readiness(repo_root)
        out["readiness_status"] = getattr(status, "status", "unknown") or "unknown"
    except Exception:
        pass
    try:
        from workflow_dataset.triage.health import build_cohort_health_summary
        health = build_cohort_health_summary(repo_root=repo_root, cohort_id="")
        out["open_issue_count"] = health.get("open_issue_count", 0)
    except Exception:
        pass
    return out


def _readiness_to_score(status: str) -> float:
    if status == "ready":
        return 1.0
    if status == "degraded":
        return 0.6
    if status == "blocked":
        return 0.2
    return 0.5


def build_candidates(repo_root: Path | str | None = None) -> list[VerticalCandidate]:
    """
    Build vertical candidates from curated packs; attach evidence/readiness/burden scores.
    When no evidence, use defaults so ranking still produces an order.
    """
    root = Path(repo_root).resolve() if repo_root else None
    if not root:
        try:
            from workflow_dataset.path_utils import get_repo_root
            root = Path(get_repo_root()).resolve()
        except Exception:
            root = Path.cwd().resolve()

    evidence = _gather_evidence(root)
    readiness_score = _readiness_to_score(evidence.get("readiness_status") or "unknown")
    sessions = evidence.get("sessions_count") or 0
    usefulness = evidence.get("avg_usefulness")
    if usefulness is not None and isinstance(usefulness, (int, float)):
        evidence_score_base = min(1.0, 0.3 + 0.7 * (float(usefulness) if float(usefulness) <= 1 else float(usefulness) / 100.0))
    else:
        evidence_score_base = 0.3 if sessions > 0 else 0.0
    open_issues = evidence.get("open_issue_count") or 0
    support_burden = min(1.0, open_issues / 20.0) if open_issues else 0.0

    candidates: list[VerticalCandidate] = []
    for pack in BUILTIN_CURATED_PACKS:
        req = pack.required_surfaces
        core_workflow_ids = list(pack.core_workflow_path.workflow_ids) if pack.core_workflow_path else []
        c = VerticalCandidate(
            vertical_id=pack.pack_id,
            label=pack.name,
            description=pack.description or "",
            evidence_score=evidence_score_base,
            readiness_score=readiness_score,
            support_burden_score=support_burden,
            trust_risk_score=0.2,
            core_workflow_ids=core_workflow_ids,
            required_surface_ids=list(req.required_surface_ids),
            optional_surface_ids=list(req.optional_surface_ids),
            excluded_surface_ids=list(req.hidden_for_vertical),
            curated_pack_id=pack.pack_id,
            strength_reason=f"Curated pack; readiness={evidence.get('readiness_status', 'unknown')}; sessions={sessions}.",
            weakness_reason=f"Support burden: {open_issues} open issues." if open_issues else "No major weakness.",
        )
        candidates.append(c)
    return candidates


def get_candidate(vertical_id: str, repo_root: Path | str | None = None) -> VerticalCandidate | None:
    """Return one candidate by id (from built list)."""
    for c in build_candidates(repo_root):
        if c.vertical_id == vertical_id:
            return c
    return None
