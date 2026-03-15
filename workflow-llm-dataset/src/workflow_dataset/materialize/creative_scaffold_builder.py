"""
Generate creative/design package scaffolds: folder trees, placeholders, naming plans, shotlist templates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.materialize.materialize_models import MaterializedArtifact
from workflow_dataset.materialize.workspace_manager import ensure_workspace_dir
from workflow_dataset.materialize.folder_scaffold_builder import build_folder_scaffold
from workflow_dataset.materialize.text_artifact_builder import build_text_artifact
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id

# Creative package folder layouts (from draft_structure_engine)
CREATIVE_FOLDER_LAYOUTS: dict[str, list[str]] = {
    "creative_project_folder_scaffold": ["source", "exports", "reviews", "assets", "references", "docs"],
    "export_package_scaffold": ["deliverables", "deliverables/print", "deliverables/web", "deliverables/source", "revisions"],
}


def build_creative_folder_scaffold(
    workspace_path: Path | str,
    layout_key: str,
    request_id: str = "",
    project_id: str = "",
    draft_ref: str = "",
    naming_hints: list[str] | None = None,
) -> MaterializedArtifact:
    """Create creative-style folder tree (source, exports, reviews, etc.) in sandbox."""
    workspace_path = Path(workspace_path)
    dirs = CREATIVE_FOLDER_LAYOUTS.get(layout_key, ["source", "exports", "assets", "references"])
    created: list[str] = []
    for part in dirs:
        sub = part.replace("..", "").strip("/")
        if not sub:
            continue
        d = ensure_workspace_dir(workspace_path, *sub.split("/"))
        try:
            rel = d.relative_to(workspace_path)
            created.append(str(rel))
        except ValueError:
            created.append(part)
    readme = workspace_path / "README_creative_scaffold.txt"
    content = "Creative package scaffold.\n\nFolders: " + ", ".join(created)
    if naming_hints:
        content += "\n\nNaming hints: " + ", ".join(naming_hints[:10])
    readme.write_text(content, encoding="utf-8")
    created.append("README_creative_scaffold.txt")
    artifact_id = stable_id("art", "creative_scaffold", request_id or layout_key, utc_now_iso(), prefix="art")
    return MaterializedArtifact(
        artifact_id=artifact_id,
        request_id=request_id,
        project_id=project_id,
        artifact_type="creative_folder_scaffold",
        sandbox_path="",
        title=f"Creative scaffold: {layout_key}",
        summary=f"Folders: {', '.join(created[:6])}",
        provenance_refs=[draft_ref] if draft_ref else [],
        created_utc=utc_now_iso(),
    )


def build_creative_artifacts(
    workspace_path: Path | str,
    draft_type: str,
    title: str,
    structure_outline: str,
    sections: list[str],
    naming: list[str],
    request_id: str = "",
    project_id: str = "",
    draft_ref: str = "",
) -> list[MaterializedArtifact]:
    """
    Build creative-domain artifacts: folder scaffold + brief/shotlist/naming guide as text.
    Returns list of MaterializedArtifact.
    """
    workspace_path = Path(workspace_path)
    artifacts: list[MaterializedArtifact] = []
    if draft_type == "creative_project_folder_scaffold":
        artifacts.append(build_creative_folder_scaffold(
            workspace_path, "creative_project_folder_scaffold",
            request_id=request_id, project_id=project_id, draft_ref=draft_ref, naming_hints=naming,
        ))
    elif draft_type == "export_package_scaffold":
        artifacts.append(build_creative_folder_scaffold(
            workspace_path, "export_package_scaffold",
            request_id=request_id, project_id=project_id, draft_ref=draft_ref, naming_hints=naming,
        ))
    # Always add a text artifact for the outline/guide
    text_art = build_text_artifact(
        workspace_path, draft_type, title, structure_outline,
        sections=sections, request_id=request_id, project_id=project_id, draft_ref=draft_ref,
    )
    if text_art:
        artifacts.append(text_art)
    return artifacts
