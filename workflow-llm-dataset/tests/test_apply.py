"""Tests for M8 user-approved apply-to-project: validation, plan, diff, execute, rollback, CLI."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.apply.apply_models import ApplyRequest, ApplyPlan, ApplyResult, RollbackRecord
from workflow_dataset.apply.policy_checks import (
    apply_policy_ok,
    require_confirm,
    target_root_allowed,
    create_backups,
)
from workflow_dataset.apply.target_validator import validate_target
from workflow_dataset.apply.copy_planner import build_apply_plan
from workflow_dataset.apply.diff_preview import render_diff_preview
from workflow_dataset.apply.apply_executor import execute_apply
from workflow_dataset.apply.rollback_store import create_rollback_record, save_rollback_record, perform_rollback
from workflow_dataset.apply.apply_manifest_store import save_apply_request, save_apply_plan, save_apply_result, load_apply_result
from workflow_dataset.materialize.manifest_store import save_manifest
from workflow_dataset.materialize.materialize_models import MaterializationManifest
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


@pytest.fixture
def apply_config_enabled():
    return type("C", (), {"apply_enabled": True, "apply_require_confirm": True, "apply_allow_overwrite": False, "apply_create_backups": True})()


@pytest.fixture
def sandbox_workspace(tmp_path: Path) -> Path:
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "file1.md").write_text("# Hello")
    (tmp_path / "b.txt").write_text("text")
    m = MaterializationManifest(
        manifest_id="mf1",
        request_id="req1",
        output_paths=["a/file1.md", "b.txt"],
        generated_from="project_brief",
        created_utc=utc_now_iso(),
        artifacts=[],
    )
    save_manifest(m, tmp_path)
    return tmp_path


def test_target_root_allowed(tmp_path: Path) -> None:
    ok, _ = target_root_allowed(tmp_path, allowed_roots=[str(tmp_path)])
    assert ok is True
    ok2, msg = target_root_allowed(Path("/etc"), deny_roots=["/etc"])
    assert ok2 is False
    assert "denied" in msg.lower() or "etc" in msg


def test_validate_target(tmp_path: Path) -> None:
    ok, msg = validate_target(tmp_path, must_exist=True)
    assert ok is True
    ok2, msg2 = validate_target(tmp_path / "nonexistent", must_exist=False)
    assert ok2 is True
    ok3, _ = validate_target(tmp_path / "nested" / "dir", must_exist=False)
    assert ok3 is True


def test_require_confirm(apply_config_enabled) -> None:
    assert require_confirm(apply_config_enabled) is True


def test_build_apply_plan(sandbox_workspace: Path, tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    plan, err = build_apply_plan(sandbox_workspace, target, dry_run=True)
    assert err == ""
    assert plan is not None
    assert plan.estimated_file_count >= 1
    assert any("file1" in o.get("source", "") or "b.txt" in o.get("source", "") for o in plan.operations)


def test_build_apply_plan_with_conflict(sandbox_workspace: Path, tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    (target / "b.txt").write_text("existing")
    plan, err = build_apply_plan(sandbox_workspace, target, allow_overwrite=False, dry_run=True)
    assert plan is not None
    assert len(plan.conflicts) >= 1 or "b.txt" in plan.skipped_paths or any("b.txt" in str(c) for c in plan.conflicts)


def test_render_diff_preview(tmp_path: Path) -> None:
    plan = ApplyPlan(
        plan_id="plan1",
        source_paths=["a.md"],
        target_paths=[str(tmp_path / "a.md")],
        operations=[{"op": "create", "source": "a.md", "target": str(tmp_path / "a.md")}],
        estimated_file_count=1,
        created_utc=utc_now_iso(),
    )
    preview = render_diff_preview(plan)
    assert "Apply plan preview" in preview or "preview" in preview.lower()
    assert "a.md" in preview


def test_execute_apply_refuses_without_confirm(sandbox_workspace: Path, tmp_path: Path) -> None:
    target = tmp_path / "out"
    target.mkdir()
    plan, _ = build_apply_plan(sandbox_workspace, target, dry_run=True)
    assert plan is not None
    result, msg = execute_apply(plan, sandbox_workspace, target, user_confirmed=False)
    assert result is None
    assert "confirm" in msg.lower()


def test_execute_apply_with_confirm(sandbox_workspace: Path, tmp_path: Path) -> None:
    target = tmp_path / "out"
    target.mkdir()
    plan, _ = build_apply_plan(sandbox_workspace, target, dry_run=True)
    assert plan is not None
    backup_root = tmp_path / "applies"
    result, msg = execute_apply(
        plan,
        sandbox_workspace,
        target,
        user_confirmed=True,
        create_backups=False,
        backup_root=None,
    )
    assert result is not None
    assert len(result.applied_paths) >= 1
    assert (target / "b.txt").exists() or (target / "a" / "file1.md").exists()


def test_rollback_record_save_load(tmp_path: Path) -> None:
    rec = create_rollback_record("apply1", [{"original": "/a", "backup": "/b"}], ["/a"], tmp_path)
    save_rollback_record(rec, tmp_path)
    assert (tmp_path / "rollbacks" / f"{rec.rollback_token}.json").exists()


def test_save_load_apply_result(tmp_path: Path) -> None:
    r = ApplyResult(result_id="res1", apply_id="ap1", applied_paths=["/x"], created_utc=utc_now_iso())
    save_apply_result(r, tmp_path)
    loaded = load_apply_result("res1", tmp_path)
    assert loaded is not None
    assert loaded.result_id == r.result_id


def test_assist_apply_plan_cli(sandbox_workspace: Path, tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    target = tmp_path / "target"
    target.mkdir()
    config = tmp_path / "cfg.yaml"
    config.write_text("""
