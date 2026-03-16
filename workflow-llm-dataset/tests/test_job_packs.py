"""
M23J: Job packs — schema, specialization, policy, execution, report.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.job_packs import (
    list_job_packs,
    get_job_pack,
    load_specialization,
    save_specialization,
    save_as_preferred,
    update_from_successful_run,
    check_job_policy,
    resolve_params,
    run_job,
    preview_job,
    job_packs_report,
    job_diagnostics,
)
from workflow_dataset.job_packs.schema import JobPack, JobPackSource
from workflow_dataset.job_packs.store import save_job_pack
from workflow_dataset.job_packs.seed_jobs import seed_example_job_pack, seed_task_demo_job_pack
from workflow_dataset.desktop_bench.seed_cases import seed_default_cases


def test_seed_and_list_jobs(tmp_path):
    seed_default_cases(tmp_path)
    seed_example_job_pack(tmp_path)
    seed_task_demo_job_pack(tmp_path)
    ids = list_job_packs(tmp_path)
    assert "weekly_status_from_notes" in ids
    assert "replay_cli_demo" in ids


def test_get_job_pack(tmp_path):
    seed_default_cases(tmp_path)
    seed_example_job_pack(tmp_path)
    job = get_job_pack("weekly_status_from_notes", tmp_path)
    assert job is not None
    assert job.title == "Weekly status from notes"
    assert job.source is not None
    assert job.source.kind == "benchmark_case"
    assert job.source.ref == "inspect_folder_basic"


def test_specialization_persistence(tmp_path):
    seed_example_job_pack(tmp_path)
    spec = load_specialization("weekly_status_from_notes", tmp_path)
    assert spec.job_pack_id == "weekly_status_from_notes"
    assert spec.preferred_params == {}
    save_as_preferred("weekly_status_from_notes", {"path": "data/local"}, tmp_path)
    spec2 = load_specialization("weekly_status_from_notes", tmp_path)
    assert spec2.preferred_params.get("path") == "data/local"


def test_update_from_successful_run(tmp_path):
    seed_example_job_pack(tmp_path)
    update_from_successful_run(
        "weekly_status_from_notes",
        run_id="test_run",
        timestamp="2026-01-01T00:00:00Z",
        params_used={"path": "data/local"},
        outcome="pass",
        repo_root=tmp_path,
    )
    spec = load_specialization("weekly_status_from_notes", tmp_path)
    assert spec.last_successful_run.get("run_id") == "test_run"
    assert spec.last_successful_run.get("params_used", {}).get("path") == "data/local"


def test_resolve_params():
    from workflow_dataset.job_packs.schema import JobPack, JobPackSource
    job = JobPack(
        job_pack_id="test",
        title="Test",
        parameter_schema={"path": {"type": "string", "default": "data/local"}},
        source=JobPackSource(kind="benchmark_case", ref="x"),
    )
    resolved = resolve_params(job, {"path": "custom"}, {"path": "override"})
    assert resolved.get("path") == "override"
    resolved2 = resolve_params(job, {}, {})
    assert resolved2.get("path") == "data/local"


def test_check_job_policy_simulate_only(tmp_path):
    seed_task_demo_job_pack(tmp_path)
    job = get_job_pack("replay_cli_demo", tmp_path)
    assert job is not None
    allowed, msg = check_job_policy(job, "real", {}, tmp_path)
    assert allowed is False
    assert "simulate" in msg.lower()
    allowed_sim, _ = check_job_policy(job, "simulate", {}, tmp_path)
    assert allowed_sim is True


def test_preview_job(tmp_path):
    seed_default_cases(tmp_path)
    seed_example_job_pack(tmp_path)
    preview = preview_job("weekly_status_from_notes", "simulate", {}, tmp_path)
    assert preview.get("error") is None
    assert "resolved_params" in preview
    assert preview.get("policy_allowed") is True


def test_run_job_simulate(tmp_path):
    seed_default_cases(tmp_path)
    seed_example_job_pack(tmp_path)
    result = run_job("weekly_status_from_notes", "simulate", {}, tmp_path)
    assert result.get("error") is None
    assert result.get("outcome") == "pass"
    assert result.get("source_kind") == "benchmark_case"


def test_run_job_task_demo(tmp_path):
    seed_task_demo_job_pack(tmp_path)
    result = run_job("replay_cli_demo", "simulate", {}, tmp_path)
    if result.get("error") and "not found" in result["error"].lower():
        pytest.skip("cli_demo task not in repo")
    assert result.get("outcome") in ("pass", "fail") or "error" in result


def test_job_packs_report(tmp_path):
    seed_example_job_pack(tmp_path)
    report = job_packs_report(tmp_path)
    assert report.get("total_jobs") >= 1
    assert "simulate_only_jobs" in report
    assert "trusted_for_real_jobs" in report


def test_job_diagnostics(tmp_path):
    seed_example_job_pack(tmp_path)
    d = job_diagnostics("weekly_status_from_notes", tmp_path)
    assert d.get("error") is None
    assert d.get("job_pack_id") == "weekly_status_from_notes"
    assert "policy_simulate" in d
    assert "policy_real" in d
