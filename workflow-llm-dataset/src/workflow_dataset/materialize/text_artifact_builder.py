"""
Generate real .md, .txt, and .json text artifacts in the sandbox from draft structures and context.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.materialize.materialize_models import MaterializedArtifact
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


# Draft type -> preferred extension and content family
TEXT_DRAFT_TYPES: dict[str, tuple[str, str]] = {
    "project_brief": ("md", "markdown_brief"),
    "meeting_agenda": ("md", "markdown_agenda"),
    "weekly_review": ("md", "markdown_review"),
    "sop_outline": ("md", "markdown_sop"),
    "planning_memo": ("md", "markdown_memo"),
    "operating_checklist": ("md", "markdown_checklist"),
    "reconciliation_checklist": ("md", "markdown_checklist"),
    "operations_report_outline": ("md", "markdown_report"),
    "creative_brief_outline": ("md", "markdown_brief"),
    "storyboard_shotlist_scaffold": ("md", "markdown_shotlist"),
    "revision_naming_scaffold": ("md", "markdown_guide"),
    "deliverable_set_outline": ("md", "markdown_outline"),
    "asset_bundle_checklist": ("md", "markdown_checklist"),
    "design_brief_structure": ("md", "markdown_brief"),
    "architecture_package_structure": ("md", "markdown_outline"),
}


def build_text_artifact(
    workspace_path: Path | str,
    draft_type: str,
    title: str,
    structure_outline: str,
    sections: list[str] | None = None,
    request_id: str = "",
    project_id: str = "",
    draft_ref: str = "",
    style_profile_refs: list[str] | None = None,
    allow_markdown: bool = True,
    allow_json: bool = True,
) -> MaterializedArtifact | None:
    """
    Write a text artifact (markdown or json) into the workspace. Returns the artifact record.
    """
    if not allow_markdown and not allow_json:
        return None
    ext, art_type = TEXT_DRAFT_TYPES.get(draft_type, ("md", "markdown_doc"))
    if not allow_markdown and ext == "md":
        ext = "txt"
    workspace_path = Path(workspace_path)
    workspace_path.mkdir(parents=True, exist_ok=True)
    safe_title = "".join(c for c in title.replace(" ", "_") if c.isalnum() or c in "_-")[:80] or "artifact"
    filename = f"{safe_title}.{ext}"
    out_path = workspace_path / filename
    content = structure_outline if structure_outline else f"# {title}\n\n" + "\n".join(f"## {s}" for s in (sections or []))
    out_path.write_text(content, encoding="utf-8")
    artifact_id = stable_id("art", draft_type, request_id or out_path.name, utc_now_iso(), prefix="art")
    try:
        rel = str(out_path.relative_to(workspace_path))
    except ValueError:
        rel = filename
    return MaterializedArtifact(
        artifact_id=artifact_id,
        request_id=request_id,
        project_id=project_id,
        artifact_type=art_type,
        sandbox_path=rel,
        title=title,
        summary=content[:200] + "..." if len(content) > 200 else content,
        provenance_refs=[draft_ref] if draft_ref else [],
        created_utc=utc_now_iso(),
    )


def build_json_structure_summary(
    workspace_path: Path | str,
    draft_type: str,
    title: str,
    sections: list[str],
    naming: list[str],
    request_id: str = "",
    project_id: str = "",
    draft_ref: str = "",
) -> MaterializedArtifact | None:
    """Write a JSON structure summary (sections + naming) into the workspace."""
    import json
    workspace_path = Path(workspace_path)
    workspace_path.mkdir(parents=True, exist_ok=True)
    data = {"title": title, "draft_type": draft_type, "sections": sections, "suggested_naming": naming}
    safe_title = "".join(c for c in title.replace(" ", "_") if c.isalnum() or c in "_-")[:80] or "structure"
    filename = f"{safe_title}_structure.json"
    out_path = workspace_path / filename
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    artifact_id = stable_id("art", "json", request_id or filename, utc_now_iso(), prefix="art")
    return MaterializedArtifact(
        artifact_id=artifact_id,
        request_id=request_id,
        project_id=project_id,
        artifact_type="json_structure",
        sandbox_path=filename,
        title=title,
        summary=f"Structure: {len(sections)} sections, {len(naming)} naming hints",
        provenance_refs=[draft_ref] if draft_ref else [],
        created_utc=utc_now_iso(),
    )
