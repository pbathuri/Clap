"""
Tests for M13/M14 toolchain-native output adapters and content-aware population.
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


# ----- M14 content extraction and population -----


def test_content_extraction_markdown() -> None:
    from workflow_dataset.output_adapters.content_extractors import (
        extract_content,
        get_first_table,
        get_narrative_sections,
    )
    md = "# Goals\n\nWe need to ship by Q2.\n\n## Tasks\n\n| id | title |\n|----|-------|\n| 1 | Alpha |\n| 2 | Beta |"
    slices = extract_content(md, source_artifact_ref="art1", max_sections=20)
    assert len(slices) >= 1
    table = get_first_table(slices)
    assert table is not None
    headers, rows = table
    assert "id" in headers or "title" in headers
    assert len(rows) >= 2
    sections = get_narrative_sections(slices)
    assert any("ship" in t for _, t in sections)


def test_content_extraction_csv() -> None:
    from workflow_dataset.output_adapters.content_extractors import extract_content, get_first_table
    csv_content = "name,value\nA,1\nB,2\nC,3"
    slices = extract_content(csv_content, source_artifact_ref="art1", source_path="x.csv")
    assert len(slices) == 1
    table = get_first_table(slices)
    assert table is not None
    headers, rows = table
    assert headers == ["name", "value"]
    assert len(rows) == 3


def test_spreadsheet_populated(bundle_root: Path, sample_request: OutputAdapterRequest) -> None:
    sample_request.adapter_type = "spreadsheet"
    adapter = SpreadsheetAdapter()
    bundle_root.mkdir(parents=True, exist_ok=True)
    source = "id,label,value\nr1,First,10\nr2,Second,20"
    bundle, manifest = adapter.create_bundle(
        sample_request,
        bundle_root,
        source_content=source,
        populate=True,
    )
    assert bundle.bundle_id
    data_path = bundle_root / bundle.bundle_id / "data.csv"
    assert data_path.exists()
    content = data_path.read_text(encoding="utf-8")
    assert "r1" in content and "First" in content and "10" in content
    assert len(manifest.populated_paths) >= 1
    assert any("data.csv" in p for p in manifest.populated_paths)


def test_spreadsheet_xlsx_when_enabled(bundle_root: Path, sample_request: OutputAdapterRequest) -> None:
    sample_request.adapter_type = "spreadsheet"
    adapter = SpreadsheetAdapter()
    bundle_root.mkdir(parents=True, exist_ok=True)
    bundle, manifest = adapter.create_bundle(
        sample_request,
        bundle_root,
        source_content="x,y\n1,2",
        populate=True,
        allow_xlsx=True,
    )
    xlsx_path = bundle_root / bundle.bundle_id / "workbook.xlsx"
    if xlsx_path.exists():
        assert manifest.xlsx_created is True
        assert any("workbook.xlsx" in p for p in bundle.output_paths)
    else:
        assert manifest.xlsx_created is False


def test_creative_package_populated(bundle_root: Path, sample_request: OutputAdapterRequest) -> None:
    sample_request.adapter_type = "creative_package"
    adapter = CreativePackageAdapter()
    bundle_root.mkdir(parents=True, exist_ok=True)
    source = "# Objective\n\nLaunch the campaign by Friday.\n\n- [ ] Brief approved\n- [ ] Assets ready"
    bundle, manifest = adapter.create_bundle(
        sample_request,
        bundle_root,
        source_content=source,
        populate=True,
    )
    brief_path = bundle_root / bundle.bundle_id / "brief" / "creative_brief.md"
    assert brief_path.exists()
    brief_text = brief_path.read_text(encoding="utf-8")
    assert "Objective" in brief_text or "campaign" in brief_text or "Friday" in brief_text
    assert len(manifest.populated_paths) >= 1 or "Launch" in brief_text


def test_design_package_populated(bundle_root: Path, sample_request: OutputAdapterRequest) -> None:
    sample_request.adapter_type = "design_package"
    adapter = DesignPackageAdapter()
    bundle_root.mkdir(parents=True, exist_ok=True)
    source = "# Scope\n\nDeliver drawings and presentation deck.\n\n| ID | Desc |\n|----|------|\n| 1 | Rev A |"
    bundle, manifest = adapter.create_bundle(
        sample_request,
        bundle_root,
        source_content=source,
        populate=True,
    )
    brief_path = bundle_root / bundle.bundle_id / "brief" / "design_brief.md"
    assert brief_path.exists()
    assert "Scope" in brief_path.read_text(encoding="utf-8") or "drawings" in brief_path.read_text(encoding="utf-8")


def test_ops_handoff_populated(bundle_root: Path, sample_request: OutputAdapterRequest) -> None:
    sample_request.adapter_type = "ops_handoff"
    adapter = OpsHandoffAdapter()
    bundle_root.mkdir(parents=True, exist_ok=True)
    source = "# Summary\n\nWeekly review complete.\n\n| id | item | status |\n|----|------|--------|\n| 1 | Task A | done |"
    bundle, manifest = adapter.create_bundle(
        sample_request,
        bundle_root,
        source_content=source,
        populate=True,
    )
    report_path = bundle_root / bundle.bundle_id / "report.md"
    assert report_path.exists()
    assert "Summary" in report_path.read_text(encoding="utf-8") or "review" in report_path.read_text(encoding="utf-8")
    tracker_path = bundle_root / bundle.bundle_id / "tracker.csv"
    assert tracker_path.exists()


def test_manifest_provenance(bundle_root: Path, sample_request: OutputAdapterRequest) -> None:
    bundle_root.mkdir(parents=True, exist_ok=True)
    result = create_bundle(
        "spreadsheet",
        sample_request,
        workspace_path=bundle_root,
        bundle_store_path=bundle_root,
        source_artifact_path="",
        populate=True,
    )
    assert result is not None
    _, manifest = result
    assert hasattr(manifest, "populated_paths")
    assert hasattr(manifest, "scaffold_only_paths")
    assert hasattr(manifest, "fallback_used")
    assert isinstance(manifest.fallback_used, bool)


def test_list_bundles_includes_population(
    bundle_root: Path, sample_request: OutputAdapterRequest, tmp_path: Path
) -> None:
    bundle_root.mkdir(parents=True, exist_ok=True)
    source_file = tmp_path / "source.csv"
    source_file.write_text("a,b\n1,2", encoding="utf-8")
    sample_request.source_artifact_path = str(source_file)
    result = create_bundle(
        "spreadsheet",
        sample_request,
        workspace_path=bundle_root,
        bundle_store_path=bundle_root,
        source_artifact_path=str(source_file),
        populate=True,
    )
    assert result is not None
    save_bundle_manifest(result[1], bundle_root)
    items = list_bundles(bundle_root, limit=5)
    assert len(items) >= 1
    assert "populated_paths" in items[0]
    assert "xlsx_created" in items[0]
