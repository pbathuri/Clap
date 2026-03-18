"""Tests for M7 sandboxed materialization: workspace, manifest, artifact builders, graph, CLI."""

from __future__ import annotations

from pathlib import Path

import pytest

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
from workflow_dataset.materialize.manifest_store import save_manifest, load_manifest
from workflow_dataset.materialize.preview_renderer import render_preview, render_artifact_tree
from workflow_dataset.materialize.text_artifact_builder import build_text_artifact
from workflow_dataset.materialize.table_artifact_builder import build_csv_artifact, build_tracker_csv_files
from workflow_dataset.materialize.folder_scaffold_builder import build_folder_scaffold, build_project_scaffold
from workflow_dataset.materialize.creative_scaffold_builder import build_creative_folder_scaffold
from workflow_dataset.materialize.artifact_builder import materialize_from_draft, materialize_from_suggestion
from workflow_dataset.materialize.materialize_graph import persist_materialization_nodes
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def test_create_workspace(tmp_path: Path) -> None:
    ws = create_workspace(tmp_path, session_id="s1", request_id="req_abc", project_id="p1")
    assert ws.exists()
    assert ws.is_dir()
    assert "req_abc" in str(ws) or "materialized" in str(ws)


def test_get_workspace_path(tmp_path: Path) -> None:
    p = get_workspace_path(tmp_path, request_id="req_xyz")
    assert "req_xyz" in str(p) or "materialized" in str(p)


def test_ensure_workspace_dir(tmp_path: Path) -> None:
    d = ensure_workspace_dir(tmp_path, "briefs", "notes")
    assert d.exists()
    assert d.is_dir()


def test_list_workspaces(tmp_path: Path) -> None:
    create_workspace(tmp_path, request_id="r1")
    create_workspace(tmp_path, request_id="r2")
    items = list_workspaces(tmp_path, limit=10)
    assert len(items) >= 1


def test_save_load_manifest(tmp_path: Path) -> None:
    m = MaterializationManifest(
        manifest_id="mf_1",
        request_id="req_1",
        output_paths=["a.md", "b.csv"],
        generated_from="project_brief",
        created_utc=utc_now_iso(),
    )
    save_manifest(m, tmp_path)
    loaded = load_manifest(tmp_path)
    assert loaded is not None
    assert loaded.manifest_id == m.manifest_id
    assert loaded.output_paths == m.output_paths


def test_build_text_artifact(tmp_path: Path) -> None:
    art = build_text_artifact(
        tmp_path,
        "project_brief",
        "Project brief",
        "# Project brief\n\n## Objective\n## Scope",
        sections=["Objective", "Scope"],
        request_id="req1",
        draft_ref="draft_1",
    )
    assert art is not None
    assert art.artifact_type == "markdown_brief"
    assert (tmp_path / art.sandbox_path).exists()
    assert "Objective" in (tmp_path / art.sandbox_path).read_text()


def test_build_csv_artifact(tmp_path: Path) -> None:
    art = build_csv_artifact(
        tmp_path,
        "inventory_sheet_scaffold",
        "Inventory",
        request_id="req1",
        draft_ref="draft_1",
    )
    assert art is not None
    assert (tmp_path / art.sandbox_path).exists()
    content = (tmp_path / art.sandbox_path).read_text()
    assert "Item ID" in content or "Quantity" in content


def test_build_tracker_csv_files(tmp_path: Path) -> None:
    arts = build_tracker_csv_files(
        tmp_path,
        "vendor_order_tracking_scaffold",
        "Vendor tracking",
        request_id="req1",
    )
    assert len(arts) >= 2
    for a in arts:
        assert (tmp_path / a.sandbox_path).exists()


def test_build_folder_scaffold(tmp_path: Path) -> None:
    art = build_folder_scaffold(
        tmp_path,
        ["briefs", "notes", "docs"],
        request_id="req1",
        include_readme=True,
    )
    assert art.artifact_type == "folder_scaffold"
    assert (tmp_path / "briefs").exists()
    assert (tmp_path / "notes").exists()
    assert (tmp_path / "README_scaffold.txt").exists()


def test_build_creative_folder_scaffold(tmp_path: Path) -> None:
    art = build_creative_folder_scaffold(
        tmp_path,
        "creative_project_folder_scaffold",
        request_id="req1",
        naming_hints=["v1", "final"],
    )
    assert "source" in str(tmp_path) or (tmp_path / "source").exists() or (tmp_path / "exports").exists()
    assert art.artifact_type == "creative_folder_scaffold"


def test_materialize_from_draft(tmp_path: Path) -> None:
    context_bundle = {
        "draft_context": {"drafts": []},
        "project_context": {"projects": [], "parsed_artifacts": [], "domains": []},
        "style_context": {},
        "workflow_context": {},
        "suggestion_context": {"suggestions": []},
        "retrieved_docs": [],
    }
    manifest, ws_path = materialize_from_draft(
        context_bundle,
        tmp_path,
        draft_type="project_brief",
        session_id="s1",
        allow_markdown=True,
        allow_csv=True,
        allow_folder_scaffolds=True,
        save_manifests=True,
    )
    assert manifest.request_id
    assert len(manifest.artifacts) >= 1
    assert ws_path.exists()
    manifest_file = ws_path / "MANIFEST.json"
    assert manifest_file.exists()
    assert "project_brief" in manifest.generated_from or "Project brief" in str(manifest.artifacts)