project: {name: x, version: v1, output_excel: o, output_csv_dir: c, output_parquet_dir: p, qa_report_path: q}
runtime: {timezone: UTC, long_run_profile: true, max_workers: 2, fail_on_missing_provenance: false, infer_low_confidence_threshold: 0.45, infer_high_confidence_threshold: 0.8}
paths: {raw_official: r, raw_private: r, interim: i, processed: p, prompts: pr, context: c, sqlite_path: s, event_log_dir: data/local/event_log, graph_store_path: data/local/work_graph.sqlite}
setup: {setup_dir: """ + str(tmp_path) + """, parsed_artifacts_dir: """ + str(tmp_path) + """, style_signals_dir: """ + str(tmp_path) + """, setup_reports_dir: """ + str(tmp_path) + """, suggestions_dir: """ + str(tmp_path) + """, draft_structures_dir: """ + str(tmp_path) + """}
apply: {apply_enabled: true, apply_require_confirm: true, apply_manifest_root: """ + str(tmp_path / "applies") + """}
""")
    runner = CliRunner()
    result = runner.invoke(app, [
        "assist", "apply-plan",
        str(sandbox_workspace),
        str(target),
        "--config", str(config),
    ])
    assert result.exit_code == 0
    assert "preview" in result.output.lower() or "create" in result.output.lower() or "Would" in result.output


def test_assist_apply_refuses_without_confirm(sandbox_workspace: Path, tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    target = tmp_path / "target"
    target.mkdir()
    config = tmp_path / "cfg2.yaml"
    config.write_text("""
project: {name: x, version: v1, output_excel: o, output_csv_dir: c, output_parquet_dir: p, qa_report_path: q}
runtime: {timezone: UTC, long_run_profile: true, max_workers: 2, fail_on_missing_provenance: false, infer_low_confidence_threshold: 0.45, infer_high_confidence_threshold: 0.8}
paths: {raw_official: r, raw_private: r, interim: i, processed: p, prompts: pr, context: c, sqlite_path: s, event_log_dir: data/local/event_log, graph_store_path: data/local/work_graph.sqlite}
setup: {setup_dir: """ + str(tmp_path) + """, parsed_artifacts_dir: """ + str(tmp_path) + """, style_signals_dir: """ + str(tmp_path) + """, setup_reports_dir: """ + str(tmp_path) + """, suggestions_dir: """ + str(tmp_path) + """, draft_structures_dir: """ + str(tmp_path) + """}
apply: {apply_enabled: true, apply_require_confirm: true, apply_manifest_root: """ + str(tmp_path / "applies") + """}
""")
    runner = CliRunner()
    result = runner.invoke(app, [
        "assist", "apply",
        str(sandbox_workspace),
        str(target),
        "--config", str(config),
    ])
    assert result.exit_code == 0
    assert "confirm" in result.output.lower()


def test_assist_apply_with_confirm(sandbox_workspace: Path, tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from workflow_dataset.cli import app
    target = tmp_path / "target"
    target.mkdir()
    config = tmp_path / "cfg3.yaml"
    config.write_text("""
project: {name: x, version: v1, output_excel: o, output_csv_dir: c, output_parquet_dir: p, qa_report_path: q}
runtime: {timezone: UTC, long_run_profile: true, max_workers: 2, fail_on_missing_provenance: false, infer_low_confidence_threshold: 0.45, infer_high_confidence_threshold: 0.8}
paths: {raw_official: r, raw_private: r, interim: i, processed: p, prompts: pr, context: c, sqlite_path: s, event_log_dir: data/local/event_log, graph_store_path: data/local/work_graph.sqlite}
setup: {setup_dir: """ + str(tmp_path) + """, parsed_artifacts_dir: """ + str(tmp_path) + """, style_signals_dir: """ + str(tmp_path) + """, setup_reports_dir: """ + str(tmp_path) + """, suggestions_dir: """ + str(tmp_path) + """, draft_structures_dir: """ + str(tmp_path) + """}
apply: {apply_enabled: true, apply_require_confirm: true, apply_manifest_root: """ + str(tmp_path / "applies") + """, apply_create_backups: false}
""")
    runner = CliRunner()
    result = runner.invoke(app, [
        "assist", "apply",
        str(sandbox_workspace),
        str(target),
        "--config", str(config),
        "--confirm",
    ])
    assert result.exit_code == 0
    assert "Applied" in result.output
    assert (target / "b.txt").exists() or (target / "a" / "file1.md").exists()
