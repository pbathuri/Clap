"""
Orchestrate materialization: draft/suggestion + context -> real artifacts in sandbox.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from workflow_dataset.materialize.materialize_models import (
    MaterializationRequest,
    MaterializedArtifact,
    MaterializationManifest,
)
from workflow_dataset.materialize.workspace_manager import create_workspace
from workflow_dataset.materialize.manifest_store import save_manifest
from workflow_dataset.materialize.text_artifact_builder import build_text_artifact, TEXT_DRAFT_TYPES
from workflow_dataset.materialize.table_artifact_builder import build_csv_artifact, build_tracker_csv_files, TABLE_SCAFFOLDS
from workflow_dataset.materialize.folder_scaffold_builder import build_folder_scaffold, build_project_scaffold
from workflow_dataset.materialize.creative_scaffold_builder import build_creative_artifacts, CREATIVE_FOLDER_LAYOUTS
from workflow_dataset.personal.draft_structure_engine import DRAFT_TEMPLATES
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def materialize_from_draft(
    context_bundle: dict[str, Any],
    workspace_root: Path | str,
    draft_id: str = "",
    draft_type: str = "",
    session_id: str = "",
    project_id: str = "",
    use_llm: bool = False,
    llm_refine_fn: Callable[..., str] | None = None,
    allow_markdown: bool = True,
    allow_csv: bool = True,
    allow_json: bool = True,
    allow_folder_scaffolds: bool = True,
    save_manifests: bool = True,
) -> tuple[MaterializationManifest, Path]:
    """
    Materialize artifacts from a draft structure. Returns (manifest, workspace_path).
    Draft can be identified by draft_id (from context) or draft_type (template key).
    """
    request_id = stable_id("req", "draft", draft_id or draft_type or "default", utc_now_iso(), prefix="req")
    workspace_path = create_workspace(workspace_root, session_id=session_id, request_id=request_id, project_id=project_id)
    req = MaterializationRequest(
        request_id=request_id,
        session_id=session_id,
        project_id=project_id,
        source_type="draft",
        source_ref=draft_id or draft_type,
        materialization_mode="sandbox",
        output_family="",
        created_utc=utc_now_iso(),
    )
    artifacts: list[MaterializedArtifact] = []
    output_paths: list[str] = []

    # Resolve draft content from context or template
    draft_ctx = context_bundle.get("draft_context") or {}
    drafts = draft_ctx.get("drafts") or []
    draft_obj: dict[str, Any] | None = None
    if draft_id:
        for d in drafts:
            if d.get("draft_id") == draft_id:
                draft_obj = d
                break
    if not draft_obj and draft_type and draft_type in DRAFT_TEMPLATES:
        t = DRAFT_TEMPLATES[draft_type]
        draft_obj = {
            "draft_id": draft_id or stable_id("draft", draft_type, prefix="draft"),
            "draft_type": draft_type,
            "title": t.get("title", draft_type),
            "structure_outline": t.get("outline", ""),
            "recommended_sections": t.get("sections", []),
            "suggested_naming": t.get("naming", []),
            "domain": t.get("domain", "general"),
        }
    if not draft_obj and drafts:
        draft_obj = drafts[0] if isinstance(drafts[0], dict) else None
    if not draft_obj:
        manifest = MaterializationManifest(
            manifest_id=stable_id("manifest", request_id, prefix="mf"),
            request_id=request_id,
            output_paths=[],
            generated_from=draft_type or draft_id or "unknown",
            llm_used=use_llm,
            retrieval_used=bool(context_bundle.get("retrieved_docs")),
            created_utc=utc_now_iso(),
            artifacts=[],
        )
        if save_manifests:
            save_manifest(manifest, workspace_path)
        return manifest, workspace_path

    dtype = draft_obj.get("draft_type", draft_type)
    title = draft_obj.get("title", dtype)
    outline = draft_obj.get("structure_outline", draft_obj.get("outline", ""))
    sections = draft_obj.get("recommended_sections", draft_obj.get("sections", []))
    naming = draft_obj.get("suggested_naming", draft_obj.get("naming", []))
    did = draft_obj.get("draft_id", "")
    style_refs = draft_obj.get("style_profile_refs") or []

    if use_llm and llm_refine_fn and context_bundle.get("retrieved_text"):
        try:
            outline = llm_refine_fn(draft_outline=outline, context_snippet=context_bundle.get("retrieved_text", "")[:2000], domain=draft_obj.get("domain", ""))
        except Exception:
            pass

    # Route by draft type to text / table / folder / creative
    if dtype in TEXT_DRAFT_TYPES and allow_markdown:
        art = build_text_artifact(
            workspace_path, dtype, title, outline,
            sections=sections, request_id=request_id, project_id=project_id, draft_ref=did,
            style_profile_refs=style_refs, allow_markdown=allow_markdown, allow_json=allow_json,
        )
        if art:
            artifacts.append(art)
            output_paths.append(art.sandbox_path)
    if dtype in TABLE_SCAFFOLDS or "scaffold" in dtype and "vendor" in dtype or "inventory" in dtype:
        if allow_csv:
            if dtype == "vendor_order_tracking_scaffold":
                for a in build_tracker_csv_files(workspace_path, dtype, title, request_id, project_id, did):
                    artifacts.append(a)
                    output_paths.append(a.sandbox_path)
            else:
                art = build_csv_artifact(workspace_path, dtype, title, request_id=request_id, project_id=project_id, draft_ref=did)
                if art:
                    artifacts.append(art)
                    output_paths.append(art.sandbox_path)
    if dtype in CREATIVE_FOLDER_LAYOUTS and allow_folder_scaffolds:
        for a in build_creative_artifacts(workspace_path, dtype, title, outline, sections, naming, request_id, project_id, did):
            artifacts.append(a)
            if a.sandbox_path:
                output_paths.append(a.sandbox_path)
    elif dtype in ("creative_brief_outline", "storyboard_shotlist_scaffold", "revision_naming_scaffold", "deliverable_set_outline", "asset_bundle_checklist", "design_brief_structure") and allow_markdown:
        art = build_text_artifact(workspace_path, dtype, title, outline, sections=sections, request_id=request_id, project_id=project_id, draft_ref=did)
        if art:
            artifacts.append(art)
            output_paths.append(art.sandbox_path)
    # Default: text artifact
    if not artifacts and outline and allow_markdown:
        art = build_text_artifact(workspace_path, "project_brief", title, outline, sections=sections, request_id=request_id, project_id=project_id, draft_ref=did)
        if art:
            artifacts.append(art)
            output_paths.append(art.sandbox_path)

    manifest = MaterializationManifest(
        manifest_id=stable_id("manifest", request_id, prefix="mf"),
        request_id=request_id,
        output_paths=list(dict.fromkeys(p for p in output_paths if p)),
        generated_from=dtype,
        style_profile_refs=style_refs,
        draft_refs=[did] if did else [],
        llm_used=use_llm,
        retrieval_used=bool(context_bundle.get("retrieved_docs")),
        created_utc=utc_now_iso(),
        artifacts=artifacts,
    )
    if save_manifests:
        save_manifest(manifest, workspace_path)
    return manifest, workspace_path


def materialize_from_suggestion(
    context_bundle: dict[str, Any],
    workspace_root: Path | str,
    suggestion_id: str = "",
    session_id: str = "",
    project_id: str = "",
    save_manifests: bool = True,
) -> tuple[MaterializationManifest, Path]:
    """
    Materialize based on a style-aware suggestion (e.g. draft_creation -> pick draft and materialize).
    """
    request_id = stable_id("req", "sug", suggestion_id or "unknown", utc_now_iso(), prefix="req")
    workspace_path = create_workspace(workspace_root, session_id=session_id, request_id=request_id, project_id=project_id)
    sug_ctx = context_bundle.get("suggestion_context") or {}
    suggestions = [s for s in (sug_ctx.get("suggestions") or []) if s.get("suggestion_id") == suggestion_id] if suggestion_id else []
    if not suggestions:
        manifest = MaterializationManifest(
            manifest_id=stable_id("manifest", request_id, prefix="mf"),
            request_id=request_id,
            output_paths=[],
            generated_from=suggestion_id,
            suggestion_refs=[suggestion_id],
            created_utc=utc_now_iso(),
            artifacts=[],
        )
        if save_manifests:
            save_manifest(manifest, workspace_path)
        return manifest, workspace_path
    s = suggestions[0]
    sug_type = s.get("suggestion_type", "")
    if sug_type == "draft_creation":
        draft_type = "project_brief"
        if "report" in (s.get("title") or "").lower():
            draft_type = "operations_report_outline"
        if "spreadsheet" in (s.get("title") or "").lower() or "workbook" in (s.get("title") or "").lower():
            draft_type = "monthly_reporting_workbook"
        return materialize_from_draft(
            context_bundle,
            workspace_root,
            draft_type=draft_type,
            session_id=session_id,
            project_id=project_id or s.get("project_id", ""),
            allow_markdown=True,
            allow_csv=True,
            allow_folder_scaffolds=True,
            save_manifests=save_manifests,
        )
    # Fallback: create a simple project scaffold
    from workflow_dataset.materialize.folder_scaffold_builder import build_project_scaffold
    art = build_project_scaffold(workspace_path, "Project", request_id=request_id, project_id=project_id or s.get("project_id", ""))
    manifest = MaterializationManifest(
        manifest_id=stable_id("manifest", request_id, prefix="mf"),
        request_id=request_id,
        output_paths=[],
        generated_from=suggestion_id,
        suggestion_refs=[suggestion_id],
        style_profile_refs=s.get("style_profile_refs") or [],
        created_utc=utc_now_iso(),
        artifacts=[art],
    )
    if save_manifests:
        save_manifest(manifest, workspace_path)
    return manifest, workspace_path