def test_materialize_from_suggestion_no_suggestion(tmp_path: Path) -> None:
    context_bundle = {
        "suggestion_context": {"suggestions": []},
        "project_context": {},
    }
    manifest, ws_path = materialize_from_suggestion(
        context_bundle,
        tmp_path,
        suggestion_id="sug_nonexistent",
        save_manifests=True,
    )
    assert len(manifest.output_paths) == 0
    assert manifest.request_id


def test_render_preview(tmp_path: Path) -> None:
    m = MaterializationManifest(
        manifest_id="mf1",
        request_id="req1",
        output_paths=["brief.md"],
        generated_from="project_brief",
        artifacts=[
            MaterializedArtifact(artifact_id="a1", title="Brief", artifact_type="markdown_brief", sandbox_path="brief.md"),
        ],
        created_utc=utc_now_iso(),
    )
    (tmp_path / "brief.md").write_text("# Brief\n\nContent.")
    preview = render_preview(m, tmp_path, max_file_preview_chars=100)
    assert "Materialization preview" in preview or "preview" in preview.lower()
    assert "req1" in preview or "Brief" in preview


def test_render_artifact_tree(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "b.txt").write_text("x")
    tree = render_artifact_tree(tmp_path, indent="", max_depth=2)
    assert "a" in tree or "b.txt" in tree


def test_persist_materialization_nodes(tmp_path: Path) -> None:
    import sqlite3
    from workflow_dataset.personal.graph_store import init_store
    db = tmp_path / "graph.sqlite"
    init_store(db)
    m = MaterializationManifest(
        manifest_id="mf1",
        request_id="req1",
        output_paths=["out.md"],
        generated_from="project_brief",
        draft_refs=[],
        artifacts=[
            MaterializedArtifact(artifact_id="art_1", title="Out", artifact_type="markdown_brief", sandbox_path="out.md"),
        ],
        created_utc=utc_now_iso(),
    )
    n = persist_materialization_nodes(db, m, tmp_path, {})
    assert n >= 1


def test_assist_materialize_cli(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    config = tmp_path / "settings.yaml"
    config.write_text("""
project: {name: x, version: v1, output_excel: o, output_csv_dir: c, output_parquet_dir: p, qa_report_path: q}
runtime: {timezone: UTC, long_run_profile: true, max_workers: 2, fail_on_missing_provenance: false, infer_low_confidence_threshold: 0.45, infer_high_confidence_threshold: 0.8}
paths: {raw_official: r, raw_private: r, interim: i, processed: p, prompts: pr, context: c, sqlite_path: s, event_log_dir: data/local/event_log, graph_store_path: data/local/work_graph.sqlite}
setup:
  setup_dir: """ + str(tmp_path) + """
  parsed_artifacts_dir: """ + str(tmp_path) + """
  style_signals_dir: """ + str(tmp_path) + """
  setup_reports_dir: """ + str(tmp_path) + """
  suggestions_dir: """ + str(tmp_path) + """
  draft_structures_dir: """ + str(tmp_path) + """
materialization:
  materialization_enabled: true
  materialization_workspace_root: """ + str(tmp_path / "ws") + """
  materialization_save_manifests: true
""")
    runner = CliRunner()
    result = runner.invoke(app, [
        "assist", "materialize", "project_brief",
        "--config", str(config),
        "--workspace", str(tmp_path / "ws"),
    ])
    assert result.exit_code == 0
    assert "Materialized" in result.output or "output" in result.output.lower()
    assert (tmp_path / "ws").exists() or (tmp_path / "ws" / "materialized").exists()


def test_assist_list_workspaces_cli(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    (tmp_path / "ws").mkdir(parents=True)
    config = tmp_path / "s2.yaml"
    config.write_text("""
project: {name: x, version: v1, output_excel: o, output_csv_dir: c, output_parquet_dir: p, qa_report_path: q}
runtime: {timezone: UTC, long_run_profile: true, max_workers: 2, fail_on_missing_provenance: false, infer_low_confidence_threshold: 0.45, infer_high_confidence_threshold: 0.8}
paths: {raw_official: r, raw_private: r, interim: i, processed: p, prompts: pr, context: c, sqlite_path: s, event_log_dir: data/local/event_log, graph_store_path: data/local/work_graph.sqlite}
setup: {setup_dir: """ + str(tmp_path) + """, parsed_artifacts_dir: """ + str(tmp_path) + """, style_signals_dir: """ + str(tmp_path) + """, setup_reports_dir: """ + str(tmp_path) + """, suggestions_dir: """ + str(tmp_path) + """, draft_structures_dir: """ + str(tmp_path) + """}
materialization: {materialization_workspace_root: """ + str(tmp_path / "ws") + """}
""")
    runner = CliRunner()
    result = runner.invoke(app, ["assist", "list-workspaces", "--config", str(config)])
    assert result.exit_code == 0
