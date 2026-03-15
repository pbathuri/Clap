"""
Next-step engine: suggest sensible next steps from graph/setup/style evidence.

Answers: what should I do next? what to prepare? what missing artifact? what reusable structure?
All outputs include rationale, evidence references, confidence, and weak-evidence disclaimer when needed.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.agent_loop.agent_models import AgentResponse
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def suggest_next_steps(context_bundle: dict[str, Any], project_id: str = "") -> AgentResponse:
    """
    Propose next-step guidance from current project/style/workflow evidence.
    """
    response_id = stable_id("resp", "next_step", project_id or "default", utc_now_iso(), prefix="resp")
    project_ctx = context_bundle.get("project_context") or {}
    workflow_ctx = context_bundle.get("workflow_context") or {}
    suggestion_ctx = context_bundle.get("suggestion_context") or {}
    draft_ctx = context_bundle.get("draft_context") or {}

    projects = project_ctx.get("projects") or []
    parsed = project_ctx.get("parsed_artifacts") or []
    domains = workflow_ctx.get("domains") or []
    families = list(workflow_ctx.get("artifact_families") or [])
    suggestions = suggestion_ctx.get("suggestions") or []
    drafts = draft_ctx.get("drafts") or []

    steps: list[str] = []
    evidence: list[str] = []
    suggestion_refs: list[str] = []
    draft_refs: list[str] = []
    confidence = 0.5

    # 1) If we have pending suggestions, recommend acting on the top one
    if suggestions:
        s = suggestions[0]
        steps.append(f"Consider: {s.get('title', '')} — {s.get('rationale', '')[:120]}.")
        suggestion_refs.append(s.get("suggestion_id", ""))
        evidence.append("Style-aware suggestion")
        confidence = max(confidence, float(s.get("confidence_score", 0.6)))

    # 2) If we have drafts but few parsed artifacts, recommend creating from a draft
    if drafts and len(parsed) < 5:
        d = drafts[0]
        steps.append(
            f"Create a new artifact using the '{d.get('title', '')}' draft structure; "
            "it matches your detected domain and can be refined with your style."
        )
        draft_refs.append(d.get("draft_id", ""))
        evidence.append(f"Draft: {d.get('draft_type', '')}")
        confidence = max(confidence, 0.65)

    # 3) Workflow-based: recurring reporting -> suggest report outline or reconciliation
    if "spreadsheet_table" in families or "tabular" in str(families):
        steps.append(
            "Your workflow suggests recurring reporting. Next step: use the operations report outline "
            "or monthly reporting workbook draft, or run a reconciliation checklist if you have multiple sources."
        )
        evidence.append("Artifact families: spreadsheet/tabular")
        confidence = max(confidence, 0.6)

    # 4) Creative/text documents -> creative brief or export scaffold
    if "text_document" in families or any("creative" in str(d.get("label", "")) for d in domains):
        steps.append(
            "Creative or document workflow detected. Next step: use the creative brief outline or "
            "export package scaffold, then align naming with your revision pattern."
        )
        evidence.append("Domain/artifacts: creative or text_document")
        confidence = max(confidence, 0.6)

    # 5) Multiple projects -> template formalization
    if len(projects) >= 2:
        steps.append(
            "You have multiple projects; consider formalizing project structure as a reusable template "
            "(see organization suggestion if available)."
        )
        evidence.append(f"Projects: {len(projects)}")
        confidence = max(confidence, 0.55)

    # 6) Weak evidence fallback
    if not steps:
        steps.append(
            "Not enough project or workflow evidence yet to recommend a specific next step. "
            "Run setup (setup init, setup run), then assist suggest and assist draft to populate suggestions and drafts; "
            "then ask again for next-step guidance."
        )
        evidence.append("No strong evidence")
        confidence = 0.2

    answer = " ".join(steps)
    if confidence < 0.5:
        answer += " [Evidence is weak; recommendations are generic.]"

    return AgentResponse(
        response_id=response_id,
        response_type="suggest_next_step",
        title="Next-step guidance",
        answer=answer,
        supporting_evidence=evidence,
        graph_refs=[p.get("node_id", "") for p in projects[:5] if p.get("node_id")],
        suggestion_refs=suggestion_refs,
        draft_refs=draft_refs,
        confidence_score=min(0.95, confidence),
        used_retrieval=bool(context_bundle.get("retrieved_docs")),
        used_llm=False,
        created_utc=utc_now_iso(),
    )
