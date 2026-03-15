"""
Image/visual demo backend: produce real sandboxed visual-planning artifacts.

M11: no heavy image model required. Outputs storyboard frame cards (markdown + HTML board),
prompt cards, and/or design variant boards as real files. Validates the multimodal execution path.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.generate.generate_models import (
    GenerationRequest,
    GenerationManifest,
    PromptPack,
    AssetPlan,
    StylePack,
    BackendExecutionRecord,
    ShotItem,
)
from workflow_dataset.generate.backend_registry import ExecuteResult


def _write_storyboard_frames(
    workspace_path: Path,
    prompt_packs: list[PromptPack],
    asset_plans: list[AssetPlan],
) -> list[str]:
    """Write one markdown file per shot (frame card) and return paths."""
    workspace_path = Path(workspace_path)
    frames_dir = workspace_path / "storyboard_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    shots: list[tuple[int, str, str]] = []  # order, title, description/prompt

    for plan in asset_plans:
        for s in plan.shot_list:
            shots.append((s.sequence_order, s.title or "Shot", s.description or ""))
    if not shots and prompt_packs:
        for i, p in enumerate(prompt_packs):
            title = (p.prompt_text[:50] + "…") if len(p.prompt_text or "") > 50 else (p.prompt_text or f"Frame {i+1}")
            shots.append((i + 1, title, p.prompt_text or ""))

    for idx, (order, title, desc) in enumerate(sorted(shots, key=lambda x: x[0])):
        safe = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)[:40].strip() or f"frame_{idx+1}"
        fname = f"{idx + 1:02d}_{safe}.md"
        out = frames_dir / fname
        body = f"# Frame {idx + 1}: {title}\n\n"
        body += f"**Sequence order:** {order}\n\n"
        body += "## Prompt / description\n\n"
        body += desc or "(No description)\n"
        out.write_text(body, encoding="utf-8")
        paths.append(str(out))
    return paths


def _write_prompt_cards_html(
    workspace_path: Path,
    prompt_packs: list[PromptPack],
    style_packs: list[StylePack],
) -> str:
    """Write a single HTML file that renders prompt cards as a visual board."""
    workspace_path = Path(workspace_path)
    out = workspace_path / "prompt_cards.html"
    hints = []
    for sp in style_packs:
        hints.extend(sp.tone_or_visual_hints or [])
    cards_html = []
    for i, p in enumerate(prompt_packs):
        family = p.prompt_family or "prompt"
        text = (p.prompt_text or "").replace("<", "&lt;").replace(">", "&gt;")
        cards_html.append(
            f'<div class="card"><h3>{family}</h3><p>{text[:500]}{"…" if len(p.prompt_text or "") > 500 else ""}</p></div>'
        )
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Prompt cards</title>
  <style>
    body { font-family: system-ui; padding: 1rem; background: #1a1a1a; color: #eee; }
    .board { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }
    .card { background: #2a2a2a; border-radius: 8px; padding: 1rem; border: 1px solid #444; }
    .card h3 { margin: 0 0 0.5rem; font-size: 0.9rem; color: #aaa; }
    .card p { margin: 0; font-size: 0.85rem; line-height: 1.4; }
  </style>
</head>
<body>
  <h1>Prompt cards</h1>
  <div class="board">
"""
    html += "\n".join(cards_html)
    html += "\n  </div>\n</body>\n</html>"
    out.write_text(html, encoding="utf-8")
    return str(out)


def execute_image_demo_backend(
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
    Generate real visual-planning artifacts: storyboard frame cards (markdown) and prompt cards (HTML).
    Sandbox-only. No external image model; artifacts are real files for inspection.
    """
    style_packs = style_packs or []
    workspace_path = Path(workspace_path)
    workspace_path.mkdir(parents=True, exist_ok=True)
    log: list[str] = []
    output_paths: list[str] = []

    frame_paths = _write_storyboard_frames(workspace_path, prompt_packs, asset_plans)
    output_paths.extend(frame_paths)
    log.append(f"Wrote {len(frame_paths)} storyboard frame(s)")

    if prompt_packs:
        card_path = _write_prompt_cards_html(workspace_path, prompt_packs, style_packs)
        output_paths.append(card_path)
        log.append("Wrote prompt_cards.html")

    rec = BackendExecutionRecord(
        backend_name="image_demo",
        backend_version="1.0",
        execution_status="success",
        generated_output_paths=output_paths,
        execution_log=log,
        used_llm=False,
        used_fallback=True,
        executed_utc=utc_now_iso(),
    )
    return True, f"Generated {len(output_paths)} visual-planning artifact(s)", output_paths, rec
