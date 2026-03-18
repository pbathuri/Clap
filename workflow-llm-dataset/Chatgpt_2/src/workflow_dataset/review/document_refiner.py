"""
M12: Optional local-LLM document refinement for generated document artifacts.

Deterministic refinement fallback; config-gated LLM refinement. Grounded in style and project context.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id
from workflow_dataset.review.review_models import RefineRequest, VariantRecord
from workflow_dataset.review.variant_manager import create_variant_record
from workflow_dataset.review.version_store import save_variant_record
from workflow_dataset.generate.generate_models import StylePack, PromptPack, AssetPlan


def _deterministic_refine(
    current_text: str,
    user_instruction: str = "",
    style_constraints: list[str] | None = None,
    structural_constraints: list[str] | None = None,
) -> str:
    """
    Deterministic refinement: append revision section with user instruction and constraints.
    Does not rewrite; adds a "Revision notes" section so output stays grounded.
    """
    lines = current_text.rstrip().splitlines()
    add: list[str] = []
    if user_instruction or (style_constraints and any(s.strip() for s in style_constraints)) or (structural_constraints and any(s.strip() for s in structural_constraints)):
        add.append("")
        add.append("## Revision notes")
        if user_instruction:
            add.append(user_instruction)
        if style_constraints and any(s.strip() for s in style_constraints):
            add.append("\nStyle constraints applied:")
            for c in style_constraints:
                if c.strip():
                    add.append(f"- {c.strip()}")
        if structural_constraints and any(s.strip() for s in structural_constraints):
            add.append("\nStructural constraints:")
            for c in structural_constraints:
                if c.strip():
                    add.append(f"- {c.strip()}")
    return "\n".join(lines + add) + "\n"


def refine_document(
    artifact_path: str | Path,
    workspace_path: str | Path,
    refine_request: RefineRequest,
    style_packs: list[StylePack] | None = None,
    prompt_packs: list[PromptPack] | None = None,
    asset_plans: list[AssetPlan] | None = None,
    llm_refine_fn: Callable[..., str] | None = None,
    generation_id: str = "",
    review_store_path: Path | str = "",
) -> tuple[bool, str, list[str], VariantRecord | None]:
    """
    Refine a generated document artifact. Writes refined variant into workspace_path/refined/.
    Returns (success, message, output_paths, variant_record).
    """
    path = Path(artifact_path)
    workspace_path = Path(workspace_path)
    if not path.exists() or not path.is_file():
        return False, f"Artifact not found: {path}", [], None
    try:
        current_text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return False, str(e), [], None

    use_llm = refine_request.use_llm and llm_refine_fn is not None
    if use_llm and llm_refine_fn:
        context_snippet = ""
        if style_packs:
            for sp in style_packs[:1]:
                context_snippet += " ".join(sp.tone_or_visual_hints or [])[:800]
        domain = style_packs[0].domain if style_packs else ""
        refined_text = llm_refine_fn(
            draft_outline=current_text[:3000],
            context_snippet=context_snippet,
            domain=domain,
        )
        if not refined_text:
            refined_text = _deterministic_refine(
                current_text,
                refine_request.user_instruction,
                refine_request.style_constraints,
                refine_request.structural_constraints,
            )
            use_llm = False
    else:
        refined_text = _deterministic_refine(
            current_text,
            refine_request.user_instruction,
            refine_request.style_constraints,
            refine_request.structural_constraints,
        )

    out_dir = workspace_path / "refined"
    out_dir.mkdir(parents=True, exist_ok=True)
    base_name = path.stem
    suffix = path.suffix or ".md"
    ts_slug = utc_now_iso()[:10]
    out_name = f"{base_name}_refined_{ts_slug}{suffix}"
    out_path = out_dir / out_name
    out_path.write_text(refined_text, encoding="utf-8")
    output_paths = [str(out_path)]

    gen_id = generation_id or refine_request.generation_id
    variant = create_variant_record(
        base_artifact_id=refine_request.artifact_id or path.stem,
        generation_id=gen_id,
        output_paths=output_paths,
        variant_type="refined",
        revision_note=refine_request.user_instruction or "Refined",
        used_llm_refinement=use_llm,
    )
    if review_store_path:
        save_variant_record(variant, review_store_path)

    return True, f"Refined artifact written to {out_path}", output_paths, variant


def get_llm_refine_fn_for_review(
    llm_config_path: str | Path | None = None,
    max_tokens: int = 800,
) -> Callable[..., str] | None:
    """Return LLM refine callable for document refinement, or None if not configured."""
    from workflow_dataset.agent_loop.llm_refine import get_llm_refine_fn
    return get_llm_refine_fn(llm_config_path=llm_config_path, max_tokens=max_tokens)
