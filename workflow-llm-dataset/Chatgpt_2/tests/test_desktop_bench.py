"""
M23I: Desktop benchmark harness — schema, harness, trusted actions, scoring, board.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.desktop_bench import (
    list_cases,
    get_case,
    load_suite,
    run_benchmark,
    run_suite,
    get_trusted_real_actions,
    score_run,
    compute_trust_status,
    list_runs,
    get_run,
    board_report,
    compare_runs,
)
from workflow_dataset.desktop_bench.config import get_cases_dir, get_runs_dir
from workflow_dataset.desktop_bench.schema import DesktopBenchmarkCase, load_case
from workflow_dataset.desktop_bench.seed_cases import seed_default_cases, seed_default_suite


def test_seed_and_list_cases(tmp_path):
    seed_default_cases(tmp_path)
    seed_default_suite(tmp_path)
    ids = list_cases(tmp_path)
    assert "inspect_folder_basic" in ids
    assert "simulate_browser_open" in ids


def test_get_case(tmp_path):
    seed_default_cases(tmp_path)
    c = get_case("inspect_folder_basic", tmp_path)
    assert c is not None
    assert c.benchmark_id == "inspect_folder_basic"
    assert c.task_category == "inspect_folder"
    assert "file_ops" in c.required_adapters
    assert c.real_mode_eligibility is True


def test_run_benchmark_simulate(tmp_path):
    seed_default_cases(tmp_path)
    r = run_benchmark("inspect_folder_basic", "simulate", repo_root=tmp_path)
    assert "error" not in r
    assert r.get("outcome") == "pass"
    assert r.get("mode") == "simulate"
    assert r.get("benchmark_id") == "inspect_folder_basic"
    assert "run_path" in r
    assert (Path(r["run_path"]) / "run_manifest.json").exists()


def test_run_benchmark_real_requires_registry(tmp_path):
    seed_default_cases(tmp_path)
    # No approval registry -> real mode refused
    r = run_benchmark("inspect_folder_basic", "real", repo_root=tmp_path)
    assert r.get("error") is not None
    assert "approval registry" in r["error"].lower() or "approvals" in r["error"].lower()


def test_run_suite_simulate(tmp_path):
    seed_default_cases(tmp_path)
    seed_default_suite(tmp_path)
    r = run_suite("desktop_bridge_core", "simulate", repo_root=tmp_path)
    assert "error" not in r
    assert "run_id" in r
    assert "cases" in r
    assert r.get("aggregate_outcome") in ("pass", "fail")


def test_trusted_actions(tmp_path):
    t = get_trusted_real_actions(tmp_path)
    assert "trusted_actions" in t
    assert "registry_path" in t
    assert "ready_for_real" in t
    assert isinstance(t["trusted_actions"], list)


def test_score_run(tmp_path):
    seed_default_cases(tmp_path)
    r = run_benchmark("inspect_folder_basic", "simulate", repo_root=tmp_path)
    assert "error" not in r
    run_path = Path(r["run_path"])
    scored = score_run(run_path)
    assert scored.get("scores") is not None
    assert "approval_correctness" in scored.get("scores", {})
    assert scored.get("trust_status") in (
        "trusted",
        "usable_with_simulation_only",
        "approval_missing",
        "experimental",
        "regression_detected",
    )


def test_board_report(tmp_path):
    seed_default_cases(tmp_path)
    run_benchmark("inspect_folder_basic", "simulate", repo_root=tmp_path)
    report = board_report(limit_runs=5, root=tmp_path)
    assert "latest_run_id" in report
    assert "latest_outcome" in report
    assert "recommended_next_action" in report


def test_compare_runs(tmp_path):
    seed_default_cases(tmp_path)
    r1 = run_benchmark("inspect_folder_basic", "simulate", repo_root=tmp_path)
    r2 = run_benchmark("simulate_browser_open", "simulate", repo_root=tmp_path)
    comp = compare_runs(r1["run_id"], r2["run_id"], root=tmp_path)
    assert "run_a" in comp
    assert "run_b" in comp
    assert "regression_detected" in comp
    assert "error" not in comp


def test_run_benchmark_invalid_mode(tmp_path):
    seed_default_cases(tmp_path)
    r = run_benchmark("inspect_folder_basic", "invalid", repo_root=tmp_path)
    assert r.get("error") is not None
    assert "mode" in r["error"].lower()


def test_run_benchmark_real_eligibility_refused(tmp_path):
    seed_default_cases(tmp_path)
    # simulate_browser_open has real_mode_eligibility: false
    r = run_benchmark("simulate_browser_open", "real", repo_root=tmp_path)
    assert r.get("error") is not None
    assert "eligible" in r["error"].lower() or "real_mode" in r["error"].lower()
