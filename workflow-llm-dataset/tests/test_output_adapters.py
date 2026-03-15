"""
Tests for M13 toolchain-native output adapters.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.output_adapters.adapter_models import (
    OutputAdapterRequest,
    OutputBundle,
    OutputBundleManifest,
)
from workflow_dataset.output_adapters.adapter_registry import (
    get_adapter,
    list_adapters,
    create_bundle,
)
from workflow_dataset.output_adapters.bundle_manifest import (
    save_bundle_manifest,
    load_bundle_manifest,
    load_manifest_for_bundle,
    list_bundles,
)
from workflow_dataset.output_adapters.spreadsheet_adapter import SpreadsheetAdapter
from workflow_dataset.output_adapters.creative_package_adapter import CreativePackageAdapter
from workflow_dataset.output_adapters.design_package_adapter import DesignPackageAdapter
from workflow_dataset.output_adapters.ops_handoff_adapter import OpsHandoffAdapter
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


@pytest.fixture
def bundle_root(tmp_path: Path) -> Path:
    return tmp_path / "bundles"


@pytest.fixture
def sample_request(bundle_root: Path) -> OutputAdapterRequest:
    ts = utc_now_iso()
    return OutputAdapterRequest(
        adapter_request_id=stable_id("adreq", "spreadsheet", ts, prefix="adreq"),
        generation_id="gen_1",
        review_id="rev_1",
        artifact_id="art_1",
        project_id="proj_1",
        domain="finance",
        adapter_type="spreadsheet",
        created_utc=ts,
        workspace_path=str(bundle_root),
    )


def test_adapter_registry() -> None:
    adapters = list_adapters()
    types = [m.adapter_type for m in adapters]
    assert "spreadsheet" in types
    assert "creative_package" in types
    assert "design_package" in types
    assert "ops_handoff" in types
    entry = get_adapter("spreadsheet")
    assert entry is not None
    adapter, meta = entry
    assert meta.label
    assert get_adapter("nonexistent") is None


def test_spreadsheet_adapter(bundle_root: Path, sample_request: OutputAdapterRequest) -> None:
    sample_request.adapter_type = "spreadsheet"
    adapter = SpreadsheetAdapter()
    workspace_path = bundle_root
    workspace_path.mkdir(parents=True, exist_ok=True)
    bundle, manifest = adapter.create_bundle(
        sample_request,
        workspace_path,
        source_content="",
        revision_note="",
    )
    assert bundle.bundle_id
    assert bundle.bundle_type == "spreadsheet"
    assert len(bundle.output_paths) >= 5
    assert (workspace_path / bundle.bundle_id / "summary.csv").exists()
    assert (workspace_path / bundle.bundle_id / "data.csv").exists()
    assert (workspace_path / bundle.bundle_id / "tab_plan.md").exists()
    assert manifest.adapter_used == "spreadsheet"


def test_creative_package_adapter(bundle_root: Path, sample_request: OutputAdapterRequest) -> None:
    sample_request.adapter_type = "creative_package"
    adapter = CreativePackageAdapter()
    workspace_path = bundle_root
    workspace_path.mkdir(parents=True, exist_ok=True)
    bundle, manifest = adapter.create_bundle(
        sample_request,
        workspace_path,
        revision_note="",
    )
    assert bundle.bundle_type == "creative_package"
    assert (workspace_path / bundle.bundle_id / "brief" / "creative_brief.md").exists()
    assert (workspace_path / bundle.bundle_id / "storyboard" / "shotlist.md").exists()
    assert (workspace_path / bundle.bundle_id / "deliverables_checklist.md").exists()


def test_design_package_adapter(bundle_root: Path, sample_request: OutputAdapterRequest) -> None:
    sample_request.adapter_type = "design_package"
    adapter = DesignPackageAdapter()
    workspace_path = bundle_root
    workspace_path.mkdir(parents=True, exist_ok=True)
    bundle, manifest = adapter.create_bundle(
        sample_request,
        workspace_path,
        revision_note="",
    )
    assert bundle.bundle_type == "design_package"
    assert (workspace_path / bundle.bundle_id / "brief" / "design_brief.md").exists()
    assert (workspace_path / bundle.bundle_id / "issue_revision_checklist.md").exists()


def test_ops_handoff_adapter(bundle_root: Path, sample_request: OutputAdapterRequest) -> None:
    sample_request.adapter_type = "ops_handoff"
    adapter = OpsHandoffAdapter()
    workspace_path = bundle_root
    workspace_path.mkdir(parents=True, exist_ok=True)
    bundle, manifest = adapter.create_bundle(
        sample_request,
        workspace_path,
        revision_note="",
    )
    assert bundle.bundle_type == "ops_handoff"
    assert (workspace_path / bundle.bundle_id / "report.md").exists()
    assert (workspace_path / bundle.bundle_id / "tracker.csv").exists()


def test_create_bundle_via_registry(bundle_root: Path, sample_request: OutputAdapterRequest) -> None:
    bundle_root.mkdir(parents=True, exist_ok=True)
    result = create_bundle(
        "spreadsheet",
        sample_request,
        workspace_path=bundle_root,
        bundle_store_path=bundle_root,
    )
    assert result is not None
    bundle, manifest = result
    save_bundle_manifest(manifest, bundle_root)
    loaded = load_bundle_manifest(manifest.manifest_id, bundle_root)
    assert loaded is not None
    assert loaded.bundle_id == bundle.bundle_id


def test_list_bundles(bundle_root: Path, sample_request: OutputAdapterRequest) -> None:
    bundle_root.mkdir(parents=True, exist_ok=True)
    result = create_bundle(
        "ops_handoff",
        sample_request,
        workspace_path=bundle_root,
        bundle_store_path=bundle_root,
    )
    assert result is not None
    _, manifest = result
    save_bundle_manifest(manifest, bundle_root)
    items = list_bundles(bundle_root, limit=10)
    assert len(items) >= 1
    assert items[0]["adapter_used"] == "ops_handoff"


def test_load_manifest_for_bundle(bundle_root: Path, sample_request: OutputAdapterRequest) -> None:
    bundle_root.mkdir(parents=True, exist_ok=True)
    result = create_bundle(
        "design_package",
        sample_request,
        workspace_path=bundle_root,
        bundle_store_path=bundle_root,
    )
    assert result is not None
    bundle, manifest = result
    save_bundle_manifest(manifest, bundle_root)
    m = load_manifest_for_bundle(bundle.bundle_id, bundle_root)
    assert m is not None
    assert m.bundle_id == bundle.bundle_id


def test_graph_integration(tmp_path: Path, bundle_root: Path, sample_request: OutputAdapterRequest) -> None:
    import sqlite3
    from workflow_dataset.personal.work_graph import NodeType
    from workflow_dataset.personal.graph_store import init_store, get_node
    from workflow_dataset.output_adapters.graph_integration import persist_adapter_request, persist_output_bundle

    bundle_root.mkdir(parents=True, exist_ok=True)
    graph_path = tmp_path / "work_graph.sqlite"
    init_store(graph_path)
    persist_adapter_request(graph_path, sample_request)
    result = create_bundle(
        "spreadsheet",
        sample_request,
        workspace_path=bundle_root,
        bundle_store_path=bundle_root,
    )
    assert result is not None
    bundle, manifest = result
    persist_output_bundle(graph_path, bundle, manifest)
    conn = sqlite3.connect(str(graph_path))
    try:
        node = get_node(conn, bundle.bundle_id)
        assert node is not None
        assert node.node_type == NodeType.OUTPUT_BUNDLE
    finally:
        conn.close()
