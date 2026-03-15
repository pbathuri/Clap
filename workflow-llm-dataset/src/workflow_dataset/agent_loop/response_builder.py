"""
Retrieval-backed response builder for the assistive agent loop.

Supports: graph-only, retrieval-only, graph+retrieval, graph+retrieval+optional LLM.
Default: graph + retrieval; local LLM only when configured.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from workflow_dataset.agent_loop.agent_models import AgentQuery, AgentResponse
from workflow_dataset.agent_loop.context_builder import build_context_bundle
from workflow_dataset.agent_loop.query_router import QueryType, route_query
from workflow_dataset.agent_loop.explain_engine import (
    explain_project,
    explain_style,
    explain_suggestion,
    explain_draft,
    explain_domain_evidence,
)
from workflow_dataset.agent_loop.next_step_engine import suggest_next_steps
from workflow_dataset.agent_loop.draft_refiner import refine_draft
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def build_response(
    query: AgentQuery,
    graph_path: Path | str,
    style_signals_dir: Path | str,
    parsed_artifacts_dir: Path | str,
    style_profiles_dir: Path | str,
    suggestions_dir: Path | str,
    draft_structures_dir: Path | str,
    setup_session_id: str = "",
    corpus_path: Path | str | None = None,
    max_retrieval_docs: int = 5,
    use_llm: bool = False,
    llm_refine_fn: Callable[..., str] | None = None,
) -> AgentResponse:
    """
    Route the query, build context, and produce a grounded response.
    Response always includes evidence refs, sources used, used_retrieval, used_llm.
    """
    project_id = query.project_id or ""
    domain_filter = query.domain or ""
    user_text = query.user_text or ""
    requested_mode = query.requested_mode or ""

    # Route
    qtype, route_extras = route_query(user_text, requested_mode)

    # Context (graph + optional retrieval)
    context_bundle = build_context_bundle(
        graph_path=graph_path,
        style_signals_dir=style_signals_dir,
        parsed_artifacts_dir=parsed_artifacts_dir,
        style_profiles_dir=style_profiles_dir,
        suggestions_dir=suggestions_dir,
        draft_structures_dir=draft_structures_dir,
        setup_session_id=setup_session_id,
        project_id=project_id,
        domain_filter=domain_filter,
        corpus_path=corpus_path,
        query=user_text,
        max_retrieval_docs=max_retrieval_docs,
    )

    # Build response by type
    if qtype == QueryType.EXPLAIN_PROJECT:
        if route_extras.get("matched") == "domain_evidence":
            resp = explain_domain_evidence(context_bundle, project_id)
        else:
            resp = explain_project(context_bundle, project_id)
    elif qtype == QueryType.EXPLAIN_STYLE:
        resp = explain_style(context_bundle, project_id)
    elif qtype == QueryType.EXPLAIN_SUGGESTION:
        suggestion_id = route_extras.get("hint_id") or ""
        resp = explain_suggestion(context_bundle, suggestion_id=suggestion_id, project_id=project_id)
    elif qtype == QueryType.EXPLAIN_DRAFT:
        draft_id = route_extras.get("hint_id") or ""
        resp = explain_draft(context_bundle, draft_id=draft_id, project_id=project_id)
    elif qtype == QueryType.SUGGEST_NEXT_STEP:
        resp = suggest_next_steps(context_bundle, project_id)
    elif qtype == QueryType.REFINE_DRAFT_STRUCTURE:
        draft_id = route_extras.get("hint_id") or ""
        draft_type = route_extras.get("draft_type") or ""
        _, resp = refine_draft(
            context_bundle,
            draft_id=draft_id,
            draft_type=draft_type,
            project_id=project_id,
            use_llm=use_llm,
            llm_refine_fn=llm_refine_fn,
        )
    elif qtype in (
        QueryType.SUMMARIZE_PROJECT_PATTERNS,
        QueryType.SUMMARIZE_WORKFLOW_PATTERNS,
    ):
        # Reuse explain_project / workflow context
        resp = explain_project(context_bundle, project_id)
        resp.response_type = qtype.value
        resp.title = "Project and workflow patterns" if "project" in qtype.value else "Workflow patterns"
    elif qtype == QueryType.LIST_ACTIVE_PROJECTS:
        resp = explain_project(context_bundle, project_id)
        resp.response_type = "list_active_projects"
        resp.title = "Active projects"
    elif qtype in (
        QueryType.CREATIVE_SCAFFOLD_HELP,
        QueryType.FINANCE_OPS_SCAFFOLD_HELP,
        QueryType.FOUNDER_ADMIN_SCAFFOLD_HELP,
    ):
        # Next-step style with domain focus
        resp = suggest_next_steps(context_bundle, project_id)
        resp.response_type = qtype.value
        resp.title = "Scaffold help: " + qtype.value.replace("_", " ").title()
    else:
        # GENERAL_CHAT: combine project + style summary as answer
        rp = explain_project(context_bundle, project_id)
        rs = explain_style(context_bundle, project_id)
        answer = rp.answer
        if rs.answer and "No style" not in rs.answer:
            answer += " " + rs.answer
        resp = AgentResponse(
            response_id=stable_id("resp", "chat", query.query_id, utc_now_iso(), prefix="resp"),
            query_id=query.query_id,
            response_type="general_chat",
            title="Summary",
            answer=answer or "No context available yet. Run setup and assist suggest/draft, then ask again.",
            supporting_evidence=rp.supporting_evidence + rs.supporting_evidence,
            retrieved_context_refs=rp.retrieved_context_refs + rs.retrieved_context_refs,
            graph_refs=rp.graph_refs,
            style_profile_refs=rs.style_profile_refs,
            confidence_score=(rp.confidence_score + rs.confidence_score) / 2,
            used_retrieval=rp.used_retrieval or rs.used_retrieval,
            used_llm=False,
            created_utc=utc_now_iso(),
        )

    resp.query_id = query.query_id
    return resp
