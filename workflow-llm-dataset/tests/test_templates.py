"""
M22E-F2: Tests for template versioning, validation, and validation reports.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.templates.registry import (
    load_template,
    list_templates,
)
from workflow_dataset.templates.validation import (
    STATUS_DEPRECATED,
    STATUS_INVALID,
    STATUS_VALID,
    STATUS_VALID_WITH_WARNING,
    get_template_status,
    resolve_template_params,
    template_validation_report,
    validate_template,
)
from workflow_dataset.templates.export_import import (
    export_template,
    import_template,
    _export_dict,
)


def _repo_root() -> Path:
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root())
    except Exception:
        return Path.cwd()


def test_validate_template_valid_dict() -> None:
    """Valid template dict yields status valid."""
    t = {
        "id": "test_valid",
        "workflow_id": "ops_reporting_workspace",
        "artifacts": ["status_brief", "action_register", "decision_requests"],
    }
    r = validate_template(t)
    assert r["valid"] is True
    assert r["status"] == STATUS_VALID
    assert r["errors"] == []
    assert r["template_id"] == "test_valid"
    assert r["checks"].get("workflow_exists", {}).get("ok") is True
    assert r["checks"].get("artifacts_valid", {}).get("ok") is True


def test_validate_template_invalid_workflow() -> None:
    """Unknown workflow_id yields invalid status and error."""
    t = {
        "id": "test_bad_workflow",
        "workflow_id": "nonexistent_workflow",
        "artifacts": ["weekly_status"],
    }
    r = validate_template(t)
    assert r["valid"] is False
    assert r["status"] == STATUS_INVALID
    assert len(r["errors"]) >= 1
    assert "workflow" in r["errors"][0].lower() or "allowed" in r["errors"][0].lower()


def test_validate_template_invalid_artifact() -> None:
    """Artifact not allowed for workflow yields invalid."""
    t = {
        "id": "test_bad_artifact",
        "workflow_id": "weekly_status",
        "artifacts": ["weekly_status", "meeting_brief"],
    }
    r = validate_template(t)
    assert r["valid"] is False
    assert r["status"] == STATUS_INVALID
    assert any("artifact" in e.lower() or "allowed" in e.lower() for e in r["errors"])


def test_validate_template_deprecated() -> None:
    """Template with deprecated=True yields status deprecated (if otherwise valid)."""
    t = {
        "id": "test_deprecated",
        "workflow_id": "weekly_status",
        "artifacts": ["weekly_status"],
        "deprecated": True,
    }
    r = validate_template(t)
    assert r["valid"] is True
    assert r["status"] == STATUS_DEPRECATED
    assert any("deprecated" in w.lower() for w in r["warnings"])
    assert len(r["migration_hints"]) >= 1


def test_get_template_status() -> None:
    """get_template_status returns one of valid | valid_with_warning | deprecated | invalid."""
    assert get_template_status({"id": "x", "workflow_id": "weekly_status", "artifacts": ["weekly_status"]}) == STATUS_VALID
    assert get_template_status({"id": "x", "workflow_id": "unknown", "artifacts": []}) == STATUS_INVALID
    assert get_template_status({
        "id": "x", "workflow_id": "weekly_status", "artifacts": ["weekly_status"], "deprecated": True
    }) == STATUS_DEPRECATED


def test_template_validation_report_string() -> None:
    """template_validation_report returns a string containing status and report header."""
    t = {"id": "rpt", "workflow_id": "ops_reporting_workspace", "artifacts": ["status_brief"]}
    report = template_validation_report(t)
    assert isinstance(report, str)
    assert "Template validation report" in report or "validation report" in report.lower()
    assert "Status:" in report
    assert "rpt" in report or "Template id" in report
    assert "Checks:" in report


def test_template_validation_report_not_found() -> None:
    """Report for missing template id includes error and invalid status."""
    report = template_validation_report("_nonexistent_template_id_99_")
    assert "not found" in report.lower() or "invalid" in report.lower()
    assert "Status:" in report


@pytest.mark.skipif(not (_repo_root() / "data/local/templates").exists(), reason="data/local/templates not present")
def test_validate_real_template_if_present() -> None:
    """If ops_reporting_core exists, validate it and expect valid or valid_with_warning."""
    root = _repo_root()
    if not (root / "data/local/templates/ops_reporting_core.yaml").exists():
        pytest.skip("ops_reporting_core.yaml not found")
    r = validate_template("ops_reporting_core", repo_root=root)
    assert r["valid"] is True
    assert r["status"] in (STATUS_VALID, STATUS_VALID_WITH_WARNING)
    assert r["template_id"] == "ops_reporting_core"


def test_load_template_sets_versioning_defaults() -> None:
    """Load template without version/deprecated in file still has keys (backward compat)."""
    root = _repo_root()
    templates_dir = root / "data/local/templates"
    if not templates_dir.exists():
        pytest.skip("data/local/templates not found")
    for tid in ["ops_reporting_core", "weekly_plus_stakeholder"]:
        try:
            t = load_template(tid, repo_root=root)
            assert "deprecated" in t
            assert "version" in t
            assert "migration_hints" in t
        except FileNotFoundError:
            pass


def _has_yaml() -> bool:
    try:
        import yaml  # noqa: F401
        return True
    except ImportError:
        return False


@pytest.mark.skipif(not _has_yaml(), reason="pyyaml required for CLI app import")
def test_cli_templates_validate_help() -> None:
    """CLI: workflow-dataset templates validate --help."""
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    result = CliRunner().invoke(app, ["templates", "validate", "--help"])
    assert result.exit_code == 0
    assert "--id" in result.output or "-i" in result.output


@pytest.mark.skipif(not _has_yaml(), reason="pyyaml required for CLI app import")
def test_cli_templates_report_help() -> None:
    """CLI: workflow-dataset templates report --help."""
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    result = CliRunner().invoke(app, ["templates", "report", "--help"])
    assert result.exit_code == 0
    assert "--id" in result.output or "-i" in result.output


@pytest.mark.skipif(not _has_yaml(), reason="pyyaml required for CLI app import")
def test_cli_templates_list_show_status_help() -> None:
    """CLI: workflow-dataset templates list accepts --show-status."""
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    result = CliRunner().invoke(app, ["templates", "list", "--help"])
    assert result.exit_code == 0
    assert "--show-status" in result.output


# ----- M22E-F3: Export / Import / Parameters -----


def test_export_dict_includes_parameters() -> None:
    """_export_dict includes parameters key when present."""
    t = {"id": "x", "workflow_id": "weekly_status", "artifacts": ["weekly_status"], "parameters": [{"name": "owner", "type": "string"}]}
    out = _export_dict(t)
    assert out["parameters"] == [{"name": "owner", "type": "string"}]
    assert out["id"] == "x"
    assert out["workflow_id"] == "weekly_status"


def test_export_import_roundtrip(tmp_path: Path) -> None:
    """Export a template to file then import it; validate after import."""
    root = _repo_root()
    if not (root / "data/local/templates/ops_reporting_core.yaml").exists():
        pytest.skip("ops_reporting_core.yaml not found")
    out_file = tmp_path / "ops_reporting_core.tmpl.json"
    export_template("ops_reporting_core", out_file, repo_root=root, format="json")
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert data["id"] == "ops_reporting_core"
    assert data["workflow_id"] == "ops_reporting_workspace"
    assert "status_brief" in data["artifacts"]
    # Import to a new id to avoid overwriting
    import_dir = tmp_path / "templates"
    import_dir.mkdir()
    dest = import_dir / "imported_core.yaml"
    # Write to dest so import has a clean dir (we'll import from out_file with target dir = tmp_path/templates)
    # Actually import_template writes to repo_root/data/local/templates. So we need to use tmp_path as repo root for import
    summary = import_template(out_file, repo_root=tmp_path, template_id="imported_core", overwrite=True)
    assert summary["id"] == "imported_core"
    assert summary["validated"] is True
    loaded = load_template("imported_core", repo_root=tmp_path)
    assert loaded["workflow_id"] == "ops_reporting_workspace"
    assert loaded["artifacts"] == data["artifacts"]


def test_import_invalid_template_fails(tmp_path: Path) -> None:
    """Import of invalid template (bad workflow) raises ValueError."""
    invalid = tmp_path / "bad.tmpl.json"
    invalid.write_text(json.dumps({"id": "bad", "workflow_id": "nonexistent_workflow", "artifacts": []}))
    with pytest.raises(ValueError, match="validation failed|workflow"):
        import_template(invalid, repo_root=tmp_path)


def test_import_existing_without_overwrite_raises(tmp_path: Path) -> None:
    """Import when template id already exists and overwrite=False raises FileExistsError."""
    (tmp_path / "data" / "local" / "templates").mkdir(parents=True)
    existing = tmp_path / "data" / "local" / "templates" / "dup.yaml"
    existing.write_text("id: dup\nworkflow_id: weekly_status\nartifacts: [weekly_status]\n")
    new_file = tmp_path / "dup2.tmpl.json"
    new_file.write_text(json.dumps({"id": "dup", "workflow_id": "weekly_status", "artifacts": ["weekly_status"]}))
    with pytest.raises(FileExistsError, match="already exists|overwrite"):
        import_template(new_file, repo_root=tmp_path, template_id="dup", overwrite=False)
    # With overwrite=True should succeed
    summary = import_template(new_file, repo_root=tmp_path, template_id="dup", overwrite=True)
    assert summary["id"] == "dup"


def test_resolve_template_params_ok() -> None:
    """resolve_template_params parses k=v and coerces types."""
    t = {
        "id": "x",
        "workflow_id": "weekly_status",
        "artifacts": ["weekly_status"],
        "parameters": [
            {"name": "owner", "type": "string"},
            {"name": "count", "type": "integer"},
            {"name": "flag", "type": "boolean"},
            {"name": "choice", "type": "choice", "choices": ["a", "b"]},
        ],
    }
    r = resolve_template_params(t, ["owner=Alex", "count=42", "flag=true", "choice=b"])
    assert r["owner"] == "Alex"
    assert r["count"] == 42
    assert r["flag"] is True
    assert r["choice"] == "b"


def test_resolve_template_params_unknown_param_raises() -> None:
    """Unknown --param key raises ValueError."""
    t = {"id": "x", "workflow_id": "weekly_status", "artifacts": ["weekly_status"], "parameters": [{"name": "owner", "type": "string"}]}
    with pytest.raises(ValueError, match="Unknown template parameter"):
        resolve_template_params(t, ["other=value"])


def test_resolve_template_params_no_params_raises() -> None:
    """Passing --param when template has no parameters raises ValueError."""
    t = {"id": "x", "workflow_id": "weekly_status", "artifacts": ["weekly_status"]}
    with pytest.raises(ValueError, match="no parameters"):
        resolve_template_params(t, ["owner=Alex"])


def test_resolve_template_params_defaults_filled() -> None:
    """Optional parameters with default are filled when not provided."""
    t = {
        "id": "x",
        "workflow_id": "weekly_status",
        "artifacts": ["weekly_status"],
        "parameters": [
            {"name": "owner", "type": "string", "required": True},
            {"name": "label", "type": "string", "required": False, "default": "default_label"},
        ],
    }
    r = resolve_template_params(t, ["owner=Alex"])
    assert r["owner"] == "Alex"
    assert r["label"] == "default_label"


def test_validate_template_with_parameters_valid() -> None:
    """Template with valid parameters schema passes validation."""
    t = {
        "id": "p",
        "workflow_id": "ops_reporting_workspace",
        "artifacts": ["status_brief"],
        "parameters": [{"name": "owner", "type": "string", "required": False}],
    }
    r = validate_template(t)
    assert r["valid"] is True
    assert r["checks"].get("parameters_valid", {}).get("ok") is True


def test_validate_template_parameters_invalid_type() -> None:
    """Parameter type not in allowed set yields invalid."""
    t = {
        "id": "p",
        "workflow_id": "weekly_status",
        "artifacts": ["weekly_status"],
        "parameters": [{"name": "x", "type": "custom_type"}],
    }
    r = validate_template(t)
    assert r["valid"] is False
    assert "parameters_valid" in r["checks"]
    assert r["checks"]["parameters_valid"].get("ok") is False


# ----- M22E-F6: Template usage and reporting -----


def test_template_usage_summary_empty(tmp_path: Path) -> None:
    """template_usage_summary returns shape with empty counts when no workspaces."""
    from workflow_dataset.templates.usage import template_usage_summary
    data = template_usage_summary(workspaces_root=tmp_path, repo_root=tmp_path, limit=50)
    assert "counts_by_template" in data
    assert "recent_runs" in data
    assert data["total_runs"] == 0
    assert data["total_template_runs"] == 0


def test_template_usage_summary_with_template_runs(tmp_path: Path) -> None:
    """template_usage_summary counts template-driven runs when workspaces have template_id in manifest."""
    from workflow_dataset.templates.usage import template_usage_summary
    ws_root = tmp_path / "data" / "local" / "workspaces"
    run_dir = ws_root / "ops_reporting_workspace" / "2025-03-16_abc123"
    run_dir.mkdir(parents=True)
    (run_dir / "workspace_manifest.json").write_text(
        json.dumps({
            "workflow": "ops_reporting_workspace",
            "timestamp": "2025-03-16T12:00:00Z",
            "template_id": "ops_reporting_core",
            "template_version": "1.0",
        }, indent=2),
        encoding="utf-8",
    )
    data = template_usage_summary(workspaces_root=str(ws_root), repo_root=tmp_path, limit=50)
    assert data["total_runs"] >= 1
    assert data["total_template_runs"] >= 1
    assert data["counts_by_template"].get("ops_reporting_core", 0) >= 1
    assert len(data["recent_runs"]) >= 1
    assert data["recent_runs"][0].get("template_id") == "ops_reporting_core"
