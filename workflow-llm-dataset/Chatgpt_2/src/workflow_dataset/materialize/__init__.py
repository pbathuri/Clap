"""
Sandboxed artifact materialization (M7).

Generates real local artifacts in a safe workspace only.
No writes to user's real filesystem.
"""

from __future__ import annotations

from workflow_dataset.materialize.materialize_models import (
    MaterializationRequest,
    MaterializedArtifact,
    MaterializationManifest,
)
from workflow_dataset.materialize.workspace_manager import (
    create_workspace,
    get_workspace_path,
    list_workspaces,
    ensure_workspace_dir,
)
from workflow_dataset.materialize.artifact_builder import materialize_from_draft, materialize_from_suggestion
from workflow_dataset.materialize.manifest_store import save_manifest, load_manifest
from workflow_dataset.materialize.preview_renderer import render_preview

__all__ = [
    "MaterializationRequest",
    "MaterializedArtifact",
    "MaterializationManifest",
    "create_workspace",
    "get_workspace_path",
    "list_workspaces",
    "ensure_workspace_dir",
    "materialize_from_draft",
    "materialize_from_suggestion",
    "save_manifest",
    "load_manifest",
    "render_preview",
]
