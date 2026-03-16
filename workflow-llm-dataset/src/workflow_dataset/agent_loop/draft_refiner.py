"""
Draft refiner: refine draft structures using project context, style profiles, and retrieval.

Two modes:
  A. Deterministic: rule/template-based, always available.
  B. Optional local LLM: only when configured; grounded in retrieved context; no fabrication.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from workflow_dataset.agent_loop.agent_models import AgentResponse
from workflow_dataset.personal.assistive_models import DraftStructure
from workflow_dataset.personal.draft_structure_engine import DRAFT_TEMPLATES
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def _refine_deterministic(
    draft: DraftStructure | dict[str, Any],
    context_bundle: dict[str, Any],
) -> tuple[str, list[str], float]:
    """
    Refine outline/sections using project naming, style patterns, and artifact families.
    Returns (refined_outline, evidence_list, confidence).
    """
    if isinstance(draft, DraftStructure):
        outline = draft.structure_outline or ""
        domain = draft.domain or ""
        draft_type = draft.draft_type or ""
        sections = list(draft.recommended_sections or [])
        naming = list(draft.suggested_naming or [])
    else:
        outline = draft.get("structure_outline") or draft.get("outline") or ""
        domain = draft.get("domain") or ""
        draft_type = draft.get("draft_type") or ""
        sections = list(draft.get("recommended_sections") or draft.get("sections") or [])
        naming = list(draft.get("suggested_naming") or draft.get("naming") or [])

    evidence: list[str] = []
    refined = outline

    # Inject project-specific naming hints from style context
    style_ctx = context_bundle.get("style_context") or {}
    profiles = style_ctx.get("profiles") or []
    naming_patterns: list[str] = []
    for p in profiles[:5]:
        np = p.get("naming_patterns") or []
        naming_patterns.extend(np[:3])
    if naming_patterns:
        unique = list(dict.fromkeys(naming_patterns))[:5]
        hint_line = "\n\n*Naming (from your style): " + ", ".join(unique) + "*"
        if hint_line not in refined:
            refined = refined.rstrip() + hint_line
        evidence.append("Naming patterns from style profiles")

    # Section headers: if we have parsed artifact titles, optionally add a "References" or "Source docs" section
    project_ctx = context_bundle.get("project_context") or {}
    parsed = project_ctx.get("parsed_artifacts") or []
    if parsed and "References" not in refined and "Source" not in refined:
        if draft_type in ("project_brief", "planning_memo", "sop_outline"):
            refined = refined.rstrip() + "\n## References\n"
            evidence.append("Added References section from parsed artifacts")
    if parsed:
        evidence.append(f"Aligned with {len(parsed)} parsed artifacts")

    # Domain-specific tweaks
    if domain == "creative" and "revision" not in refined.lower():
        rev_note = "\n\n*Revision stages: draft → review → final → archive (match your naming convention)*"
        if rev_note.strip() not in refined:
            refined = refined.rstrip() + rev_note
        evidence.append("Creative revision convention note")
    if domain in ("finance", "ops") and "recon" in draft_type.lower():
        refined = refined.rstrip() + "\n\n*Match criteria and sign-off per your reconciliation workflow.*"
        evidence.append("Finance/ops reconciliation note")

    confidence = min(0.9, 0.5 + 0.05 * len(evidence) + (0.1 if naming_patterns else 0))
    return refined, evidence, confidence


def refine_draft(
    context_bundle: dict[str, Any],
    draft_id: str = "",
    draft_type: str = "",
    project_id: str = "",
    use_llm: bool = False,
    llm_refine_fn: Any = None,
) -> tuple[DraftStructure | dict[str, Any], AgentResponse]:
    """
    Refine a draft structure using context. Returns (refined_draft_or_dict, explanation_response).

    If draft_id is set, load from draft_context. Else if draft_type is set, use template.
    use_llm and llm_refine_fn: optional local LLM refinement; must stay grounded (no fabrication).
    """
    response_id = stable_id("resp", "refine_draft", draft_id or draft_type or "default", utc_now_iso(), prefix="resp")
    draft_ctx = context_bundle.get("draft_context") or {}
    drafts = draft_ctx.get("drafts") or []

    draft_obj: DraftStructure | dict[str, Any] | None = None
    if draft_id:
        for d in drafts:
            if d.get("draft_id") == draft_id:
                draft_obj = d
                break
    if not draft_obj and draft_type:
        if draft_type in DRAFT_TEMPLATES:
            t = DRAFT_TEMPLATES[draft_type]
            draft_obj = {
                "draft_id": stable_id("draft", draft_type, project_id or "default", prefix="draft"),
                "draft_type": draft_type,
                "domain": t.get("domain", "general"),
                "title": t.get("title", draft_type),
                "structure_outline": t.get("outline", ""),
                "recommended_sections": t.get("sections", []),
                "suggested_naming": t.get("naming", []),
            }
        else:
            # Try to find first draft of this type in context
            for d in drafts:
                if d.get("draft_type") == draft_type:
                    draft_obj = d
                    break
    if not draft_obj and drafts:
        draft_obj = drafts[0]

    if not draft_obj:
        return {}, AgentResponse(
            response_id=response_id,
            response_type="refine_draft",
            title="Draft refinement",
            answer="No draft structure found to refine. Specify draft_id or draft_type, or run 'assist draft' first.",
            supporting_evidence=[],
            draft_refs=[],
            confidence_score=0.0,
            used_retrieval=bool(context_bundle.get("retrieved_docs")),
            used_llm=False,
            created_utc=utc_now_iso(),
        )

    # Deterministic refinement
    refined_outline, evidence_list, confidence = _refine_deterministic(draft_obj, context_bundle)

    used_llm = False
    if use_llm and llm_refine_fn and context_bundle.get("retrieved_text"):
        try:
            # Optional: call LLM with strict prompt to only refine wording, not add new facts
            result = llm_refine_fn(
                draft_outline=refined_outline,
                context_snippet=context_bundle.get("retrieved_text", "")[:2000],
                domain=draft_obj.get("domain") if isinstance(draft_obj, dict) else getattr(draft_obj, "domain", ""),
            )
            if result and isinstance(result, str) and len(result) > len(refined_outline):
                refined_outline = result
                evidence_list.append("Local LLM used for wording refinement (grounded in retrieval)")
                used_llm = True
        except Exception:
            pass

    # Build refined structure (dict for simplicity; could return DraftStructure)
    if isinstance(draft_obj, DraftStructure):
        refined_draft = DraftStructure(
            draft_id=draft_obj.draft_id,
            draft_type=draft_obj.draft_type,
            project_id=project_id or draft_obj.project_id,
            domain=draft_obj.domain,
            title=draft_obj.title,
            structure_outline=refined_outline,
            recommended_sections=draft_obj.recommended_sections,
            suggested_naming=draft_obj.suggested_naming,
            suggested_assets_or_tables=draft_obj.suggested_assets_or_tables,
            style_profile_refs=draft_obj.style_profile_refs,
            confidence_score=confidence,
            created_utc=draft_obj.created_utc,
        )
    else:
        refined_draft = dict(draft_obj)
        refined_draft["structure_outline"] = refined_outline
        refined_draft["confidence_score"] = confidence

    answer = (
        f"Refined draft structure (deterministic{' + local LLM' if used_llm else ''}): "
        f"outline updated with naming hints and domain-specific notes. Evidence: {'; '.join(evidence_list)}."
    )

    resp = AgentResponse(
        response_id=response_id,
        response_type="refine_draft",
        title="Draft refinement",
        answer=answer,
        supporting_evidence=evidence_list,
        draft_refs=[draft_obj.get("draft_id") if isinstance(draft_obj, dict) else draft_obj.draft_id],
        style_profile_refs=(
            (draft_obj.get("style_profile_refs") or []) if isinstance(draft_obj, dict) else (getattr(draft_obj, "style_profile_refs", None) or [])
        ),
        retrieved_context_refs=[d.doc_id for d in (context_bundle.get("retrieved_docs") or [])],
        confidence_score=confidence,
        used_retrieval=bool(context_bundle.get("retrieved_docs")),
        used_llm=used_llm,
        created_utc=utc_now_iso(),
    )
    return refined_draft, resp
