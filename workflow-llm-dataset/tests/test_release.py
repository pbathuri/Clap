"""
Tests for M18 release: config resolution, report generation, CLI entrypoints.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from workflow_dataset.cli import app
from workflow_dataset.release.report import write_release_readiness_report

runner = CliRunner()


def test_release_config_resolution() -> None:
    path = Path("configs/release_narrow.yaml")
    if not path.exists():
        pytest.skip("configs/release_narrow.yaml not found")
    with open(path) as f:
        data = yaml.safe_load(f)
    rel = data.get("release", {})
    assert rel.get("scope") == "ops"
    assert "trial_ids" in rel
    assert "default_llm_config" in rel


def test_release_verify_help() -> None:
    result = runner.invoke(app, ["release", "verify", "--help"])
    assert result.exit_code == 0
    assert "verify" in result.output.lower()


def test_release_verify_runs() -> None:
    result = runner.invoke(app, ["release", "verify", "--config", "configs/settings.yaml"])
    assert result.exit_code == 0
    assert "Release scope" in result.output or "scope" in result.output.lower()
    assert "Graph" in result.output or "LLM" in result.output or "Trials" in result.output


def test_release_report_generates(tmp_path: Path) -> None:
    report_path = write_release_readiness_report(
        config_path="configs/settings.yaml",
        release_config_path="configs/release_narrow.yaml",
        output_dir=tmp_path,
    )
    assert report_path.exists()
    text = report_path.read_text()
    assert "Release readiness" in text or "release" in text.lower()
    assert "ops" in text.lower() or "Operations" in text
    assert "Safety" in text or "safety" in text.lower()


def test_release_report_cli(tmp_path: Path) -> None:
    result = runner.invoke(app, [
        "release", "report",
        "--config", "configs/settings.yaml",
        "--release-config", "configs/release_narrow.yaml",
        "--output-dir", str(tmp_path),
    ])
    assert result.exit_code == 0
    assert (tmp_path / "release_readiness_report.md").exists()


def test_release_run_help() -> None:
    result = runner.invoke(app, ["release", "run", "--help"])
    assert result.exit_code == 0


def test_release_demo_help() -> None:
    result = runner.invoke(app, ["release", "demo", "--help"])
    assert result.exit_code == 0
    assert "--context-file" in result.output
    assert "--context-text" in result.output
    assert "--input-pack" in result.output
    assert "--save-artifact" in result.output
    assert "--workflow" in result.output or "-w" in result.output
    assert "retrieval" in result.output.lower()


def test_stakeholder_update_bundle_artifact_sandbox_format(tmp_path: Path) -> None:
    """Stakeholder update bundle artifact + manifest have expected shape."""
    import json
    (tmp_path / "stakeholder_update.md").write_text(
        "**Headline:** Delivery on track.\n**Key progress:** Milestone shipped.\n**Asks:** Vendor unblock.",
        encoding="utf-8",
    )
    (tmp_path / "decision_requests.md").write_text(
        "| Decision | Why | Consequence if delayed |\n|----------|-----|------------------------|\n| Approve scope | Unblock next phase | Slip to next sprint |",
        encoding="utf-8",
    )
    manifest = {
        "artifact_type": "stakeholder_update_bundle",
        "workflow": "stakeholder_update_bundle",
        "grounding": "task_context_only",
        "has_stakeholder_update": True,
        "has_decision_requests": True,
        "timestamp": "2025-01-15T12:00:00Z",
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    loaded = json.loads((tmp_path / "manifest.json").read_text())
    assert loaded["artifact_type"] == "stakeholder_update_bundle"
    assert loaded.get("workflow") == "stakeholder_update_bundle"
    assert (tmp_path / "stakeholder_update.md").exists()
    assert (tmp_path / "decision_requests.md").exists()


def test_status_action_bundle_artifact_sandbox_format(tmp_path: Path) -> None:
    """Status action bundle artifact + manifest have expected shape."""
    import json
    (tmp_path / "status_brief.md").write_text(
        "**Headline:** Project on track.\n**Wins:** Delivered X.\n**Risks:** Y.",
        encoding="utf-8",
    )
    (tmp_path / "action_register.md").write_text(
        "| Action | Why |\n|--------|-----|\n| Follow up with vendor | Unblock delivery |",
        encoding="utf-8",
    )
    manifest = {
        "artifact_type": "status_action_bundle",
        "workflow": "status_action_bundle",
        "grounding": "task_context_only",
        "has_status_brief": True,
        "has_action_register": True,
        "timestamp": "2025-01-15T12:00:00Z",
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    loaded = json.loads((tmp_path / "manifest.json").read_text())
    assert loaded["artifact_type"] == "status_action_bundle"
    assert loaded.get("workflow") == "status_action_bundle"
    assert (tmp_path / "status_brief.md").exists()
    assert (tmp_path / "action_register.md").exists()


def test_meeting_brief_bundle_artifact_sandbox_format(tmp_path: Path) -> None:
    """Meeting brief bundle artifact + manifest have expected shape."""
    import json
    (tmp_path / "meeting_brief.md").write_text(
        "**Meeting:** Q1 review.\n**Attendees:** Eng, PM.\n**Decisions:** Scope approved.",
        encoding="utf-8",
    )
    (tmp_path / "action_items.md").write_text(
        "| Action | Owner | Due |\n|--------|-------|-----|\n| Send recap | PM | EOW |",
        encoding="utf-8",
    )
    manifest = {
        "artifact_type": "meeting_brief_bundle",
        "workflow": "meeting_brief_bundle",
        "grounding": "task_context_only",
        "has_meeting_brief": True,
        "has_action_items": True,
        "timestamp": "2025-01-15T12:00:00Z",
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    loaded = json.loads((tmp_path / "manifest.json").read_text())
    assert loaded["artifact_type"] == "meeting_brief_bundle"
    assert loaded.get("workflow") == "meeting_brief_bundle"
    assert (tmp_path / "meeting_brief.md").exists()
    assert (tmp_path / "action_items.md").exists()


def test_ops_reporting_workspace_artifact_sandbox_format(tmp_path: Path) -> None:
    """Ops reporting workspace: workspace_manifest.json + source_snapshot + artifact .md files have expected shape."""
    import json
    (tmp_path / "source_snapshot.md").write_text(
        "# Source snapshot\n\n- **Explicit task context:** yes\n- **Retrieval grounding:** no\n",
        encoding="utf-8",
    )
    (tmp_path / "weekly_status.md").write_text("**Summary:** Ops update.\n**Wins:** X.\n**Next steps:** Y.", encoding="utf-8")
    (tmp_path / "status_brief.md").write_text("**Headline:** On track.", encoding="utf-8")
    (tmp_path / "action_register.md").write_text("| Action | Why |\n|--------|-----|\n| Follow up | Unblock.", encoding="utf-8")
    (tmp_path / "stakeholder_update.md").write_text("**Headline:** Delivery on track.", encoding="utf-8")
    (tmp_path / "decision_requests.md").write_text("| Decision | Why |\n|----------|-----|\n| Approve scope | Unblock.", encoding="utf-8")
    manifest = {
        "workflow": "ops_reporting_workspace",
        "timestamp": "2025-01-15T12:00:00Z",
        "grounding": "task_context_only",
        "retrieval_used": False,
        "explicit_context_used": True,
        "saved_artifact_paths": ["source_snapshot.md", "weekly_status.md", "status_brief.md", "action_register.md", "stakeholder_update.md", "decision_requests.md"],
    }
    (tmp_path / "workspace_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    loaded = json.loads((tmp_path / "workspace_manifest.json").read_text())
    assert loaded["workflow"] == "ops_reporting_workspace"
    assert "saved_artifact_paths" in loaded
    assert "source_snapshot.md" in loaded["saved_artifact_paths"]
    assert (tmp_path / "source_snapshot.md").exists()
    assert (tmp_path / "weekly_status.md").exists()
    assert (tmp_path / "workspace_manifest.json").exists()


def test_save_ops_reporting_workspace_writes_sandbox(tmp_path: Path) -> None:
    """save_ops_reporting_workspace creates workspace dir with artifacts and workspace_manifest.json."""
    import json
    from workflow_dataset.release.workspace_save import save_ops_reporting_workspace

    root = tmp_path / "repo"
    root.mkdir()
    artifacts = {
        "source_snapshot.md": "# Source\n\n- Task context: yes",
        "weekly_status.md": "**Summary:** Done.",
    }
    manifest_dict = {"workflow": "ops_reporting_workspace", "grounding": "task_context_only"}
    out_dir = save_ops_reporting_workspace(artifacts, manifest_dict, repo_root=root)
    assert out_dir.is_dir()
    assert (out_dir / "source_snapshot.md").exists()
    assert (out_dir / "weekly_status.md").exists()
    assert (out_dir / "workspace_manifest.json").exists()
    loaded = json.loads((out_dir / "workspace_manifest.json").read_text())
    assert loaded["workflow"] == "ops_reporting_workspace"
    assert "saved_artifact_paths" in loaded
    assert "source_snapshot.md" in loaded["saved_artifact_paths"]


def test_weekly_status_artifact_sandbox_format(tmp_path: Path) -> None:
    """Weekly status artifact + manifest written to sandbox have expected shape."""
    import json
    md = "**Summary:** Weekly ops update.\n**Wins:** Shipped X.\n**Blockers:** Waiting on Y.\n**Next steps:** (1) Z."
    manifest = {
        "artifact_type": "weekly_status",
        "grounding": "task_context_only",
        "task_context_used": True,
        "retrieval_used": False,
        "retrieval_relevance": None,
        "timestamp": "2025-01-15T12:00:00Z",
    }
    (tmp_path / "weekly_status.md").write_text(md, encoding="utf-8")
    (tmp_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    assert (tmp_path / "weekly_status.md").read_text() == md
    loaded = json.loads((tmp_path / "manifest.json").read_text())
    assert loaded["artifact_type"] == "weekly_status"
    assert loaded["grounding"] == "task_context_only"
    assert "timestamp" in loaded


def test_weekly_status_workspace_dir_acceptable_for_apply(tmp_path: Path) -> None:
    """Weekly status sandbox is a directory; apply-plan accepts it (printed path is valid for apply)."""
    ws = tmp_path / "weekly_status_ws"
    ws.mkdir()
    (ws / "weekly_status.md").write_text("**Summary:** Done.\n**Next steps:** Follow up.", encoding="utf-8")
    target = tmp_path / "target"
    target.mkdir()
    from workflow_dataset.apply.copy_planner import build_apply_plan
    plan, err = build_apply_plan(ws, target, dry_run=True)
    assert plan is not None, err
    assert err == ""
    assert plan.estimated_file_count >= 1
    assert any("weekly_status" in str(o.get("source", "")) for o in plan.operations)


def test_load_task_context(tmp_path: Path) -> None:
    """Task-scoped context loads from file and/or inline text; capped at 2000 chars."""
    from workflow_dataset.cli import _load_task_context, _resolve_path
    ctx_file = tmp_path / "ctx.txt"
    ctx_file.write_text("weekly ops reporting for project delivery", encoding="utf-8")
    out = _load_task_context(str(ctx_file), "", _resolve_path)
    assert "weekly ops reporting" in out
    out2 = _load_task_context("", "inline status and blockers", _resolve_path)
    assert "inline status and blockers" in out2
    out3 = _load_task_context(str(ctx_file), " and inline", _resolve_path)
    assert "weekly ops reporting" in out3 and "inline" in out3


def test_load_input_pack_directory_snapshot(tmp_path: Path) -> None:
    """Input pack with no pack.yaml: directory snapshot of .md/.txt files."""
    from workflow_dataset.release.input_packs import load_input_pack, INPUT_PACKS_ROOT

    root = tmp_path / "repo"
    pack_root = root / INPUT_PACKS_ROOT / "sprint_notes_q1"
    pack_root.mkdir(parents=True)
    (pack_root / "notes.md").write_text("Sprint 1 notes: shipped X.", encoding="utf-8")
    (pack_root / "blockers.txt").write_text("Waiting on vendor.", encoding="utf-8")
    (pack_root / "skip.json").write_text("{}", encoding="utf-8")
    content, sources = load_input_pack("sprint_notes_q1", repo_root=root)
    assert "Sprint 1 notes" in content
    assert "Waiting on vendor" in content
    assert "skip.json" not in content
    assert len(sources) == 2
    assert any(s.get("type") == "input_pack_snapshot" for s in sources)


def test_load_input_pack_with_manifest(tmp_path: Path) -> None:
    """Input pack with <name>.json manifest listing paths (root = repo)."""
    import json
    from workflow_dataset.release.input_packs import load_input_pack, INPUT_PACKS_ROOT

    root = tmp_path / "repo"
    root.mkdir(parents=True)
    (root / INPUT_PACKS_ROOT).mkdir(parents=True)
    (root / "a.md").write_text("Content A", encoding="utf-8")
    (root / "b.md").write_text("Content B", encoding="utf-8")
    (root / INPUT_PACKS_ROOT / "my_pack.json").write_text(
        json.dumps({"paths": ["a.md", "b.md"], "root": "."}), encoding="utf-8"
    )
    content, sources = load_input_pack("my_pack", repo_root=root)
    assert "Content A" in content and "Content B" in content
    assert len(sources) == 2
    assert any(s.get("type") == "input_pack_file" for s in sources)


def test_build_source_snapshot_md() -> None:
    """Standardized source_snapshot includes input sources and artifact list."""
    from workflow_dataset.release.artifact_schema import build_source_snapshot_md

    md = build_source_snapshot_md(
        input_sources_used=[{"type": "context_file", "path_or_name": "notes.txt"}],
        context_file_used=True,
        context_file_path="notes.txt",
        input_pack_used=True,
        input_pack_name="sprint_notes_q1",
        retrieval_used=False,
        retrieval_relevance=None,
        retrieval_relevance_weak_or_mixed=False,
        saved_artifact_paths=["source_snapshot.md", "weekly_status.md", "status_brief.md"],
    )
    assert "# Source snapshot" in md
    assert "notes.txt" in md
    assert "sprint_notes_q1" in md
    assert "weekly_status.md" in md
    assert "Artifacts generated" in md or "artifacts" in md.lower()


def test_ops_reporting_workspace_manifest_includes_input_sources(tmp_path: Path) -> None:
    """Workspace manifest has input_sources_used and retrieval_relevance_weak_or_mixed when provided."""
    import json
    from workflow_dataset.release.workspace_save import save_ops_reporting_workspace

    root = tmp_path / "repo"
    artifacts = {"source_snapshot.md": "# Source\n\nTest.", "weekly_status.md": "**Summary:** Done."}
    manifest = {
        "workflow": "ops_reporting_workspace",
        "input_sources_used": [{"type": "context_file", "path_or_name": "notes.txt"}],
        "retrieval_relevance_weak_or_mixed": True,
        "artifact_list": ["source_snapshot.md", "weekly_status.md"],
        "schema_validation": {"weekly_status.md": {"valid": True, "missing_required": []}},
    }
    out_dir = save_ops_reporting_workspace(artifacts, manifest, repo_root=root)
    loaded = json.loads((out_dir / "workspace_manifest.json").read_text())
    assert loaded.get("input_sources_used") == [{"type": "context_file", "path_or_name": "notes.txt"}]
    assert loaded.get("retrieval_relevance_weak_or_mixed") is True
    assert loaded.get("artifact_list") == ["source_snapshot.md", "weekly_status.md"]
    assert "weekly_status.md" in loaded.get("schema_validation", {})


def test_artifact_schema_validation() -> None:
    """validate_artifact_schema and validate_workspace_artifacts return expected structure."""
    from workflow_dataset.release.artifact_schema import (
        validate_artifact_schema,
        validate_workspace_artifacts,
    )

    r = validate_artifact_schema("## Summary\nDone.", "weekly_status.md")
    assert r["valid"] is True
    assert "Summary" in r["found_sections"]

    r2 = validate_artifact_schema("No sections here.", "weekly_status.md")
    assert r2["valid"] is False
    assert "Summary" in r2["missing_required"]

    artifacts = {"weekly_status.md": "## Summary\nDone.", "status_brief.md": "## Headline summary\nOk."}
    out = validate_workspace_artifacts(artifacts)
    assert "weekly_status.md" in out
    assert "status_brief.md" in out
    assert out["weekly_status.md"]["valid"] is True


def test_infer_rerun_args() -> None:
    """infer_rerun_args extracts context_file, input_pack, retrieval, workflow from manifest."""
    from workflow_dataset.release.workspace_rerun_diff import infer_rerun_args

    manifest = {
        "workflow": "ops_reporting_workspace",
        "input_sources_used": [
            {"type": "context_file", "path_or_name": "notes.txt"},
            {"type": "input_pack_snapshot", "path_or_name": "path/to/file.md", "pack": "sprint_q1"},
        ],
        "retrieval_used": True,
    }
    args = infer_rerun_args(manifest)
    assert args["context_file"] == "notes.txt"
    assert args["input_pack"] == "sprint_q1"
    assert args["retrieval"] is True
    assert args["workflow"] == "ops_reporting_workspace"


def test_diff_workspaces(tmp_path: Path) -> None:
    """diff_workspaces returns inventory diff, manifest metadata diff, and artifact deltas."""
    import json
    from workflow_dataset.release.workspace_rerun_diff import diff_workspaces

    a_dir = tmp_path / "a"
    b_dir = tmp_path / "b"
    a_dir.mkdir()
    b_dir.mkdir()
    for d, name in [(a_dir, "a"), (b_dir, "b")]:
        (d / "weekly_status.md").write_text(f"**Summary:** Run {name}.", encoding="utf-8")
        (d / "workspace_manifest.json").write_text(
            json.dumps({"workflow": "ops_reporting_workspace", "timestamp": f"2025-01-01T0{name == 'a' and '1' or '2'}:00:00Z", "grounding": "task_context_only"}),
            encoding="utf-8",
        )
    (a_dir / "only_in_a.md").write_text("Only A", encoding="utf-8")
    result = diff_workspaces(a_dir, b_dir, include_artifact_diffs=True)
    assert result["path_a"] == str(a_dir.resolve())
    assert result["path_b"] == str(b_dir.resolve())
    inv = result["inventory_diff"]
    assert "only_in_a.md" in inv["only_in_a"]
    assert "weekly_status.md" in inv["common"]
    assert "artifact_deltas" in result
    assert "weekly_status.md" in result["artifact_deltas"]
    assert result["artifact_deltas"]["weekly_status.md"]["diff_lines"] > 0


def test_workspace_timeline(tmp_path: Path) -> None:
    """workspace_timeline returns list of runs with timestamp, run_id, grounding, artifact_count."""
    from workflow_dataset.release.reporting_workspaces import get_workspace_inventory
    from workflow_dataset.release.workspace_rerun_diff import workspace_timeline
    from workflow_dataset.release.workspace_save import save_ops_reporting_workspace

    root = tmp_path / "repo"
    root.mkdir()
    artifacts = {"source_snapshot.md": "# Snapshot", "weekly_status.md": "**Summary:** Ok."}
    manifest = {"workflow": "ops_reporting_workspace", "grounding": "task_context_only"}
    save_ops_reporting_workspace(artifacts, manifest, repo_root=root)
    items = workspace_timeline(root / "data/local/workspaces", workflow="ops_reporting_workspace", limit=5)
    assert len(items) >= 1
    assert items[0]["workflow"] == "ops_reporting_workspace"
    assert "run_id" in items[0]
    assert items[0]["artifact_count"] >= 2


def test_get_export_contract() -> None:
    """Export contract exists for ops_reporting_workspace and has required fields."""
    from workflow_dataset.release.workspace_export_contract import get_export_contract, WORKSPACE_EXPORT_SCHEMA_VERSION

    c = get_export_contract("ops_reporting_workspace")
    assert c is not None
    assert c.get("manifest_file") == "workspace_manifest.json"
    assert "workspace_manifest.json" in c.get("required_files", [])
    assert "source_snapshot.md" in c.get("required_files", [])
    assert "weekly_status.md" in c.get("optional_files", [])
    assert get_export_contract("nonexistent") is None


def test_validate_workspace_export_valid(tmp_path: Path) -> None:
    """validate_workspace_export passes for a compliant ops_reporting_workspace."""
    import json
    from workflow_dataset.release.workspace_export_contract import validate_workspace_export

    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "workspace_manifest.json").write_text(
        json.dumps({
            "workflow": "ops_reporting_workspace",
            "timestamp": "2025-01-01T12:00:00Z",
            "saved_artifact_paths": ["workspace_manifest.json", "source_snapshot.md", "weekly_status.md"],
        }),
        encoding="utf-8",
    )
    (ws / "source_snapshot.md").write_text("# Source snapshot\n\nInputs used.", encoding="utf-8")
    (ws / "weekly_status.md").write_text("**Summary:** Ok.", encoding="utf-8")
    result = validate_workspace_export(ws)
    assert result["valid"] is True
    assert result["workflow"] == "ops_reporting_workspace"
    assert result["manifest_compatible"] is True
    assert len(result["errors"]) == 0


def test_validate_workspace_export_missing_required(tmp_path: Path) -> None:
    """validate_workspace_export fails when required file is missing."""
    import json
    from workflow_dataset.release.workspace_export_contract import validate_workspace_export

    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "workspace_manifest.json").write_text(
        json.dumps({
            "workflow": "ops_reporting_workspace",
            "timestamp": "2025-01-01T12:00:00Z",
            "saved_artifact_paths": ["workspace_manifest.json"],
        }),
        encoding="utf-8",
    )
    # missing source_snapshot.md
    result = validate_workspace_export(ws)
    assert result["valid"] is False
    assert "source_snapshot.md" in result["missing_required"]


def test_validate_workspace_export_missing_manifest_key(tmp_path: Path) -> None:
    """validate_workspace_export fails when required manifest key is missing."""
    import json
    from workflow_dataset.release.workspace_export_contract import validate_workspace_export

    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "workspace_manifest.json").write_text(
        json.dumps({"workflow": "ops_reporting_workspace"}),  # missing timestamp, saved_artifact_paths
        encoding="utf-8",
    )
    (ws / "source_snapshot.md").write_text("# Snapshot", encoding="utf-8")
    result = validate_workspace_export(ws)
    assert result["valid"] is False
    assert len(result["missing_manifest_keys"]) >= 1


def test_review_validate_workspace_cli() -> None:
    """review validate-workspace and export-contract CLI exist and run."""
    result = runner.invoke(app, ["review", "validate-workspace", "--help"])
    assert result.exit_code == 0
    assert "validate-workspace" in result.output or "validate_workspace" in result.output
    result2 = runner.invoke(app, ["review", "export-contract", "--help"])
    assert result2.exit_code == 0
    assert "workflow" in result2.output.lower()

