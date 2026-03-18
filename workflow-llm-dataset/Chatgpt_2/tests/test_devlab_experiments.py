"""
M21Z: Tests for experiment scheduler and patch proposal factory. No auto-apply.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_experiment_config_paths(tmp_path: Path) -> None:
    from workflow_dataset.devlab.config import get_experiments_dir, get_proposals_dir, get_experiment_queue_path
    root = tmp_path
    get_experiments_dir(root)
    proposals_dir = get_proposals_dir(root)
    assert (tmp_path / "experiments").exists()
    assert proposals_dir.exists() and proposals_dir.name == "proposals"
    assert get_experiment_queue_path(root).name == "experiment_queue.json"


def test_save_load_experiment(tmp_path: Path) -> None:
    from workflow_dataset.devlab.experiments import save_experiment, load_experiment, list_experiments
    definition = {"id": "test_exp", "goal": "Test", "benchmark_suite": "ops_reporting_core"}
    save_experiment(definition, tmp_path)
    loaded = load_experiment("test_exp", tmp_path)
    assert loaded and loaded["id"] == "test_exp"
    assert len(list_experiments(tmp_path)) >= 1


def test_queue_experiment(tmp_path: Path) -> None:
    from workflow_dataset.devlab.experiments import save_experiment, queue_experiment, load_queue
    save_experiment({"id": "qtest", "goal": "Q", "benchmark_suite": "ops_reporting_core"}, tmp_path)
    entry = queue_experiment("qtest", tmp_path)
    assert entry["status"] == "queued"
    assert entry["experiment_id"] == "qtest"
    q = load_queue(tmp_path)
    assert len(q) == 1


def test_queue_status(tmp_path: Path) -> None:
    from workflow_dataset.devlab.experiments import get_queue_status
    s = get_queue_status(tmp_path)
    assert "queued" in s and "running" in s and "done" in s


def test_seed_default_experiment(tmp_path: Path) -> None:
    from workflow_dataset.devlab.experiments import seed_default_experiment, load_experiment
    d = seed_default_experiment(tmp_path)
    assert d["id"] == "ops_reporting_benchmark"
    assert load_experiment("ops_reporting_benchmark", tmp_path) is not None


def test_list_and_get_proposal(tmp_path: Path) -> None:
    from workflow_dataset.devlab.proposals import list_proposals, get_proposal
    prop_dir = tmp_path / "proposals"
    prop_dir.mkdir(parents=True)
    (prop_dir / "prop1").mkdir()
    (prop_dir / "prop1" / "manifest.json").write_text(
        json.dumps({"proposal_id": "prop1", "status": "pending", "experiment_id": "e1", "run_id": "r1", "created_at": "2025-01-01"}),
        encoding="utf-8",
    )
    proposals = list_proposals(tmp_path)
    assert len(proposals) == 1
    assert proposals[0]["proposal_id"] == "prop1"
    p = get_proposal("prop1", tmp_path)
    assert p and p["status"] == "pending"


def test_update_proposal_status(tmp_path: Path) -> None:
    from workflow_dataset.devlab.proposals import update_proposal_status, get_proposal
    prop_dir = tmp_path / "proposals" / "prop2"
    prop_dir.mkdir(parents=True)
    (prop_dir / "manifest.json").write_text(
        json.dumps({"proposal_id": "prop2", "status": "pending", "created_at": "2025-01-01", "operator_notes": ""}),
        encoding="utf-8",
    )
    ok = update_proposal_status("prop2", "accepted", operator_notes="LGTM", root=tmp_path)
    assert ok
    p = get_proposal("prop2", tmp_path)
    assert p["status"] == "accepted" and p.get("operator_notes") == "LGTM"


def test_run_experiment_missing_definition(tmp_path: Path) -> None:
    from workflow_dataset.devlab.experiment_runner import run_experiment
    result = run_experiment("nonexistent", tmp_path)
    assert result.get("status") == "failed"
    assert "not found" in result.get("error", "").lower()


# ----- D4: Scheduler + run history board -----


def test_list_recent_runs_empty(tmp_path: Path) -> None:
    from workflow_dataset.devlab.experiments import list_recent_runs
    runs = list_recent_runs(limit=10, root=tmp_path)
    assert runs == []


def test_list_recent_runs_newest_first(tmp_path: Path) -> None:
    from workflow_dataset.devlab.experiments import save_queue, list_recent_runs
    q = [
        {"experiment_id": "a", "status": "done", "queued_at": "2025-01-01T10:00:00Z", "completed_at": "2025-01-01T10:05:00Z", "run_id": "r1", "proposal_id": "p1"},
        {"experiment_id": "b", "status": "done", "queued_at": "2025-01-01T11:00:00Z", "completed_at": "2025-01-01T11:05:00Z", "run_id": "r2", "proposal_id": "p2"},
    ]
    save_queue(q, tmp_path)
    runs = list_recent_runs(limit=5, root=tmp_path)
    assert len(runs) == 2
    assert runs[0].get("_index") == 0 and runs[0].get("experiment_id") == "b"
    assert runs[1].get("experiment_id") == "a"


def test_get_run_entry_by_run_id(tmp_path: Path) -> None:
    from workflow_dataset.devlab.experiments import save_queue, get_run_entry
    save_queue([{"experiment_id": "x", "status": "done", "run_id": "run_abc", "queued_at": "2025-01-01T00:00:00Z"}], tmp_path)
    entry = get_run_entry(run_id="run_abc", root=tmp_path)
    assert entry is not None and entry["experiment_id"] == "x" and entry["run_id"] == "run_abc"


def test_get_run_entry_by_index(tmp_path: Path) -> None:
    from workflow_dataset.devlab.experiments import save_queue, get_run_entry
    save_queue([
        {"experiment_id": "first", "status": "done", "queued_at": "2025-01-01T09:00:00Z"},
        {"experiment_id": "second", "status": "queued", "queued_at": "2025-01-01T10:00:00Z"},
    ], tmp_path)
    entry = get_run_entry(index=0, root=tmp_path)
    assert entry is not None and entry["experiment_id"] == "second"
    entry1 = get_run_entry(index=1, root=tmp_path)
    assert entry1 is not None and entry1["experiment_id"] == "first"


def test_get_run_entry_by_experiment_id(tmp_path: Path) -> None:
    from workflow_dataset.devlab.experiments import save_queue, get_run_entry
    save_queue([
        {"experiment_id": "e1", "status": "done", "queued_at": "2025-01-01T08:00:00Z", "completed_at": "2025-01-01T08:10:00Z"},
        {"experiment_id": "e1", "status": "done", "queued_at": "2025-01-01T09:00:00Z", "completed_at": "2025-01-01T09:10:00Z"},
    ], tmp_path)
    entry = get_run_entry(experiment_id="e1", root=tmp_path)
    assert entry is not None and "2025-01-01T09" in (entry.get("completed_at") or "")


def test_cancel_queued(tmp_path: Path) -> None:
    from workflow_dataset.devlab.experiments import save_queue, cancel_queued, load_queue
    save_queue([{"experiment_id": "cancel_me", "status": "queued", "queued_at": "2025-01-01T12:00:00Z"}], tmp_path)
    ok = cancel_queued("cancel_me", tmp_path)
    assert ok
    q = load_queue(tmp_path)
    assert q[0]["status"] == "cancelled"


def test_cancel_queued_no_match(tmp_path: Path) -> None:
    from workflow_dataset.devlab.experiments import cancel_queued
    ok = cancel_queued("nonexistent", tmp_path)
    assert not ok


def test_cancel_queued_by_index(tmp_path: Path) -> None:
    from workflow_dataset.devlab.experiments import save_queue, cancel_queued_by_index, load_queue
    save_queue([
        {"experiment_id": "e1", "status": "done", "queued_at": "2025-01-01T10:00:00Z", "completed_at": "2025-01-01T10:05:00Z"},
        {"experiment_id": "e2", "status": "queued", "queued_at": "2025-01-01T11:00:00Z"},
    ], tmp_path)
    ok = cancel_queued_by_index(0, tmp_path)
    assert ok
    q = load_queue(tmp_path)
    queued_entry = next((e for e in q if e["experiment_id"] == "e2"), None)
    assert queued_entry is not None and queued_entry["status"] == "cancelled"


def test_run_next_queued_empty(tmp_path: Path) -> None:
    from workflow_dataset.devlab.experiments import run_next_queued
    out = run_next_queued(tmp_path)
    assert out.get("ran") is False and out.get("reason") == "no_queued"


def test_run_next_queued_skips_cancelled(tmp_path: Path) -> None:
    from workflow_dataset.devlab.experiments import save_queue, run_next_queued
    save_queue([{"experiment_id": "cancelled", "status": "cancelled", "queued_at": "2025-01-01T12:00:00Z"}], tmp_path)
    out = run_next_queued(tmp_path)
    assert out.get("ran") is False


def test_queue_status_includes_cancelled(tmp_path: Path) -> None:
    from workflow_dataset.devlab.experiments import save_queue, get_queue_status
    save_queue([
        {"experiment_id": "a", "status": "queued", "queued_at": "2025-01-01T10:00:00Z"},
        {"experiment_id": "b", "status": "cancelled", "queued_at": "2025-01-01T11:00:00Z", "completed_at": "2025-01-01T11:01:00Z"},
    ], tmp_path)
    s = get_queue_status(tmp_path)
    assert s.get("queued") == 1 and s.get("cancelled") == 1
