"""
Render a human-readable preview of materialized outputs and manifest.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.materialize.materialize_models import MaterializationManifest, MaterializedArtifact


def render_preview(
    manifest: MaterializationManifest,
    workspace_path: Path | str,
    max_file_preview_chars: int = 500,
) -> str:
    """
    Produce a text preview of what was created: manifest summary + optional file snippets.
    """
    lines = [
        "# Materialization preview",
        "",
        f"**Manifest ID:** {manifest.manifest_id}",
        f"**Request ID:** {manifest.request_id}",
        f"**Generated from:** {manifest.generated_from}",
        f"**LLM used:** {manifest.llm_used} | **Retrieval used:** {manifest.retrieval_used}",
        "",
        "## Output paths",
        "",
    ]
    for p in manifest.output_paths:
        lines.append(f"- `{p}`")
    lines.extend(["", "## Artifacts", ""])
    for a in manifest.artifacts:
        lines.append(f"- **{a.title}** ({a.artifact_type})")
        lines.append(f"  - Path: `{a.sandbox_path}`")
        if a.summary:
            lines.append(f"  - Summary: {a.summary[:200]}")
    if manifest.draft_refs:
        lines.extend(["", "**Draft refs:** " + ", ".join(manifest.draft_refs)])
    if manifest.suggestion_refs:
        lines.extend(["", "**Suggestion refs:** " + ", ".join(manifest.suggestion_refs)])
    if manifest.style_profile_refs:
        lines.extend(["", "**Style profile refs:** " + ", ".join(manifest.style_profile_refs[:5])])
    lines.append("")

    base = Path(workspace_path)
    if base.exists() and manifest.output_paths and max_file_preview_chars > 0:
        lines.append("## File previews")
        lines.append("")
        for rel in manifest.output_paths[:5]:
            full = base / rel if not Path(rel).is_absolute() else Path(rel)
            if full.exists() and full.is_file():
                try:
                    raw = full.read_text(encoding="utf-8", errors="replace")
                    snippet = raw[:max_file_preview_chars] + ("..." if len(raw) > max_file_preview_chars else "")
                    lines.append(f"### {rel}")
                    lines.append("```")
                    lines.append(snippet)
                    lines.append("```")
                    lines.append("")
                except Exception:
                    lines.append(f"### {rel} (binary or unreadable)")
                    lines.append("")

    return "\n".join(lines)


def render_artifact_tree(workspace_path: Path | str, indent: str = "", max_depth: int = 4) -> str:
    """Render a simple directory tree of the workspace (for list-workspaces / preview)."""
    def _tree(b: Path, prefix: str, depth: int) -> list[str]:
        if depth <= 0:
            return []
        if not b.exists() or not b.is_dir():
            return [f"{prefix}(empty or missing)"]
        lines: list[str] = []
        try:
            entries = sorted(b.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            for i, p in enumerate(entries):
                last = i == len(entries) - 1
                branch = "└── " if last else "├── "
                lines.append(f"{prefix}{branch}{p.name}")
                if p.is_dir() and p.name not in (".git", "__pycache__", "node_modules") and depth > 1:
                    lines.extend(_tree(p, prefix + ("    " if last else "│   "), depth - 1))
        except Exception:
            lines.append(f"{prefix}(error listing)")
        return lines

    base = Path(workspace_path)
    return "\n".join(_tree(base, indent, max_depth)) if base.exists() else f"{indent}(missing)"
