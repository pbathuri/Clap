"""
Persist generation scaffolding entities in the personal graph (M10).

Nodes: generation_request, style_pack, prompt_pack, asset_plan, generation_manifest.
Edges: generation_for_project, generation_uses_style_profile, generation_uses_imitation_candidate,
       style_pack_supports_generation, prompt_pack_generated_for_request, asset_plan_generated_for_request,
       generation_manifest_for_workspace.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from workflow_dataset.personal.graph_store import init_store, add_node, add_edge, get_node
from workflow_dataset.personal.work_graph import NodeType, PersonalWorkGraphNode
from workflow_dataset.utils.dates import utc_now_iso

from workflow_dataset.generate.generate_models import (
    GenerationRequest,
    StylePack,
    PromptPack,
    AssetPlan,
    GenerationManifest,
)


def _ensure_conn(conn_or_path: sqlite3.Connection | Path | str) -> sqlite3.Connection:
    if isinstance(conn_or_path, sqlite3.Connection):
        return conn_or_path
    path = Path(conn_or_path)
    init_store(path)
    return sqlite3.connect(str(path))


def persist_generation_request(
    conn_or_path: sqlite3.Connection | Path | str,
    request: GenerationRequest,
    project_id: str = "",
) -> None:
    """Write generation request node and generation_for_project edge."""
    conn = _ensure_conn(conn_or_path)
    ts = getattr(request, "created_utc", None) or utc_now_iso()
    proj_id = project_id or getattr(request, "project_id", "")
    try:
        node = PersonalWorkGraphNode(
            node_id=request.generation_id,
            node_type=NodeType.GENERATION_REQUEST,
            label=request.generation_type or "generation",
            attributes={
                "session_id": request.session_id,
                "project_id": request.project_id,
                "domain": request.domain,
                "generation_type": request.generation_type,
                "source_ref": request.source_ref,
                "source_type": request.source_type,
                "status": getattr(request.status, "value", str(request.status)),
            },
            source="generate",
            created_utc=ts,
            updated_utc=ts,
            confidence=0.8,
        )
        add_node(conn, node)
        if proj_id and get_node(conn, proj_id):
            add_edge(conn, proj_id, request.generation_id, "generation_for_project")
        if not isinstance(conn_or_path, sqlite3.Connection):
            conn.commit()
    finally:
        if not isinstance(conn_or_path, sqlite3.Connection):
            conn.close()


def persist_style_pack_node(
    conn_or_path: sqlite3.Connection | Path | str,
    pack: StylePack,
    generation_id: str,
) -> None:
    """Write style_pack node and style_pack_supports_generation edge."""
    conn = _ensure_conn(conn_or_path)
    ts = pack.created_utc or utc_now_iso()
    try:
        node = PersonalWorkGraphNode(
            node_id=pack.style_pack_id,
            node_type=NodeType.STYLE_PACK,
            label=pack.domain or "style_pack",
            attributes={
                "project_id": pack.project_id,
                "domain": pack.domain,
                "style_profile_refs": pack.style_profile_refs[:10],
            },
            source="generate",
            created_utc=ts,
            updated_utc=ts,
            confidence=0.8,
        )
        add_node(conn, node)
        add_edge(conn, pack.style_pack_id, generation_id, "style_pack_supports_generation")
        for ref in pack.style_profile_refs[:5]:
            if get_node(conn, ref):
                add_edge(conn, generation_id, ref, "generation_uses_style_profile")
        for ref in pack.imitation_candidate_refs[:5]:
            if get_node(conn, ref):
                add_edge(conn, generation_id, ref, "generation_uses_imitation_candidate")
        if not isinstance(conn_or_path, sqlite3.Connection):
            conn.commit()
    finally:
        if not isinstance(conn_or_path, sqlite3.Connection):
            conn.close()


def persist_prompt_pack_node(
    conn_or_path: sqlite3.Connection | Path | str,
    pack: PromptPack,
) -> None:
    """Write prompt_pack node and prompt_pack_generated_for_request edge."""
    conn = _ensure_conn(conn_or_path)
    ts = pack.created_utc or utc_now_iso()
    try:
        node = PersonalWorkGraphNode(
            node_id=pack.prompt_pack_id,
            node_type=NodeType.PROMPT_PACK,
            label=pack.prompt_family or "prompt_pack",
            attributes={
                "generation_id": pack.generation_id,
                "prompt_family": pack.prompt_family,
            },
            source="generate",
            created_utc=ts,
            updated_utc=ts,
            confidence=0.8,
        )
        add_node(conn, node)
        if pack.generation_id:
            add_edge(conn, pack.prompt_pack_id, pack.generation_id, "prompt_pack_generated_for_request")
        if not isinstance(conn_or_path, sqlite3.Connection):
            conn.commit()
    finally:
        if not isinstance(conn_or_path, sqlite3.Connection):
            conn.close()


def persist_asset_plan_node(
    conn_or_path: sqlite3.Connection | Path | str,
    plan: AssetPlan,
) -> None:
    """Write asset_plan node and asset_plan_generated_for_request edge."""
    conn = _ensure_conn(conn_or_path)
    ts = plan.created_utc or utc_now_iso()
    try:
        node = PersonalWorkGraphNode(
            node_id=plan.asset_plan_id,
            node_type=NodeType.ASSET_PLAN,
            label="asset_plan",
            attributes={
                "generation_id": plan.generation_id,
                "target_outputs": plan.target_outputs[:10],
            },
            source="generate",
            created_utc=ts,
            updated_utc=ts,
            confidence=0.8,
        )
        add_node(conn, node)
        if plan.generation_id:
            add_edge(conn, plan.asset_plan_id, plan.generation_id, "asset_plan_generated_for_request")
        if not isinstance(conn_or_path, sqlite3.Connection):
            conn.commit()
    finally:
        if not isinstance(conn_or_path, sqlite3.Connection):
            conn.close()


def persist_generation_manifest_node(
    conn_or_path: sqlite3.Connection | Path | str,
    manifest: GenerationManifest,
) -> None:
    """Write generation_manifest node and generation_manifest_for_workspace relation."""
    conn = _ensure_conn(conn_or_path)
    ts = manifest.created_utc or utc_now_iso()
    try:
        node = PersonalWorkGraphNode(
            node_id=manifest.manifest_id,
            node_type=NodeType.GENERATION_MANIFEST,
            label="generation_manifest",
            attributes={
                "generation_id": manifest.generation_id,
                "workspace_path": manifest.workspace_path[:500],
                "backend_executed": manifest.backend_executed,
                "status": getattr(manifest.status, "value", str(manifest.status)),
            },
            source="generate",
            created_utc=ts,
            updated_utc=ts,
            confidence=0.8,
        )
        add_node(conn, node)
        if manifest.generation_id:
            add_edge(conn, manifest.manifest_id, manifest.generation_id, "generation_manifest_for_request")
        if not isinstance(conn_or_path, sqlite3.Connection):
            conn.commit()
    finally:
        if not isinstance(conn_or_path, sqlite3.Connection):
            conn.close()


def persist_generation_to_graph(
    conn_or_path: sqlite3.Connection | Path | str,
    request: GenerationRequest,
    style_packs: list[StylePack],
    prompt_packs: list[PromptPack],
    asset_plans: list[AssetPlan],
    manifest: GenerationManifest,
    project_id: str = "",
) -> None:
    """Persist full generation run to graph: request, style packs, prompt packs, asset plans, manifest."""
    persist_generation_request(conn_or_path, request, project_id=project_id or request.project_id)
    for sp in style_packs:
        persist_style_pack_node(conn_or_path, sp, request.generation_id)
    for pp in prompt_packs:
        persist_prompt_pack_node(conn_or_path, pp)
    for ap in asset_plans:
        persist_asset_plan_node(conn_or_path, ap)
    persist_generation_manifest_node(conn_or_path, manifest)
