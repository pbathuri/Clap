"""
M21: Rank candidate repos for role/industry/workflow/task/pain-point queries. Offline-first.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from workflow_dataset.capability_intake.source_registry import list_sources
from workflow_dataset.capability_intake.source_models import ExternalSourceCandidate


@dataclass
class RepoTaskFitQuery:
    """Query for ranking repos by task/role/industry fit."""

    role: str = ""
    industry: str = ""
    workflow_type: str = ""
    task_type: str = ""
    pain_points: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    local_first_required: bool = True
    UI_need: bool = False
    parsing_need: bool = False
    orchestration_need: bool = False
    model_need: bool = False
    proxy_need: bool = False


@dataclass
class RepoTaskFitResult:
    """Single result from ranking."""

    source_id: str = ""
    fit_score: float = 0.0
    role_match_score: float = 0.0
    workflow_match_score: float = 0.0
    pain_point_match_score: float = 0.0
    safety_score: float = 0.0
    maintenance_score: float = 0.0
    license_score: float = 0.0
    adoption_recommendation: str = ""
    rationale: str = ""


def rank_sources_for_query(
    query: RepoTaskFitQuery,
    registry_path: str | None = None,
    top_k: int = 10,
) -> list[RepoTaskFitResult]:
    """
    Rank registered sources by fit to the query. Offline; uses registry only.
    Scores are heuristic from metadata (role, workflow, risk, maintenance, license).
    """
    sources = list_sources(registry_path=registry_path)
    results: list[RepoTaskFitResult] = []
    for c in sources:
        res = _score_candidate(c, query)
        results.append(res)
    results.sort(key=lambda r: r.fit_score, reverse=True)
    return results[:top_k]


def _score_candidate(c: ExternalSourceCandidate, query: RepoTaskFitQuery) -> RepoTaskFitResult:
    """Compute fit/safety/maintenance/license scores and rationale."""
    role_match = 0.0
    workflow_match = 0.0
    pain_match = 0.0
    safety = 0.0
    maintenance = 0.0
    license_score = 0.0
    rationale_parts: list[str] = []

    role_lower = query.role.lower() if query.role else ""
    workflow_lower = query.workflow_type.lower() if query.workflow_type else ""
    desc = (c.description + " " + c.notes + " " + c.recommended_role).lower()
    layers = [p.lower() for p in c.product_layers]

    if role_lower and (role_lower in desc or role_lower in layers or c.recommended_role and role_lower in c.recommended_role.lower()):
        role_match = 0.8
        rationale_parts.append("role match")
    elif c.recommended_role:
        role_match = 0.3
    if workflow_lower and (workflow_lower in desc or workflow_lower in layers):
        workflow_match = 0.8
        rationale_parts.append("workflow match")
    elif "workflow" in desc or "trial" in layers:
        workflow_match = 0.4
    if query.pain_points:
        for pp in query.pain_points:
            if pp.lower() in desc or pp.lower() in c.notes.lower():
                pain_match = min(1.0, pain_match + 0.3)
                rationale_parts.append("pain point")
                break

    if c.safety_risk_level == "low":
        safety = 1.0
    elif c.safety_risk_level == "medium":
        safety = 0.5
    elif c.safety_risk_level == "high":
        safety = 0.0
    else:
        safety = 0.3
    if c.maintainer_signal == "active":
        maintenance = 1.0
    elif c.maintainer_signal == "stale":
        maintenance = 0.3
    else:
        maintenance = 0.5
    if c.license and ("mit" in c.license.lower() or "apache" in c.license.lower() or "bsd" in c.license.lower()):
        license_score = 1.0
    elif c.license:
        license_score = 0.5
    else:
        license_score = 0.2

    if query.local_first_required and c.local_runtime_fit == "high":
        rationale_parts.append("local-first fit")
    if query.UI_need and c.recommended_role == "dashboard_ui":
        role_match = max(role_match, 0.7)
        rationale_parts.append("UI fit")
    if query.parsing_need and c.recommended_role == "parser":
        role_match = max(role_match, 0.7)
        rationale_parts.append("parsing fit")
    if query.orchestration_need and c.recommended_role == "agent_orchestrator":
        role_match = max(role_match, 0.8)
        rationale_parts.append("orchestration fit")
    if query.proxy_need and c.recommended_role == "network_proxy":
        role_match = max(role_match, 0.7)
        rationale_parts.append("proxy fit")
    if query.model_need and c.recommended_role == "agent_runtime":
        role_match = max(role_match, 0.6)

    if c.unresolved_reason:
        safety *= 0.7
        rationale_parts.append("unresolved")

    fit_score = 0.4 * (role_match + workflow_match) / 2 + 0.2 * pain_match + 0.2 * safety + 0.1 * maintenance + 0.1 * license_score
    rationale = "; ".join(rationale_parts) if rationale_parts else "no strong match"

    return RepoTaskFitResult(
        source_id=c.source_id,
        fit_score=round(fit_score, 3),
        role_match_score=round(role_match, 3),
        workflow_match_score=round(workflow_match, 3),
        pain_point_match_score=round(pain_match, 3),
        safety_score=round(safety, 3),
        maintenance_score=round(maintenance, 3),
        license_score=round(license_score, 3),
        adoption_recommendation=c.adoption_recommendation or "",
        rationale=rationale,
    )
