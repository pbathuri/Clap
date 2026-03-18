"""
Build prompt packs for image, keyframe, storyboard, report narrative, etc.

Structured prompts and constraints; style-pack aware. Scaffolding only.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id

from workflow_dataset.generate.generate_models import PromptPack, StylePack


def build_prompt_pack(
    generation_id: str,
    prompt_family: str,
    context: dict[str, Any],
    style_pack: StylePack | None = None,
    draft_ref: str = "",
    suggestion_ref: str = "",
) -> PromptPack:
    """
    Build a PromptPack for a given family (image, keyframe, storyboard, report_narrative, etc.).
    Uses context and optional style_pack; no fabricated visual detail.
    """
    ts = utc_now_iso()
    pack_id = stable_id("promptpack", generation_id, prompt_family, ts, prefix="pp")

    # Base structural constraints from context
    structural_constraints: list[str] = []
    summary = context.get("summary") or {}
    draft_types = summary.get("draft_types") or []
    artifact_families = summary.get("artifact_families") or []
    if draft_types:
        structural_constraints.append(f"Align with draft types: {', '.join(draft_types[:5])}")
    if artifact_families:
        structural_constraints.append(f"Artifact families: {', '.join(artifact_families[:5])}")

    if style_pack:
        if style_pack.naming_patterns:
            structural_constraints.append(f"Naming conventions: {', '.join(style_pack.naming_patterns[:3])}")
        if style_pack.export_patterns:
            structural_constraints.append(f"Export patterns: {', '.join(style_pack.export_patterns[:3])}")
    style_pack_refs = [style_pack.style_pack_id] if style_pack else []

    # Prompt text: domain- and family-specific scaffold (no fabricated imagery)
    prompt_text = _default_prompt_text(prompt_family, context, style_pack)
    negative_constraints = ["Do not fabricate specific visual details without evidence"]

    return PromptPack(
        prompt_pack_id=pack_id,
        generation_id=generation_id,
        prompt_family=prompt_family,
        prompt_text=prompt_text,
        negative_constraints=negative_constraints,
        structural_constraints=structural_constraints[:10],
        style_pack_refs=style_pack_refs,
        created_utc=ts,
    )


def _default_prompt_text(
    prompt_family: str,
    context: dict[str, Any],
    style_pack: StylePack | None,
) -> str:
    """Default prompt text scaffold by family. Evidence-based only."""
    domain = context.get("domain_filter") or (style_pack.domain if style_pack else "")
    projects = context.get("projects") or []
    project_labels = [p.get("label", p.get("node_id", "")) for p in projects[:3] if p.get("label") or p.get("node_id")]

    if prompt_family == "image":
        return (
            f"Generate image concepts consistent with project context: {', '.join(project_labels) or 'general'}.\n"
            "Use observed naming and export patterns. Stay within evidence-based style hints."
        )
    if prompt_family == "keyframe":
        return (
            f"Keyframe or key visual for sequence; project context: {', '.join(project_labels) or 'general'}.\n"
            "Match deliverable shapes and revision patterns from style pack."
        )
    if prompt_family == "storyboard":
        return (
            f"Storyboard sequence for project: {', '.join(project_labels) or 'general'}.\n"
            "Sections and layout should follow observed structure patterns."
        )
    if prompt_family == "report_narrative":
        return (
            f"Report or document narrative outline; domain: {domain or 'general'}.\n"
            "Structure and tone consistent with observed document and export patterns."
        )
    if prompt_family == "presentation":
        return (
            f"Presentation narrative; project: {', '.join(project_labels) or 'general'}.\n"
            "Slide/section flow aligned with deliverable shapes and naming conventions."
        )
    # Generic
    return (
        f"Generation prompt for family '{prompt_family}'; domain: {domain or 'general'}.\n"
        f"Project context: {', '.join(project_labels) or 'none'}. Use style pack constraints where available."
    )
