"""
Assemble structured generation context from setup, graph, style, drafts, and materialization.

Used by style pack, prompt pack, and asset plan builders. Structured and inspectable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.personal.project_interpreter import get_assistive_context
from workflow_dataset.personal.style_profiles import load_style_profiles
from workflow_dataset.personal.imitation_candidates import collect_candidates_from_profiles
from workflow_dataset.personal.style_suggestion_engine import load_style_aware_suggestions
from workflow_dataset.personal.draft_structure_engine import load_draft_structures


def build_generation_context(
    graph_path: Path | str,
    style_signals_dir: Path | str,
    parsed_artifacts_dir: Path | str,
    style_profiles_dir: Path | str,
    suggestions_dir: Path | str,
    draft_structures_dir: Path | str,
    setup_session_id: str = "",
    project_id: str = "",
    domain_filter: str = "",
) -> dict[str, Any]:
    """
    Build structured context suitable for image prompt packs, shot planning,
    design variant planning, and asset package planning.
    Returns dict with: projects, domains, style_signals, parsed_artifacts,
    style_profiles, imitation_candidates, suggestions, drafts, summary.
    """
    assistive = get_assistive_context(
        graph_path,
        style_signals_dir,
        parsed_artifacts_dir,
        setup_session_id,
    )
    projects = assistive.get("projects") or []
    domains = assistive.get("domains") or []
    style_signals = assistive.get("style_signals") or []
    parsed = assistive.get("parsed_artifacts") or []

    if project_id:
        projects = [p for p in projects if p.get("label") == project_id or p.get("node_id") == project_id]
        parsed = [a for a in parsed if project_id in (a.get("source_path") or "")]
    if domain_filter:
        domains = [d for d in domains if (d.get("label") or "").lower() == domain_filter.lower()]

    profiles = load_style_profiles(style_profiles_dir) if Path(style_profiles_dir).exists() else []
    if project_id:
        profiles = [
            p for p in profiles
            if getattr(p, "project_id", "") == project_id
            or (getattr(p, "project_paths", []) and project_id in str(getattr(p, "project_paths", [])))
        ]
    candidates = collect_candidates_from_profiles(style_profiles_dir) if Path(style_profiles_dir).exists() else []
    suggestions = load_style_aware_suggestions(suggestions_dir) if Path(suggestions_dir).exists() else []
    if project_id:
        suggestions = [s for s in suggestions if getattr(s, "project_id", "") == project_id]
    drafts = load_draft_structures(draft_structures_dir) if Path(draft_structures_dir).exists() else []
    if project_id:
        drafts = [d for d in drafts if getattr(d, "project_id", "") == project_id]
    if domain_filter:
        drafts = [d for d in drafts if (getattr(d, "domain", "") or "").lower() == domain_filter.lower()]

    # Summaries for generation builders
    artifact_families = list({a.get("artifact_family") for a in parsed if a.get("artifact_family")})
    profile_types = list({getattr(p, "profile_type", "") for p in profiles if getattr(p, "profile_type", "")})
    candidate_types = list({getattr(c, "candidate_type", "") for c in candidates if getattr(c, "candidate_type", "")})
    draft_types = list({getattr(d, "draft_type", "") for d in drafts if getattr(d, "draft_type", "")})

    return {
        "projects": projects,
        "domains": domains,
        "style_signals": style_signals,
        "parsed_artifacts": parsed,
        "style_profiles": profiles,
        "imitation_candidates": candidates,
        "suggestions": suggestions,
        "drafts": drafts,
        "setup_session_id": setup_session_id,
        "project_id": project_id,
        "domain_filter": domain_filter,
        "summary": {
            "artifact_families": artifact_families,
            "profile_types": profile_types,
            "candidate_types": candidate_types,
            "draft_types": draft_types,
            "n_projects": len(projects),
            "n_profiles": len(profiles),
            "n_candidates": len(candidates),
            "n_drafts": len(drafts),
            "n_suggestions": len(suggestions),
        },
    }
