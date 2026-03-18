"""
M13: Persist output bundle and adapter request nodes in the personal work graph.

Local-only; inspectable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.output_adapters.adapter_models import (
    OutputAdapterRequest,
    OutputBundle,
    OutputBundleManifest,
)
from workflow_dataset.personal.work_graph import (
    NodeType,
    PersonalWorkGraphNode,
)
from workflow_dataset.utils.dates import utc_now_iso


def persist_adapter_request(
    graph_path: Path | str,
    request: OutputAdapterRequest,
) -> None:
    """Write adapter_request node to graph."""
    import sqlite3
    from workflow_dataset.personal.graph_store import add_node as _add_node, init_store

    graph_path = Path(graph_path)
    if not graph_path.exists():
        return
    init_store(graph_path)
    node = PersonalWorkGraphNode(
        node_id=request.adapter_request_id,
        node_type=NodeType.ADAPTER_REQUEST,
        label=f"Adapter request {request.adapter_type}",
        attributes={
            "generation_id": request.generation_id,
            "review_id": request.review_id,
            "artifact_id": request.artifact_id,
            "project_id": request.project_id,
            "domain": request.domain,
            "adapter_type": request.adapter_type,
        },
        source="output_adapter",
        created_utc=request.created_utc or utc_now_iso(),
        updated_utc=utc_now_iso(),
    )
    conn = sqlite3.connect(str(graph_path))
    try:
        _add_node(conn, node)
        conn.commit()
    finally:
        conn.close()


def persist_output_bundle(
    graph_path: Path | str,
    bundle: OutputBundle,
    manifest: OutputBundleManifest,
) -> None:
    """Write output_bundle and bundle_manifest nodes; link to adapter_request."""
    import sqlite3
    from workflow_dataset.personal.graph_store import add_edge, add_node as _add_node, init_store

    graph_path = Path(graph_path)
    if not graph_path.exists():
        return
    init_store(graph_path)
    conn = sqlite3.connect(str(graph_path))
    try:
        bundle_node = PersonalWorkGraphNode(
            node_id=bundle.bundle_id,
            node_type=NodeType.OUTPUT_BUNDLE,
            label=f"Bundle {bundle.bundle_type}",
            attributes={
                "adapter_request_id": bundle.adapter_request_id,
                "bundle_type": bundle.bundle_type,
                "workspace_path": bundle.workspace_path,
                "output_paths": bundle.output_paths[:50],
            },
            source="output_adapter",
            created_utc=bundle.created_utc or utc_now_iso(),
            updated_utc=utc_now_iso(),
        )
        _add_node(conn, bundle_node)
        manifest_node = PersonalWorkGraphNode(
            node_id=manifest.manifest_id,
            node_type=NodeType.BUNDLE_MANIFEST,
            label=f"Manifest {manifest.bundle_id}",
            attributes={
                "bundle_id": manifest.bundle_id,
                "adapter_used": manifest.adapter_used,
            },
            source="output_adapter",
            created_utc=manifest.created_utc or utc_now_iso(),
            updated_utc=utc_now_iso(),
        )
        _add_node(conn, manifest_node)
        add_edge(conn, manifest.manifest_id, bundle.bundle_id, "manifest_for_bundle")
        if bundle.adapter_request_id:
            add_edge(conn, bundle.bundle_id, bundle.adapter_request_id, "bundle_generated_from_request")
        conn.commit()
    finally:
        conn.close()
