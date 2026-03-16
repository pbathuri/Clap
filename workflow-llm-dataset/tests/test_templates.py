"""
M22E-F2: Tests for template versioning, validation, and validation reports.
"""

from __future__ import annotations

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
    template_validation_report,
    validate_template,
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
