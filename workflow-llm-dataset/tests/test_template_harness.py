"""
M22E-F5: Template testing harness tests. Validate artifact inventory, order, manifest shape.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.templates.harness import (
    HarnessResult,
    expected_artifact_list_for_template,
    required_manifest_keys_for_template,
    run_template_harness,
    validate_workspace_against_template,
)


def _repo_root() -> Path:
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root())
    except Exception:
        return Path.cwd()


def _fixtures_dir() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "template_harness"


def test_expected_artifact_list_for_template() -> None:
    """Expected list is source_snapshot.md + template artifact filenames in order."""
    t = {
        "id": "x",
        "workflow_id": "ops_reporting_workspace",
        "artifacts": ["status_brief", "action_register", "decision_requests"],
    }
    expected = expected_artifact_list_for_template(t)
    assert expected[0] == "source_snapshot.md"
    assert expected[1:] == ["status_brief.md", "action_register.md", "decision_requests.md"]


def test_required_manifest_keys_for_template() -> None:
    """Required keys include workflow, artifact_list, template_id."""
    t = {"id": "tid", "workflow_id": "ops_reporting_workspace", "artifacts": []}
    keys = required_manifest_keys_for_template(t)
    assert "workflow" in keys
    assert "artifact_list" in keys
    assert "template_id" in keys


def test_validate_workspace_against_template_success() -> None:
    """Golden fixture ops_reporting_core passes validation."""
    fixture_ws = _fixtures_dir() / "ops_reporting_core"
    if not fixture_ws.exists():
        pytest.skip("fixtures/template_harness/ops_reporting_core not found")
    root = _repo_root()
    result = validate_workspace_against_template(fixture_ws, "ops_reporting_core", repo_root=root)
    assert result.passed, result.to_message()
    assert result.template_id == "ops_reporting_core"
    assert "source_snapshot.md" in result.expected_artifacts
    assert "status_brief.md" in result.expected_artifacts
    assert result.expected_artifacts == result.actual_artifacts


def test_validate_workspace_against_template_missing_artifact() -> None:
    """Missing an expected artifact yields readable error."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp)
        (ws / "workspace_manifest.json").write_text(
            '{"workflow":"ops_reporting_workspace","template_id":"ops_reporting_core","artifact_list":["source_snapshot.md","status_brief.md"]}'
        )
        (ws / "source_snapshot.md").write_text("# Source\n")
        (ws / "status_brief.md").write_text("Brief\n")
        root = _repo_root()
        result = validate_workspace_against_template(ws, "ops_reporting_core", repo_root=root)
    assert result.passed is False
    assert any("Missing" in e for e in result.errors)
    assert "action_register.md" in str(result.errors) or "decision_requests" in str(result.errors)


def test_validate_workspace_against_template_wrong_order() -> None:
    """Wrong artifact order yields order mismatch error."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp)
        (ws / "workspace_manifest.json").write_text(
            '{"workflow":"ops_reporting_workspace","template_id":"ops_reporting_core",'
            '"artifact_list":["source_snapshot.md","decision_requests.md","action_register.md","status_brief.md"]}'
        )
        for f in ["source_snapshot.md", "decision_requests.md", "action_register.md", "status_brief.md"]:
            (ws / f).write_text("x\n")
        root = _repo_root()
        result = validate_workspace_against_template(ws, "ops_reporting_core", repo_root=root)
    assert result.passed is False
    assert any("order" in e.lower() for e in result.errors)


def test_validate_workspace_against_template_manifest_mismatch() -> None:
    """Manifest missing template_id yields manifest_errors."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp)
        (ws / "workspace_manifest.json").write_text(
            '{"workflow":"ops_reporting_workspace","artifact_list":["source_snapshot.md","status_brief.md","action_register.md","decision_requests.md"]}'
        )
        for f in ["source_snapshot.md", "status_brief.md", "action_register.md", "decision_requests.md"]:
            (ws / f).write_text("x\n")
        root = _repo_root()
        result = validate_workspace_against_template(ws, "ops_reporting_core", repo_root=root)
    assert result.passed is False
    assert any("template_id" in e for e in result.manifest_errors)


def test_run_template_harness_without_workspace() -> None:
    """run_template_harness without workspace returns expected list and passed."""
    root = _repo_root()
    if not (root / "data/local/templates/ops_reporting_core.yaml").exists():
        pytest.skip("ops_reporting_core template not found")
    result = run_template_harness("ops_reporting_core", workspace_path=None, repo_root=root)
    assert result.passed is True
    assert result.expected_artifacts
    assert result.template_id == "ops_reporting_core"


def test_run_template_harness_with_fixture_workspace() -> None:
    """run_template_harness with fixture workspace validates and passes."""
    fixture_ws = _fixtures_dir() / "ops_reporting_core"
    if not fixture_ws.exists():
        pytest.skip("fixtures/template_harness/ops_reporting_core not found")
    root = _repo_root()
    result = run_template_harness("ops_reporting_core", workspace_path=fixture_ws, repo_root=root)
    assert result.passed, result.to_message()


def test_harness_result_to_message_readable() -> None:
    """HarnessResult.to_message() includes expected/actual and errors."""
    r = HarnessResult(
        passed=False,
        template_id="x",
        expected_artifacts=["a.md", "b.md"],
        actual_artifacts=["a.md"],
        errors=["Missing artifacts: ['b.md']"],
    )
    msg = r.to_message()
    assert "Template: x" in msg
    assert "a.md" in msg
    assert "Missing" in msg
    assert "b.md" in msg
