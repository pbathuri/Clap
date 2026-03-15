"""
Document/variant backend: generate real markdown artifacts from prompt packs and style context.

M11: deterministic templating; optional LLM refinement is config-gated elsewhere.
Outputs: creative_brief_generated.md, storyboard_plan_generated.md, report_variant_generated.md,
design_brief_generated.md, presentation_narrative_generated.md, architecture_narrative_generated.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.generate.generate_models import (
    GenerationRequest,
    GenerationManifest,
    PromptPack,
    AssetPlan,
    StylePack,
    BackendExecutionRecord,
)
from workflow_dataset.generate.backend_registry import ExecuteResult, UnsupportedFamilyError


# Map prompt_family -> output filename (no path)
_FAMILY_TO_FILENAME: dict[str, str] = {
    "report_narrative": "report_variant_generated.md",
    "storyboard": "storyboard_plan_generated.md",
    "creative_brief": "creative_brief_generated.md",
    "design_brief": "design_brief_generated.md",
    "presentation_narrative": "presentation_narrative_generated.md",
    "architecture_narrative": "architecture_package_plan_narrative_generated.md",
}


def _style_hints(style_packs: list[StylePack]) -> list[str]:
    out: list[str] = []
    for sp in style_packs:
        out.extend(sp.tone_or_visual_hints or [])
        out.extend(sp.deliverable_shapes or [])
    return out[:20]


def _render_document(
    pack: PromptPack,
    style_packs: list[StylePack],
    asset_plans: list[AssetPlan],
) -> str:
    """Produce markdown content from prompt pack and context. Deterministic."""
    lines: list[str] = []
    family = (pack.prompt_family or "document").replace(" ", "_")
    lines.append(f"# {family.replace('_', ' ').title()}\n")
    lines.append(f"*Generated from prompt pack: {pack.prompt_pack_id}*\n")
    if pack.prompt_text:
        lines.append("## Brief / Prompt\n")
        lines.append(pack.prompt_text.strip())
        lines.append("")
    if pack.structural_constraints:
        lines.append("## Structural constraints\n")
        for c in pack.structural_constraints:
            lines.append(f"- {c}")
        lines.append("")
    hints = _style_hints(style_packs)
    if hints:
        lines.append("## Style / deliverable hints\n")
        for h in hints:
            lines.append(f"- {h}")
        lines.append("")
    # Optional: pull shot/scene titles from asset plan for narrative
    for plan in asset_plans:
        if plan.shot_list:
            lines.append("## Shot / sequence outline\n")
            for s in sorted(plan.shot_list, key=lambda x: x.sequence_order):
                lines.append(f"- **{s.title}** (order {s.sequence_order})")
                if s.description:
                    lines.append(f"  {s.description}")
            lines.append("")
            break
    return "\n".join(lines).strip() + "\n"


def execute_document_backend(
    request: GenerationRequest,
    manifest: GenerationManifest,
    workspace_path: Path,
    prompt_packs: list[PromptPack],
    asset_plans: list[AssetPlan],
    style_packs: list[StylePack] | None = None,
    use_llm: bool = False,
    allow_fallback: bool = True,
) -> ExecuteResult:
    """
    Generate document-style markdown files in workspace_path from prompt packs and style.
    Sandbox-only. Deterministic; use_llm is reserved for future optional refinement.
    """
    style_packs = style_packs or []
    workspace_path = Path(workspace_path)
    workspace_path.mkdir(parents=True, exist_ok=True)
    supported = set(_FAMILY_TO_FILENAME)
    doc_packs = [p for p in prompt_packs if p.prompt_family in supported]
    if not doc_packs and prompt_packs:
        families = {p.prompt_family for p in prompt_packs}
        raise UnsupportedFamilyError(
            f"Document backend does not support prompt families: {families}. "
            f"Supported: {sorted(supported)}"
        )
    if not doc_packs:
        # No document-family packs: generate one generic doc from first pack or request
        if prompt_packs:
            doc_packs = [prompt_packs[0]]
        else:
            rec = BackendExecutionRecord(
                backend_name="document",
                backend_version="1.0",
                execution_status="success",
                generated_output_paths=[],
                used_llm=False,
                used_fallback=True,
                executed_utc=utc_now_iso(),
                execution_log=["No document-family prompt packs; no files written"],
            )
            return True, "No document-family packs; nothing to generate", [], rec

    log: list[str] = []
    output_paths: list[str] = []
    for pack in doc_packs:
        fname = _FAMILY_TO_FILENAME.get(pack.prompt_family, "document_generated.md")
        out_path = workspace_path / fname
        content = _render_document(pack, style_packs, asset_plans)
        out_path.write_text(content, encoding="utf-8")
        output_paths.append(str(out_path))
        log.append(f"Wrote {out_path.name}")

    rec = BackendExecutionRecord(
        backend_name="document",
        backend_version="1.0",
        execution_status="success",
        generated_output_paths=output_paths,
        execution_log=log,
        used_llm=use_llm,
        used_fallback=not use_llm,
        executed_utc=utc_now_iso(),
    )
    return True, f"Generated {len(output_paths)} document(s)", output_paths, rec
