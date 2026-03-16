"""
Assemble grounded context bundles for the agent loop.

Produces structured project, style, workflow, suggestion, and draft context
from graph, setup outputs, style profiles, suggestions, drafts, and retrieval.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.personal.project_interpreter import get_assistive_context
from workflow_dataset.personal.style_profiles import load_style_profiles
from workflow_dataset.personal.imitation_candidates import collect_candidates_from_profiles
from workflow_dataset.personal.style_suggestion_engine import load_style_aware_suggestions
from workflow_dataset.personal.draft_structure_engine import load_draft_structures
from workflow_dataset.llm.retrieval_context import retrieve, format_context_for_prompt
from workflow_dataset.llm.corpus_builder import load_corpus
from workflow_dataset.llm.schemas import CorpusDocument


def build_context_bundle(
    graph_path: Path | str,
    style_signals_dir: Path | str,
    parsed_artifacts_dir: Path | str,
    style_profiles_dir: Path | str,
    suggestions_dir: Path | str,
    draft_structures_dir: Path | str,
    setup_session_id: str = "",
    project_id: str = "",
    domain_filter: str = "",
    corpus_path: Path | str | None = None,
    query: str = "",
    max_retrieval_docs: int = 5,
) -> dict[str, Any]:
    """
    Build a structured context bundle for the agent.
    Returns dict with: project_context, style_context, workflow_context,
    suggestion_context, draft_context, retrieved_docs, retrieved_text.
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

    # Filter by project if requested
    if project_id:
        projects = [p for p in projects if p.get("label") == project_id or p.get("node_id") == project_id]
        parsed = [a for a in parsed if project_id in (a.get("source_path") or "")]
    if domain_filter:
        domains = [d for d in domains if (d.get("label") or "").lower() == domain_filter.lower()]

    # Style profiles and imitation candidates
    profiles = load_style_profiles(style_profiles_dir) if Path(style_profiles_dir).exists() else []
    if project_id:
        profiles = [p for p in profiles if getattr(p, "project_id", "") == project_id or getattr(p, "project_paths", []) and project_id in str(getattr(p, "project_paths", []))]
    candidates = collect_candidates_from_profiles(style_profiles_dir) if Path(style_profiles_dir).exists() else []
    suggestions = load_style_aware_suggestions(suggestions_dir) if Path(suggestions_dir).exists() else []
    if project_id:
        suggestions = [s for s in suggestions if s.project_id == project_id]
    drafts = load_draft_structures(draft_structures_dir) if Path(draft_structures_dir).exists() else []
    if project_id:
        drafts = [d for d in drafts if d.project_id == project_id]
    if domain_filter:
        drafts = [d for d in drafts if d.domain == domain_filter]

    # Retrieval
    retrieved_docs: list[CorpusDocument] = []
    retrieved_text = ""
    if corpus_path and Path(corpus_path).exists() and query:
        retrieved_docs = retrieve(corpus_path, query, top_k=max_retrieval_docs)
        retrieved_text = format_context_for_prompt(retrieved_docs, max_chars=2500)

    # Structured bundles
    project_context = {
        "projects": [{"node_id": p.get("node_id"), "label": p.get("label")} for p in projects],
        "parsed_artifacts": [{"source_path": a.get("source_path"), "artifact_family": a.get("artifact_family"), "title": a.get("title")} for a in parsed[:30]],
        "domains": [{"node_id": d.get("node_id"), "label": d.get("label")} for d in domains],
    }
    style_context = {
        "style_signals": style_signals[:50],
        "profiles": [{"profile_id": getattr(p, "profile_id", ""), "profile_type": getattr(p, "profile_type", ""), "domain": getattr(p, "domain", ""), "naming_patterns": getattr(p, "naming_patterns", [])[:10]} for p in profiles[:20]],
        "imitation_candidates": [{"candidate_id": getattr(c, "candidate_id", ""), "candidate_type": getattr(c, "candidate_type", ""), "domain": getattr(c, "domain", "")} for c in candidates[:20]],
    }
    workflow_context = {
        "domains": project_context["domains"],
        "artifact_families": list({a.get("artifact_family") for a in parsed if a.get("artifact_family")}),
    }
    suggestion_context = {
        "suggestions": [{"suggestion_id": s.suggestion_id, "suggestion_type": s.suggestion_type, "title": s.title, "rationale": s.rationale[:200]} for s in suggestions[:20]],
    }
    draft_context = {
        "drafts": [{"draft_id": d.draft_id, "draft_type": d.draft_type, "title": d.title, "domain": d.domain} for d in drafts[:20]],
    }

    return {
        "project_context": project_context,
        "style_context": style_context,
        "workflow_context": workflow_context,
        "suggestion_context": suggestion_context,
        "draft_context": draft_context,
        "retrieved_docs": retrieved_docs,
        "retrieved_text": retrieved_text,
        "assistive_raw": assistive,
    }
