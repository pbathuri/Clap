"""M23A: Internal Agent Chain Lab — registry, runner, list/run/status. Operator-controlled; local only."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.chain.registry import (
    load_chain,
    get_chain,
    list_chains,
    _expand_step_to_cmd,
)
from workflow_dataset.chain.runner import run_chain, get_run_status, list_runs


def test_load_chain_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match="Chain not found"):
        load_chain("nonexistent", repo_root=tmp_path)


def test_load_chain_from_json(tmp_path):
    (tmp_path / "data/local/chains").mkdir(parents=True)
    (tmp_path / "data/local/chains/simple.json").write_text(
        '{"id": "simple", "steps": [{"id": "a", "type": "command", "cmd": "echo ok"}]}',
        encoding="utf-8",
    )
    c = load_chain("simple", repo_root=tmp_path)
    assert c["id"] == "simple"
    assert len(c["steps"]) == 1
    assert c["steps"][0]["cmd"] == "echo ok"


def test_get_chain_returns_none_for_missing(tmp_path):
    assert get_chain("missing", repo_root=tmp_path) is None


def test_list_chains_empty(tmp_path):
    assert list_chains(repo_root=tmp_path) == []


def test_list_chains_finds_definitions(tmp_path):
    (tmp_path / "data/local/chains").mkdir(parents=True)
    (tmp_path / "data/local/chains/c1.json").write_text(
        '{"id": "c1", "steps": []}',
        encoding="utf-8",
    )
    items = list_chains(repo_root=tmp_path)
    assert len(items) == 1
    assert items[0]["id"] == "c1"


def test_expand_step_to_cmd_command(tmp_path):
    cmd = _expand_step_to_cmd({"type": "command", "cmd": "echo hi"}, tmp_path)
    assert cmd == "echo hi"


def test_expand_step_to_cmd_intake_add(tmp_path):
    cmd = _expand_step_to_cmd(
        {"type": "intake_add", "params": {"path": "./x", "label": "l1"}},
        tmp_path,
    )
    assert "intake add" in cmd
    assert "l1" in cmd


def test_run_chain_persists_outputs(tmp_path):
    (tmp_path / "data/local/chains").mkdir(parents=True)
    (tmp_path / "data/local/chains/echo_chain.json").write_text(
        json.dumps({
            "id": "echo_chain",
            "steps": [
                {"id": "s1", "type": "command", "cmd": "echo step1"},
                {"id": "s2", "type": "command", "cmd": "echo step2"},
            ],
            "stop_conditions": {"on_step_failure": True},
        }),
        encoding="utf-8",
    )
    run_dir = run_chain("echo_chain", repo_root=tmp_path)
    assert run_dir.exists()
    assert (run_dir / "chain_definition.json").exists()
    assert (run_dir / "run_report.json").exists()
    report = json.loads((run_dir / "run_report.json").read_text(encoding="utf-8"))
    assert report["status"] == "completed"
    assert len(report["steps"]) == 2
    assert report["steps"][0]["status"] == "ok"
    assert report["steps"][1]["status"] == "ok"


def test_get_run_status_latest(tmp_path):
    (tmp_path / "data/local/chains").mkdir(parents=True)
    (tmp_path / "data/local/chains/runs").mkdir(parents=True)
    run_dir = tmp_path / "data/local/chains/runs/20250101_abc"
    run_dir.mkdir(parents=True)
    (run_dir / "run_report.json").write_text(
        json.dumps({"run_id": "20250101_abc", "chain_id": "c1", "status": "completed", "steps": []}),
        encoding="utf-8",
    )
    report = get_run_status("latest", repo_root=tmp_path)
    assert report is not None
    assert report["run_id"] == "20250101_abc"
    assert report["status"] == "completed"


def test_list_runs(tmp_path):
    (tmp_path / "data/local/chains/runs").mkdir(parents=True)
    r1 = tmp_path / "data/local/chains/runs/20250101_aaa"
    r1.mkdir()
    (r1 / "run_report.json").write_text(
        json.dumps({"run_id": "20250101_aaa", "chain_id": "x", "status": "completed", "steps_total": 1}),
        encoding="utf-8",
    )
    items = list_runs(limit=5, repo_root=tmp_path)
    assert len(items) >= 1
    assert items[0]["run_id"] == "20250101_aaa"
