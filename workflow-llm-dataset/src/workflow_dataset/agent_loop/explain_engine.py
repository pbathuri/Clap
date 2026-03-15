"""
Explain engine: answer project-, style-, suggestion-, and draft-aware questions.

All answers include rationale, evidence references, and confidence.
Explicit statement when evidence is weak.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.agent_loop.agent_models import AgentResponse
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def explain_project(context_bundle: dict[str, Any], project_id: str = "") -> AgentResponse:
    """
    Answer: what is this project? what evidence supports domain classification?
    """
    response_id = stable_id("resp", "explain_project", project_id or "all", utc_now_iso(), prefix="resp")
    projects = (context_bundle.get("project_context") or {}).get("projects") or []
    parsed = (context_bundle.get("project_context") or {}).get("parsed_artifacts") or []
    domains = (context_bundle.get("project_context") or {}).get("domains") or []

    if not projects and not parsed:
        return AgentResponse(
            response_id=response_id,
            response_type="explain_project",
            title="Project context",
            answer="No project or artifact data is available yet. Run setup (setup init, setup run) and optionally assist suggest / assist draft to populate the graph and parsed artifacts.",
            supporting_evidence=[],
            graph_refs=[],
            confidence_score=0.0,
            used_retrieval=bool(context_bundle.get("retrieved_docs")),
            used_llm=False,
            created_utc=utc_now_iso(),
        )

    lines = []
    evidence: list[str] = []
    graph_refs: list[str] = []

    if projects:
        proj_list = [p.get("label") or p.get("node_id") for p in projects if (p.get("label") or p.get("node_id"))]
        if project_id:
            proj_list = [p for p in proj_list if p == project_id]
        if proj_list:
            lines.append(f"Projects in scope: {', '.join(proj_list[:10])}.")
            graph_refs.extend([p.get("node_id", "") for p in projects[:10] if p.get("node_id")])
            evidence.append(f"Graph projects: {len(projects)}")

    if domains:
        domain_list = [d.get("label") or d.get("node_id") for d in domains if (d.get("label") or d.get("node_id"))]
        lines.append(f"Detected domains: {', '.join(domain_list[:10])}.")
        evidence.append(f"Domains: {', '.join(domain_list[:5])}")

    if parsed:
        families: dict[str, int] = {}
        for a in parsed:
            fam = a.get("artifact_family") or "unknown"
            families[fam] = families.get(fam, 0) + 1
        fam_str = ", ".join(f"{k}: {v}" for k, v in sorted(families.items(), key=lambda x: -x[1])[:8])
        lines.append(f"Parsed artifacts by family: {fam_str}.")
        evidence.append(f"Parsed artifacts: {len(parsed)}")

    if context_bundle.get("retrieved_text"):
        lines.append("Retrieved corpus context was used to ground this summary.")
        evidence.append("Retrieval: used")

    if not lines:
        lines.append("Project scope is empty for the given filters.")
        confidence = 0.2
    else:
        confidence = min(0.95, 0.5 + 0.1 * (len(projects) + len(domains) + min(1, len(parsed) // 5)))

    return AgentResponse(
        response_id=response_id,
        response_type="explain_project",
        title="Project context",
        answer=" ".join(lines),
        supporting_evidence=evidence,
        graph_refs=graph_refs,
        retrieved_context_refs=[d.doc_id for d in (context_bundle.get("retrieved_docs") or [])],
        confidence_score=confidence,
        used_retrieval=bool(context_bundle.get("retrieved_docs")),
        used_llm=False,
        created_utc=utc_now_iso(),
    )


def explain_style(context_bundle: dict[str, Any], project_id: str = "") -> AgentResponse:
    """Answer: what style pattern did you detect? why this naming/folder style?"""
    response_id = stable_id("resp", "explain_style", project_id or "all", utc_now_iso(), prefix="resp")
    style_ctx = context_bundle.get("style_context") or {}
    profiles = style_ctx.get("profiles") or []
    signals = style_ctx.get("style_signals") or []
    candidates = style_ctx.get("imitation_candidates") or []

    if not profiles and not signals:
        return AgentResponse(
            response_id=response_id,
            response_type="explain_style",
            title="Style patterns",
            answer="No style profiles or signals are available yet. Run setup with style extraction enabled, then assist suggest to build style profiles from your artifacts.",
            supporting_evidence=[],
            style_profile_refs=[],
            confidence_score=0.0,
            used_retrieval=bool(context_bundle.get("retrieved_docs")),
            used_llm=False,
            created_utc=utc_now_iso(),
        )

    lines = []
    evidence: list[str] = []
    profile_refs: list[str] = []

    if signals:
        types = set(s.get("pattern_type") for s in signals if s.get("pattern_type"))
        lines.append(f"Style signals detected: {', '.join(sorted(types)[:10])}.")
        evidence.append(f"Style signals: {len(signals)}")

    for p in profiles[:5]:
        pid = p.get("profile_id", "")
        if pid:
            profile_refs.append(pid)
        ptype = p.get("profile_type", "")
        domain = p.get("domain", "")
        naming = p.get("naming_patterns") or []
        folder = p.get("folder_patterns") or []
        if ptype == "naming_style" and naming:
            lines.append(f"Naming style ({domain}): patterns like {', '.join(naming[:5])}.")
        elif ptype == "folder_structure_style" and folder:
            lines.append(f"Folder structure style: {', '.join(folder[:3])}.")

    if candidates:
        lines.append(f"{len(candidates)} imitation candidate(s) derived from these profiles.")
        evidence.append(f"Imitation candidates: {len(candidates)}")

    if not lines:
        lines.append("Style data is present but could not be summarized; evidence may be weak.")
        confidence = 0.3
    else:
        confidence = min(0.9, 0.4 + 0.1 * (len(profiles) + min(1, len(signals) // 5)))

    return AgentResponse(
        response_id=response_id,
        response_type="explain_style",
        title="Style patterns",
        answer=" ".join(lines),
        supporting_evidence=evidence,
        style_profile_refs=profile_refs,
        retrieved_context_refs=[d.doc_id for d in (context_bundle.get("retrieved_docs") or [])],
        confidence_score=confidence,
        used_retrieval=bool(context_bundle.get("retrieved_docs")),
        used_llm=False,
        created_utc=utc_now_iso(),
    )


def explain_suggestion(
    context_bundle: dict[str, Any],
    suggestion_id: str = "",
    project_id: str = "",
) -> AgentResponse:
    """Answer: why did you suggest this? what evidence supports this suggestion?"""
    response_id = stable_id("resp", "explain_suggestion", suggestion_id or "any", utc_now_iso(), prefix="resp")
    sug_ctx = context_bundle.get("suggestion_context") or {}
    suggestions = sug_ctx.get("suggestions") or []

    if suggestion_id:
        suggestions = [s for s in suggestions if s.get("suggestion_id") == suggestion_id]
    if project_id:
        suggestions = [s for s in suggestions if s.get("project_id") == project_id]

    if not suggestions:
        return AgentResponse(
            response_id=response_id,
            response_type="explain_suggestion",
            title="Suggestion explanation",
            answer="No matching suggestion found. Run 'assist suggest' to generate style-aware suggestions, or specify a suggestion ID / project.",
            supporting_evidence=[],
            suggestion_refs=[],
            confidence_score=0.0,
            used_retrieval=bool(context_bundle.get("retrieved_docs")),
            used_llm=False,
            created_utc=utc_now_iso(),
        )

    s = suggestions[0]
    sid = s.get("suggestion_id", "")
    title = s.get("title", "Suggestion")
    rationale = s.get("rationale", "")
    sug_type = s.get("suggestion_type", "")
    confidence = float(s.get("confidence_score", 0.5))
    signals = s.get("supporting_signals") or []
    if isinstance(signals, list) and signals and isinstance(signals[0], dict):
        signals = [str(x) for x in signals[:5]]
    else:
        signals = [str(x) for x in signals[:5]]

    answer = f"{title} ({sug_type}). Rationale: {rationale}"
    if signals:
        answer += f" Supporting signals: {', '.join(signals)}."

    return AgentResponse(
        response_id=response_id,
        response_type="explain_suggestion",
        title=title,
        answer=answer,
        supporting_evidence=signals,
        suggestion_refs=[sid] if sid else [],
        style_profile_refs=s.get("style_profile_refs") or [],
        confidence_score=confidence,
        used_retrieval=bool(context_bundle.get("retrieved_docs")),
        used_llm=False,
        created_utc=utc_now_iso(),
    )


def explain_draft(
    context_bundle: dict[str, Any],
    draft_id: str = "",
    project_id: str = "",
) -> AgentResponse:
    """Answer: why is this draft structure appropriate? what evidence supports it?"""
    response_id = stable_id("resp", "explain_draft", draft_id or "any", utc_now_iso(), prefix="resp")
    draft_ctx = context_bundle.get("draft_context") or {}
    drafts = draft_ctx.get("drafts") or []

    if draft_id:
        drafts = [d for d in drafts if d.get("draft_id") == draft_id]
    if project_id:
        drafts = [d for d in drafts if d.get("project_id") == project_id]

    if not drafts:
        return AgentResponse(
            response_id=response_id,
            response_type="explain_draft",
            title="Draft structure explanation",
            answer="No matching draft structure found. Run 'assist draft' to generate draft structures from your project and domain, or specify a draft ID / project.",
            supporting_evidence=[],
            draft_refs=[],
            confidence_score=0.0,
            used_retrieval=bool(context_bundle.get("retrieved_docs")),
            used_llm=False,
            created_utc=utc_now_iso(),
        )

    d = drafts[0]
    did = d.get("draft_id", "")
    title = d.get("title", "Draft")
    domain = d.get("domain", "")
    draft_type = d.get("draft_type", "")

    workflow_ctx = context_bundle.get("workflow_context") or {}
    families = workflow_ctx.get("artifact_families") or []
    domains_list = workflow_ctx.get("domains") or []

    evidence_list = [f"Domain: {domain}", f"Type: {draft_type}"]
    if families:
        evidence_list.append(f"Artifact families in workflow: {', '.join(list(families)[:5])}")
    if domains_list:
        evidence_list.append("Draft domain aligned with detected workflow domains.")

    answer = (
        f"{title} is appropriate because it matches the detected domain ({domain}) and draft type {draft_type}. "
        "It was generated from your setup outputs and style profiles so that sections and naming follow "
        "reusable patterns. Evidence: " + "; ".join(evidence_list) + "."
    )

    return AgentResponse(
        response_id=response_id,
        response_type="explain_draft",
        title=title,
        answer=answer,
        supporting_evidence=evidence_list,
        draft_refs=[did] if did else [],
        confidence_score=float(d.get("confidence_score", 0.75)),
        used_retrieval=bool(context_bundle.get("retrieved_docs")),
        used_llm=False,
        created_utc=utc_now_iso(),
    )


def explain_domain_evidence(context_bundle: dict[str, Any], project_id: str = "") -> AgentResponse:
    """Answer: what evidence supports this domain classification? (delegates to explain_project with domain focus.)"""
    r = explain_project(context_bundle, project_id)
    r.response_type = "explain_domain_evidence"
    r.title = "Domain classification evidence"
    return r
