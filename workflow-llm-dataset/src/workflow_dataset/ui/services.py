"""
Service layer for the operator console.

Thin wrappers around setup, project_interpreter, suggestions, drafts,
materialize, apply, rollback, and agent_loop. No business logic duplication.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.settings import load_settings, Settings


def get_settings(config_path: str = "configs/settings.yaml") -> Settings:
    """Load settings from config. Uses project root when path is relative."""
    return load_settings(config_path)


def _resolve_latest_session_id(settings: Settings) -> str | None:
    setup = getattr(settings, "setup", None)
    if not setup:
        return None
    sessions_dir = Path(setup.setup_dir) / "sessions"
    if not sessions_dir.exists():
        return None
    latest = sorted(sessions_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return latest[0].stem if latest else None


# ----- Setup -----


def get_setup_sessions(settings: Settings) -> list[dict[str, Any]]:
    """List setup sessions (session_id, path)."""
    setup = getattr(settings, "setup", None)
    if not setup:
        return []
    sessions_dir = Path(setup.setup_dir) / "sessions"
    if not sessions_dir.exists():
        return []
    out = []
    for p in sorted(sessions_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        out.append({"session_id": p.stem, "path": str(p)})
    return out


def get_setup_progress(settings: Settings, session_id: str | None = None) -> dict[str, Any] | None:
    """Get progress for a session. Uses latest if session_id is empty."""
    from workflow_dataset.setup.progress_tracker import get_progress
    from workflow_dataset.setup.job_store import load_session

    setup = getattr(settings, "setup", None)
    if not setup:
        return None
    sid = session_id or _resolve_latest_session_id(settings)
    if not sid:
        return None
    setup_dir = Path(setup.setup_dir)
    progress = get_progress(setup_dir, sid)
    session = load_session(setup_dir, sid)
    if not progress:
        return {"session_id": sid, "session": session.model_dump() if session else None}
    return {
        "session_id": sid,
        "current_stage": progress.current_stage.value,
        "files_scanned": progress.files_scanned,
        "artifacts_classified": progress.artifacts_classified,
        "docs_parsed": progress.docs_parsed,
        "projects_detected": progress.projects_detected,
        "style_patterns_extracted": progress.style_patterns_extracted,
        "graph_nodes_created": progress.graph_nodes_created,
        "adapter_errors": progress.adapter_errors,
        "adapter_skips": progress.adapter_skips,
        "details": progress.details or {},
        "session": session.model_dump() if session else None,
    }


def get_setup_summary_markdown(settings: Settings, session_id: str | None = None) -> str:
    """Load setup summary markdown for a session."""
    setup = getattr(settings, "setup", None)
    if not setup:
        return ""
    sid = session_id or _resolve_latest_session_id(settings)
    if not sid:
        return ""
    report_path = Path(setup.setup_reports_dir) / f"{sid}_summary.md"
    if not report_path.exists():
        return ""
    return report_path.read_text(encoding="utf-8")


# ----- Projects / context -----


def get_projects(settings: Settings) -> list[dict[str, Any]]:
    """List projects from graph."""
    from workflow_dataset.personal.project_interpreter import load_projects_from_graph

    graph_path = Path(getattr(settings.paths, "graph_store_path", "data/local/work_graph.sqlite"))
    if not graph_path.exists():
        return []
    return load_projects_from_graph(graph_path)


def get_assistive_context(settings: Settings, session_id: str | None = None, project_id: str = "") -> dict[str, Any]:
    """Full assistive context (projects, domains, style_signals, parsed_artifacts)."""
    from workflow_dataset.personal.project_interpreter import get_assistive_context as _get

    setup = getattr(settings, "setup", None)
    if not setup:
        return {}
    sid = session_id or _resolve_latest_session_id(settings) or ""
    graph_path = Path(getattr(settings.paths, "graph_store_path", "data/local/work_graph.sqlite"))
    return _get(
        graph_path,
        setup.style_signals_dir,
        setup.parsed_artifacts_dir,
        sid,
    )


# ----- Suggestions -----


def get_suggestions(settings: Settings) -> list[Any]:
    """Load style-aware suggestions from suggestions_dir."""
    from workflow_dataset.personal.style_suggestion_engine import load_style_aware_suggestions

    setup = getattr(settings, "setup", None)
    if not setup:
        return []
    suggestions_dir = Path(getattr(setup, "suggestions_dir", "data/local/suggestions"))
    return load_style_aware_suggestions(suggestions_dir)


# ----- Drafts -----


def get_drafts(settings: Settings) -> list[Any]:
    """Load draft structures from draft_structures_dir."""
    from workflow_dataset.personal.draft_structure_engine import load_draft_structures

    setup = getattr(settings, "setup", None)
    if not setup:
        return []
    draft_dir = Path(getattr(setup, "draft_structures_dir", "data/local/draft_structures"))
    if not draft_dir.exists():
        return []
    return load_draft_structures(draft_dir)


# ----- Style profiles -----


def get_style_profiles(settings: Settings) -> list[Any]:
    """Load style profiles from style_profiles_dir."""
    from workflow_dataset.personal.style_profiles import load_style_profiles

    setup = getattr(settings, "setup", None)
    if not setup:
        return []
    profiles_dir = Path(getattr(setup, "style_profiles_dir", "data/local/style_profiles"))
    if not profiles_dir.exists():
        return []
    return load_style_profiles(profiles_dir)


# ----- Workspaces -----


def get_workspaces(settings: Settings, session_id: str = "", limit: int = 50) -> list[dict[str, Any]]:
    """List materialized workspaces (and generation workspaces when adoption bridge enabled)."""
    from workflow_dataset.materialize.workspace_manager import list_workspaces

    mat = getattr(settings, "materialization", None)
    root = Path(getattr(mat, "materialization_workspace_root", "data/local/workspaces")) if mat else Path("data/local/workspaces")
    workspaces = list_workspaces(root, session_id=session_id, limit=limit)
    gen = getattr(settings, "generation", None)
    if gen and getattr(gen, "generation_adoption_bridge_enabled", False):
        gen_ws = get_generation_workspaces(settings, limit=20)
        workspaces = workspaces + gen_ws
    return workspaces


def get_generation_workspaces(settings: Settings, limit: int = 20) -> list[dict[str, Any]]:
    """List generation sandbox workspaces (for apply flow when adoption bridge enabled)."""
    gen = getattr(settings, "generation", None)
    if not gen:
        return []
    root = Path(getattr(gen, "generation_workspace_root", "data/local/generation"))
    if not root.exists():
        return []
    out = []
    for d in sorted(root.iterdir(), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True):
        if d.is_dir() and not d.name.startswith(".") and d.name not in ("requests", "manifests", "style_packs", "prompt_packs", "asset_plans", "variant_plans", "review"):
            out.append({"name": f"Generation: {d.name[:24]}", "path": str(d.resolve())})
            if len(out) >= limit:
                break
    return out


def get_workspace_preview(workspace_path: str | Path) -> str:
    """Preview contents of a workspace (manifest + tree or tree only)."""
    from workflow_dataset.materialize.manifest_store import load_manifest
    from workflow_dataset.materialize.preview_renderer import render_preview, render_artifact_tree

    path = Path(workspace_path)
    if not path.exists():
        return ""
    manifest = load_manifest(path)
    if manifest:
        return render_preview(manifest, path, max_file_preview_chars=500)
    return render_artifact_tree(path)


# ----- Materialization -----


def run_materialize(
    settings: Settings,
    draft_type: str = "",
    suggestion_id: str = "",
    session_id: str | None = None,
    project_id: str = "",
    use_llm: bool = False,
) -> tuple[Any, Path]:
    """
    Materialize draft or suggestion to sandbox. Returns (manifest, workspace_path).
    Exactly one of draft_type or suggestion_id should be set (suggestion_id takes precedence if both).
    """
    from workflow_dataset.agent_loop.context_builder import build_context_bundle
    from workflow_dataset.materialize.artifact_builder import materialize_from_draft, materialize_from_suggestion
    from workflow_dataset.materialize.materialize_graph import persist_materialization_nodes
    from workflow_dataset.agent_loop.llm_refine import get_llm_refine_fn

    setup = getattr(settings, "setup", None)
    if not setup:
        raise ValueError("Setup config missing")
    mat = getattr(settings, "materialization", None)
    workspace_root = Path(getattr(mat, "materialization_workspace_root", "data/local/workspaces")) if mat else Path("data/local/workspaces")
    graph_path = Path(getattr(settings.paths, "graph_store_path", "data/local/work_graph.sqlite"))
    sid = session_id or _resolve_latest_session_id(settings) or ""
    corpus_path = Path("data/local/llm/personal_corpus/personal_corpus.jsonl")
    if not corpus_path.exists():
        corpus_path = None

    context_bundle = build_context_bundle(
        graph_path=graph_path,
        style_signals_dir=setup.style_signals_dir,
        parsed_artifacts_dir=setup.parsed_artifacts_dir,
        style_profiles_dir=getattr(setup, "style_profiles_dir", "data/local/style_profiles"),
        suggestions_dir=getattr(setup, "suggestions_dir", "data/local/suggestions"),
        draft_structures_dir=getattr(setup, "draft_structures_dir", "data/local/draft_structures"),
        setup_session_id=sid,
        project_id=project_id,
        corpus_path=corpus_path,
        query=draft_type or suggestion_id,
        max_retrieval_docs=5,
    )
    project_id_by_label = {
        p.get("label", ""): p.get("node_id", "")
        for p in (context_bundle.get("project_context") or {}).get("projects", [])
        if p.get("label")
    }
    save_manifests = getattr(mat, "materialization_save_manifests", True) if mat else True
    llm_refine_fn = get_llm_refine_fn(llm_config_path=Path("configs/llm_training.yaml")) if use_llm else None

    if suggestion_id:
        manifest, ws_path = materialize_from_suggestion(
            context_bundle,
            workspace_root,
            suggestion_id=suggestion_id,
            session_id=sid,
            project_id=project_id,
            save_manifests=save_manifests,
        )
    else:
        manifest, ws_path = materialize_from_draft(
            context_bundle,
            workspace_root,
            draft_type=draft_type or "project_brief",
            session_id=sid,
            project_id=project_id,
            use_llm=use_llm,
            llm_refine_fn=llm_refine_fn,
            allow_markdown=getattr(mat, "materialization_allow_markdown", True) if mat else True,
            allow_csv=getattr(mat, "materialization_allow_csv", True) if mat else True,
            allow_json=getattr(mat, "materialization_allow_json", True) if mat else True,
            allow_folder_scaffolds=getattr(mat, "materialization_allow_folder_scaffolds", True) if mat else True,
            save_manifests=save_manifests,
        )

    if getattr(mat, "materialization_graph_persistence", True) and graph_path.exists():
        persist_materialization_nodes(graph_path, manifest, ws_path, project_id_by_label)

    return manifest, ws_path


# ----- Apply -----


def build_apply_plan(
    settings: Settings,
    workspace_path: str | Path,
    target_path: str | Path,
    allow_overwrite: bool = False,
    selected_paths: list[str] | None = None,
) -> tuple[Any, str]:
    """
    Build apply plan (dry-run). Returns (ApplyPlan or None, error_message).
    selected_paths: optional relative paths in workspace (e.g. from adoption candidate).
    """
    from workflow_dataset.apply.target_validator import validate_target
    from workflow_dataset.apply.copy_planner import build_apply_plan as _build

    ap = getattr(settings, "apply", None)
    allowed_roots = getattr(ap, "apply_allowed_target_roots", None) or [] if ap else []
    ws = Path(workspace_path).resolve()
    target = Path(target_path).resolve()
    ok, msg = validate_target(target, allowed_roots=allowed_roots, must_exist=False)
    if not ok:
        return None, msg
    plan, err = _build(ws, target, selected_paths=selected_paths, allow_overwrite=allow_overwrite, dry_run=True)
    if err and not plan:
        return None, err or "Unknown error"
    return plan, ""


def get_diff_preview(plan: Any) -> str:
    """Render diff preview text for an apply plan."""
    from workflow_dataset.apply.diff_preview import render_diff_preview

    return render_diff_preview(plan)


def execute_apply(
    settings: Settings,
    workspace_path: str | Path,
    target_path: str | Path,
    allow_overwrite: bool = False,
    selected_paths: list[str] | None = None,
) -> tuple[Any, str]:
    """
    Execute apply (copy to target with backups). Assumes caller has already confirmed.
    Returns (ApplyResult or None, error_message).
    selected_paths: optional relative paths in workspace (e.g. from adoption candidate).
    """
    from workflow_dataset.apply.target_validator import validate_target
    from workflow_dataset.apply.copy_planner import build_apply_plan
    from workflow_dataset.apply.apply_executor import execute_apply as _execute
    from workflow_dataset.apply.apply_models import ApplyRequest
    from workflow_dataset.apply.apply_manifest_store import save_apply_request, save_apply_plan, save_apply_result
    from workflow_dataset.apply.apply_graph import persist_apply_request, persist_apply_plan_node, persist_apply_result_node
    from workflow_dataset.utils.dates import utc_now_iso
    from workflow_dataset.utils.hashes import stable_id

    ap = getattr(settings, "apply", None)
    if not ap or not getattr(ap, "apply_enabled", False):
        return None, "Apply is disabled. Enable apply.apply_enabled in config."
    allowed_roots = getattr(ap, "apply_allowed_target_roots", None) or []
    manifest_root = Path(getattr(ap, "apply_manifest_root", "data/local/applies"))
    backup_root = Path(getattr(ap, "apply_backup_root", "data/local/applies"))

    ws = Path(workspace_path).resolve()
    target = Path(target_path).resolve()
    ok, msg = validate_target(target, allowed_roots=allowed_roots, must_exist=False)
    if not ok:
        return None, msg
    plan, err = build_apply_plan(ws, target, selected_paths=selected_paths, allow_overwrite=allow_overwrite, dry_run=True)
    if err and not plan:
        return None, err or "Unknown error"
    if not plan or not plan.operations:
        return None, "Nothing to apply."

    apply_id = stable_id("apply", str(ws), str(target), utc_now_iso(), prefix="apply")
    plan.apply_id = apply_id
    req = ApplyRequest(
        apply_id=apply_id,
        workspace_path=str(ws),
        target_root=str(target),
        user_confirmed=True,
        created_utc=utc_now_iso(),
    )
    save_apply_request(req, manifest_root)
    save_apply_plan(plan, manifest_root)
    result, exec_err = _execute(
        plan,
        ws,
        target,
        user_confirmed=True,
        create_backups=getattr(ap, "apply_create_backups", True),
        backup_root=backup_root,
    )
    if not result:
        return None, exec_err or "Execution failed"
    result.apply_id = apply_id
    save_apply_result(result, manifest_root)
    if getattr(ap, "apply_graph_persistence", True):
        graph_path = Path(getattr(settings.paths, "graph_store_path", "data/local/work_graph.sqlite"))
        if graph_path.exists():
            persist_apply_request(graph_path, req)
            persist_apply_plan_node(graph_path, plan, apply_id)
            persist_apply_result_node(graph_path, result, apply_id)
    return result, ""


# ----- Rollback -----


def list_rollback_records(settings: Settings) -> list[dict[str, Any]]:
    """List rollback records (token, apply_id, created_utc)."""
    from workflow_dataset.apply.apply_manifest_store import load_rollback_record

    ap = getattr(settings, "apply", None)
    store = Path(getattr(ap, "apply_manifest_root", "data/local/applies")) if ap else Path("data/local/applies")
    rollbacks_dir = store / "rollbacks"
    if not rollbacks_dir.exists():
        return []
    out = []
    for p in sorted(rollbacks_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        token = p.stem
        rec = load_rollback_record(token, store)
        if rec:
            out.append({
                "rollback_token": rec.rollback_token,
                "apply_id": rec.apply_id,
                "created_utc": rec.created_utc,
                "affected_paths": rec.affected_paths,
            })
    return out


def get_rollback_record(settings: Settings, rollback_token: str) -> Any:
    """Load a single rollback record."""
    from workflow_dataset.apply.apply_manifest_store import load_rollback_record

    ap = getattr(settings, "apply", None)
    store = Path(getattr(ap, "apply_manifest_root", "data/local/applies")) if ap else Path("data/local/applies")
    return load_rollback_record(rollback_token, store)


def run_rollback(settings: Settings, rollback_token: str) -> tuple[bool, str]:
    """Perform rollback. Returns (success, message)."""
    from workflow_dataset.apply.rollback_store import perform_rollback

    ap = getattr(settings, "apply", None)
    if not getattr(ap, "apply_rollback_enabled", True):
        return False, "Rollback is disabled."
    store = Path(getattr(ap, "apply_manifest_root", "data/local/applies")) if ap else Path("data/local/applies")
    return perform_rollback(rollback_token, store)


# ----- Assist / chat -----


def run_assist_query(
    settings: Settings,
    query_text: str,
    project_id: str = "",
    session_id: str | None = None,
    use_llm: bool = False,
) -> dict[str, Any]:
    """
    Run one assist query (explain/next-step/chat). Returns dict with title, answer, supporting_evidence, confidence_score, used_retrieval, used_llm.
    """
    from workflow_dataset.agent_loop.agent_models import AgentQuery
    from workflow_dataset.agent_loop.response_builder import build_response
    from workflow_dataset.agent_loop.llm_refine import get_llm_refine_fn
    from workflow_dataset.utils.hashes import stable_id
    from workflow_dataset.utils.dates import utc_now_iso

    setup = getattr(settings, "setup", None)
    if not setup:
        return {"title": "Error", "answer": "Setup config missing.", "supporting_evidence": [], "confidence_score": 0.0, "used_retrieval": False, "used_llm": False}
    al = getattr(settings, "agent_loop", None) or type("AL", (), {"agent_loop_max_context_docs": 5, "agent_loop_project_scope_default": ""})()
    sid = session_id or _resolve_latest_session_id(settings) or ""
    graph_path = Path(getattr(settings.paths, "graph_store_path", "data/local/work_graph.sqlite"))
    corpus_path = Path("data/local/llm/personal_corpus/personal_corpus.jsonl")
    if not corpus_path.exists():
        corpus_path = None
    llm_refine_fn = get_llm_refine_fn(llm_config_path=Path("configs/llm_training.yaml")) if use_llm else None

    q = AgentQuery(
        query_id=stable_id("query", query_text[:50], utc_now_iso(), prefix="q"),
        user_text=query_text,
        project_id=project_id or getattr(al, "agent_loop_project_scope_default", "") or "",
        created_utc=utc_now_iso(),
    )
    resp = build_response(
        q,
        graph_path=graph_path,
        style_signals_dir=setup.style_signals_dir,
        parsed_artifacts_dir=setup.parsed_artifacts_dir,
        style_profiles_dir=getattr(setup, "style_profiles_dir", "data/local/style_profiles"),
        suggestions_dir=getattr(setup, "suggestions_dir", "data/local/suggestions"),
        draft_structures_dir=getattr(setup, "draft_structures_dir", "data/local/draft_structures"),
        setup_session_id=sid,
        corpus_path=corpus_path,
        max_retrieval_docs=getattr(al, "agent_loop_max_context_docs", 5),
        use_llm=use_llm,
        llm_refine_fn=llm_refine_fn,
    )
    return {
        "title": resp.title,
        "answer": resp.answer,
        "supporting_evidence": list(resp.supporting_evidence or []),
        "confidence_score": resp.confidence_score,
        "used_retrieval": resp.used_retrieval,
        "used_llm": resp.used_llm,
    }


# ----- Generation (M10) -----


def get_generation_requests(
    settings: Settings,
    session_id: str = "",
    project_id: str = "",
    limit: int = 30,
) -> list[dict[str, Any]]:
    """List generation requests for session/project."""
    gen = getattr(settings, "generation", None)
    if not gen:
        return []
    root = Path(getattr(gen, "generation_workspace_root", "data/local/generation"))
    from workflow_dataset.generate.sandbox_generation_store import list_generation_requests
    return list_generation_requests(root, session_id=session_id, project_id=project_id, limit=limit)


def get_generation_manifest_preview(settings: Settings, manifest_id: str) -> dict[str, Any] | None:
    """Load generation manifest for preview (refs, execution records, generated outputs)."""
    gen = getattr(settings, "generation", None)
    if not gen:
        return None
    root = Path(getattr(gen, "generation_workspace_root", "data/local/generation"))
    from workflow_dataset.generate.sandbox_generation_store import load_generation_manifest, load_packs_for_manifest
    m = load_generation_manifest(manifest_id, root)
    if not m:
        return None
    load_packs_for_manifest(m, root)
    execution_records = []
    for rec in (m.execution_records or []):
        execution_records.append({
            "backend_name": rec.backend_name,
            "backend_version": rec.backend_version,
            "execution_status": rec.execution_status,
            "generated_output_paths": rec.generated_output_paths[:20],
            "error_message": rec.error_message,
            "used_llm": rec.used_llm,
            "used_fallback": rec.used_fallback,
            "executed_utc": rec.executed_utc,
        })
    return {
        "manifest_id": m.manifest_id,
        "generation_id": m.generation_id,
        "workspace_path": m.workspace_path,
        "style_pack_refs": m.style_pack_refs,
        "prompt_pack_refs": m.prompt_pack_refs,
        "asset_plan_refs": m.asset_plan_refs,
        "status": getattr(m.status, "value", str(m.status)),
        "backend_requested": m.backend_requested or "",
        "backend_executed": m.backend_executed or "",
        "execution_records": execution_records,
        "generated_output_paths": list(m.generated_output_paths or [])[:30],
        "prompt_packs": [{"prompt_family": p.prompt_family, "prompt_text": (p.prompt_text or "")[:200]} for p in (m.prompt_packs or [])],
        "asset_plans": [{"target_outputs": a.target_outputs[:10]} for a in (m.asset_plans or [])],
    }


def get_available_generation_backends(settings: Settings) -> list[dict[str, Any]]:
    """List backends that are both registered and enabled in config."""
    gen = getattr(settings, "generation", None)
    if not gen:
        return []
    from workflow_dataset.generate import list_backends
    enabled = []
    for meta in list_backends():
        name = meta.backend_name
        if name == "mock" and getattr(gen, "generation_enable_demo_backend", False):
            enabled.append({"name": name, "type": meta.backend_type, "families": meta.supported_families})
        elif name == "document" and getattr(gen, "generation_enable_document_backend", False):
            enabled.append({"name": name, "type": meta.backend_type, "families": meta.supported_families})
        elif name == "image_demo" and getattr(gen, "generation_enable_image_demo_backend", False):
            enabled.append({"name": name, "type": meta.backend_type, "families": meta.supported_families})
    return enabled


def run_generation_backend_from_console(
    settings: Settings,
    generation_id: str,
    backend: str,
    use_llm: bool = False,
    allow_fallback: bool = True,
) -> tuple[bool, str, list[str]]:
    """
    Run a generation backend in sandbox for the given generation_id. Returns (success, message, output_paths).
    """
    gen = getattr(settings, "generation", None)
    if not gen:
        return False, "Generation config missing", []
    root = Path(getattr(gen, "generation_workspace_root", "data/local/generation"))
    if backend == "mock" and not getattr(gen, "generation_enable_demo_backend", False):
        return False, "Mock backend is disabled", []
    if backend == "document" and not getattr(gen, "generation_enable_document_backend", False):
        return False, "Document backend is disabled", []
    if backend == "image_demo" and not getattr(gen, "generation_enable_image_demo_backend", False):
        return False, "Image demo backend is disabled", []
    from workflow_dataset.generate.sandbox_generation_store import (
        load_generation_manifest,
        load_packs_for_manifest,
        save_generation_manifest,
    )
    from workflow_dataset.generate.backend_registry import execute_generation, get_backend
    from workflow_dataset.generate.generate_models import GenerationRequest, GenerationStatus
    import json
    if get_backend(backend) is None:
        return False, f"Unknown backend: {backend}", []
    req_path = root / "requests" / f"{generation_id}.json"
    if not req_path.exists():
        return False, f"Generation request not found: {generation_id}", []
    req_data = json.loads(req_path.read_text(encoding="utf-8"))
    req_data["status"] = GenerationStatus(req_data.get("status", "planned_only"))
    request = GenerationRequest.model_validate(req_data)
    manifest_id = None
    for p in (root / "manifests").glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if data.get("generation_id") == generation_id:
                manifest_id = p.stem
                break
        except Exception:
            continue
    manifest = load_generation_manifest(manifest_id, root) if manifest_id else None
    if not manifest:
        return False, "Manifest not found for this generation", []
    load_packs_for_manifest(manifest, root)
    workspace_path = root / generation_id
    workspace_path.mkdir(parents=True, exist_ok=True)
    use_llm = use_llm and getattr(gen, "generation_backend_allow_llm", False)
    allow_fallback = allow_fallback and getattr(gen, "generation_backend_fallback_enabled", True)
    ok, msg, output_paths, execution_record = execute_generation(
        backend,
        request,
        manifest,
        workspace_path,
        prompt_packs=manifest.prompt_packs,
        asset_plans=manifest.asset_plans,
        style_packs=manifest.style_packs,
        use_llm=use_llm,
        allow_fallback=allow_fallback,
    )
    manifest.backend_requested = backend
    manifest.generated_output_paths = list(manifest.generated_output_paths or []) + output_paths
    if execution_record:
        manifest.execution_records = list(manifest.execution_records or []) + [execution_record]
    manifest.backend_executed = backend
    manifest.status = GenerationStatus.BACKEND_EXECUTED if ok else GenerationStatus.BACKEND_FAILED
    save_generation_manifest(manifest, root)
    return ok, msg, output_paths


def get_generation_review_preview(
    settings: Settings,
    generation_id: str,
) -> list[tuple[Any, str]]:
    """Get review previews for all generated outputs of a generation. Returns list of (review, preview_text)."""
    gen = getattr(settings, "generation", None)
    if not gen or not getattr(gen, "generation_preview_enabled", True):
        return []
    root = Path(getattr(gen, "generation_workspace_root", "data/local/generation"))
    from workflow_dataset.generate.sandbox_generation_store import load_generation_manifest, load_packs_for_manifest
    from workflow_dataset.review.artifact_preview import preview_artifacts_from_manifest

    manifest = None
    for p in (root / "manifests").glob("*.json"):
        m = load_generation_manifest(p.stem, root)
        if m and m.generation_id == generation_id:
            manifest = m
            load_packs_for_manifest(manifest, root)
            break
    workspace_path = root / generation_id
    paths = list(manifest.generated_output_paths or []) if manifest else []
    if not paths and workspace_path.exists():
        paths = [str(f) for f in workspace_path.rglob("*") if f.is_file()]
    if not paths:
        return []
    return preview_artifacts_from_manifest(
        paths,
        workspace_path,
        generation_id=generation_id,
        execution_records=manifest.execution_records if manifest else None,
        style_pack_refs=manifest.style_pack_refs if manifest else [],
        prompt_pack_refs=manifest.prompt_pack_refs if manifest else [],
    )


def run_generation_refine_from_console(
    settings: Settings,
    generation_id: str,
    artifact_path: str,
    use_llm: bool = False,
    instruction: str = "",
) -> tuple[bool, str, list[str]]:
    """Refine a generated document. Returns (success, message, output_paths)."""
    gen = getattr(settings, "generation", None)
    if not gen or not getattr(gen, "generation_refinement_enabled", True):
        return False, "Refinement is disabled", []
    root = Path(getattr(gen, "generation_workspace_root", "data/local/generation"))
    workspace_path = root / generation_id
    review_root = root / "review"
    art_path = Path(artifact_path)
    if not art_path.is_absolute():
        art_path = workspace_path / artifact_path
    from workflow_dataset.review import build_refine_request, refine_document, get_llm_refine_fn_for_review
    req = build_refine_request(
        artifact_id=art_path.stem,
        generation_id=generation_id,
        use_llm=use_llm and getattr(gen, "generation_refinement_default_use_llm", False) or use_llm,
        user_instruction=instruction,
    )
    llm_fn = get_llm_refine_fn_for_review(Path("configs/llm_training.yaml")) if req.use_llm else None
    ok, msg, out_paths, _ = refine_document(
        art_path,
        workspace_path,
        req,
        style_packs=[],
        prompt_packs=[],
        llm_refine_fn=llm_fn,
        generation_id=generation_id,
        review_store_path=review_root,
    )
    return ok, msg, out_paths or []


def create_adoption_candidate_from_console(
    settings: Settings,
    generation_id: str,
    candidate_paths: list[str],
    target_project_id: str = "",
) -> dict[str, Any] | None:
    """Create adoption candidate and optionally set state for Apply flow. Returns candidate dict or None."""
    gen = getattr(settings, "generation", None)
    if not gen or not getattr(gen, "generation_adoption_bridge_enabled", True):
        return None
    root = Path(getattr(gen, "generation_workspace_root", "data/local/generation"))
    workspace_path = root / generation_id
    if not workspace_path.exists():
        return None
    from workflow_dataset.review import create_adoption_candidate, save_adoption_candidate
    candidate = create_adoption_candidate(
        generation_id=generation_id,
        workspace_path=workspace_path,
        candidate_paths=candidate_paths,
        target_project_id=target_project_id,
    )
    save_adoption_candidate(candidate, root / "review")
    return {
        "adoption_id": candidate.adoption_id,
        "workspace_path": candidate.workspace_path,
        "candidate_paths": candidate.candidate_paths,
        "generation_id": candidate.generation_id,
    }


def run_generation_plan_from_console(
    settings: Settings,
    session_id: str | None = None,
    project_id: str = "",
    generation_type: str = "image_pack",
    source_ref: str = "",
    source_type: str = "project",
) -> tuple[str, str]:
    """
    Run full generation plan (style pack + prompt packs + asset plan). Returns (generation_id, workspace_path).
    """
    setup = getattr(settings, "setup", None)
    if not setup:
        raise ValueError("Setup config missing")
    gen = getattr(settings, "generation", None)
    if not gen or not getattr(gen, "generation_enabled", True):
        raise ValueError("Generation is disabled")
    sid = session_id or _resolve_latest_session_id(settings) or ""
    graph_path = Path(getattr(settings.paths, "graph_store_path", "data/local/work_graph.sqlite"))
    workspace_root = Path(getattr(gen, "generation_workspace_root", "data/local/generation"))

    from workflow_dataset.generate.run_generation import run_generation_plan
    request, manifest, ws_path = run_generation_plan(
        graph_path=graph_path,
        style_signals_dir=setup.style_signals_dir,
        parsed_artifacts_dir=setup.parsed_artifacts_dir,
        style_profiles_dir=getattr(setup, "style_profiles_dir", "data/local/style_profiles"),
        suggestions_dir=getattr(setup, "suggestions_dir", "data/local/suggestions"),
        draft_structures_dir=getattr(setup, "draft_structures_dir", "data/local/draft_structures"),
        generation_workspace_root=workspace_root,
        setup_session_id=sid,
        project_id=project_id,
        domain="",
        source_ref=source_ref,
        source_type=source_type,
        generation_type=generation_type,
        use_llm=getattr(gen, "generation_default_use_llm", False),
        allow_style_packs=getattr(gen, "generation_allow_style_packs", True),
        allow_prompt_packs=getattr(gen, "generation_allow_prompt_packs", True),
        allow_asset_plans=getattr(gen, "generation_allow_asset_plans", True),
        persist_to_graph=getattr(gen, "generation_graph_persistence", True),
    )
    return request.generation_id, ws_path


def create_bundle_from_console(
    settings: Settings,
    adapter_type: str,
    generation_id: str = "",
    artifact_path: str = "",
    project_id: str = "",
    domain: str = "",
    populate: bool = True,
) -> tuple[str, list[str], dict[str, Any]] | None:
    """Create an output bundle. Returns (bundle_id, output_paths, info) or None. info has populated_paths, xlsx_created."""
    oa = getattr(settings, "output_adapters", None)
    if not oa or not getattr(oa, "output_adapters_enabled", True):
        return None
    from workflow_dataset.output_adapters import create_bundle, get_adapter
    from workflow_dataset.output_adapters.adapter_models import OutputAdapterRequest
    from workflow_dataset.utils.dates import utc_now_iso
    from workflow_dataset.utils.hashes import stable_id
    if get_adapter(adapter_type) is None:
        return None
    bundle_root = Path(getattr(oa, "output_adapter_bundle_root", "data/local/bundles"))
    bundle_root.mkdir(parents=True, exist_ok=True)
    ts = utc_now_iso()
    req_id = stable_id("adreq", adapter_type, generation_id or ts, prefix="adreq")
    request = OutputAdapterRequest(
        adapter_request_id=req_id,
        generation_id=generation_id,
        review_id="",
        artifact_id="",
        project_id=project_id,
        domain=domain,
        adapter_type=adapter_type,
        source_artifact_path=artifact_path,
        workspace_path=str(bundle_root),
        created_utc=ts,
    )
    population_enabled = getattr(oa, "output_adapter_population_enabled", True)
    do_populate = populate and population_enabled and bool(artifact_path)
    allow_xlsx = getattr(oa, "output_adapter_allow_xlsx", False)
    max_rows = getattr(oa, "output_adapter_population_max_rows", 1000)
    max_sections = getattr(oa, "output_adapter_population_max_sections", 50)
    result = create_bundle(
        adapter_type,
        request,
        workspace_path=bundle_root,
        bundle_store_path=bundle_root,
        source_artifact_path=artifact_path or "",
        revision_note="",
        populate=do_populate,
        allow_xlsx=allow_xlsx,
        population_max_rows=max_rows,
        population_max_sections=max_sections,
    )
    if not result:
        return None
    bundle, manifest = result
    if getattr(oa, "output_adapter_graph_persistence", True):
        graph_path = Path(getattr(settings.paths, "graph_store_path", "data/local/work_graph.sqlite"))
        if graph_path.exists():
            from workflow_dataset.output_adapters.graph_integration import persist_adapter_request, persist_output_bundle
            persist_adapter_request(graph_path, request)
            persist_output_bundle(graph_path, bundle, manifest)
    info: dict[str, Any] = {
        "populated_paths": getattr(manifest, "populated_paths", []) or [],
        "scaffold_only_paths": getattr(manifest, "scaffold_only_paths", []) or [],
        "fallback_used": getattr(manifest, "fallback_used", False),
        "xlsx_created": getattr(manifest, "xlsx_created", False),
    }
    return bundle.bundle_id, bundle.output_paths, info


def list_bundles_for_console(settings: Settings, limit: int = 20) -> list[dict[str, Any]]:
    """List output bundles for console."""
    oa = getattr(settings, "output_adapters", None)
    if not oa:
        return []
    from workflow_dataset.output_adapters import list_bundles
    bundle_root = Path(getattr(oa, "output_adapter_bundle_root", "data/local/bundles"))
    return list_bundles(bundle_root, limit=limit)


def adopt_bundle_for_console(
    settings: Settings,
    bundle_id: str,
) -> dict[str, Any] | None:
    """Create adoption candidate for a bundle; return candidate dict for state."""
    oa = getattr(settings, "output_adapters", None)
    if not oa:
        return None
    from workflow_dataset.output_adapters import load_manifest_for_bundle
    from workflow_dataset.review.adoption_bridge import create_adoption_candidate, save_adoption_candidate
    bundle_root = Path(getattr(oa, "output_adapter_bundle_root", "data/local/bundles"))
    manifest = load_manifest_for_bundle(bundle_id, bundle_root)
    if not manifest:
        return None
    workspace_path = bundle_root / bundle_id
    if not workspace_path.exists():
        return None
    candidate = create_adoption_candidate(
        generation_id=bundle_id,
        workspace_path=workspace_path,
        candidate_paths=manifest.generated_paths,
        artifact_id=bundle_id,
    )
    gen = getattr(settings, "generation", None)
    review_root = Path(getattr(gen, "generation_workspace_root", "data/local/generation")) / "review" if gen else bundle_root / "review"
    review_root.mkdir(parents=True, exist_ok=True)
    save_adoption_candidate(candidate, review_root)
    return {
        "adoption_id": candidate.adoption_id,
        "workspace_path": candidate.workspace_path,
        "candidate_paths": candidate.candidate_paths,
        "generation_id": bundle_id,
    }


def get_home_counts(settings: Settings, session_id: str | None = None) -> dict[str, int]:
    """Aggregate counts for home screen: projects, domains, styles, suggestions, drafts, workspaces, applies (rollback count), generations."""
    sid = session_id or _resolve_latest_session_id(settings)
    projects = get_projects(settings)
    context = get_assistive_context(settings, sid) if sid else {}
    domains = context.get("domains") or []
    profiles = get_style_profiles(settings)
    suggestions = get_suggestions(settings)
    drafts = get_drafts(settings)
    workspaces = get_workspaces(settings, session_id=sid or "", limit=100)
    rollbacks = list_rollback_records(settings)
    generations = get_generation_requests(settings, session_id=sid or "", limit=100) if getattr(settings, "generation", None) else []
    return {
        "sessions": len(get_setup_sessions(settings)),
        "projects": len(projects),
        "domains": len(domains),
        "style_profiles": len(profiles),
        "suggestions": len(suggestions),
        "drafts": len(drafts),
        "workspaces": len(workspaces),
        "rollback_records": len(rollbacks),
        "generations": len(generations),
    }


def get_llm_status(runs_dir: Path | str | None = None) -> dict[str, Any]:
    """LLM training status for console: latest run type, smoke/full adapter availability, comparison report path."""
    rdir = Path(runs_dir) if runs_dir else Path("data/local/llm/runs")
    out: dict[str, Any] = {
        "latest_run_type": None,
        "smoke_available": False,
        "full_available": False,
        "comparison_report": None,
        "latest_run_dir": None,
    }
    if not rdir.exists():
        return out
    try:
        from workflow_dataset.llm.run_summary import (
            find_latest_successful_adapter,
            find_latest_successful_adapter_by_type,
            get_run_type,
        )
        adapter_path, run_dir = find_latest_successful_adapter(rdir)
        if run_dir:
            out["latest_run_dir"] = run_dir
            out["latest_run_type"] = get_run_type(Path(run_dir))
        smoke_path, _ = find_latest_successful_adapter_by_type(rdir, "smoke")
        full_path, _ = find_latest_successful_adapter_by_type(rdir, "full")
        out["smoke_available"] = bool(smoke_path)
        out["full_available"] = bool(full_path)
        report = rdir / "comparison_latest.md"
        if report.exists():
            out["comparison_report"] = str(report)
    except Exception:
        pass
    return out


def get_trials_status(trials_dir: Path | str | None = None) -> dict[str, Any]:
    """Workflow trials status for console: available trials, result count, report path."""
    from workflow_dataset.trials.trial_registry import list_trials
    from workflow_dataset.trials.trial_scenarios import register_all_trials
    if not list_trials():
        register_all_trials()
    trials = list_trials()
    out: dict[str, Any] = {
        "trial_count": len(trials),
        "domains": list({t.domain for t in trials if t.domain}),
        "report_path": None,
        "result_count": 0,
    }
    base = Path(trials_dir) if trials_dir else Path("data/local/trials")
    if base.exists():
        report = base / "latest_trial_report.md"
        if report.exists():
            out["report_path"] = str(report)
        out["result_count"] = len(list(base.glob("res_*.json")))
    return out
