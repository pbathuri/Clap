"""M23E-F1: Task demonstration capture + replay. Simulate-only replay."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.task_demos import (
    TaskDefinition,
    TaskStep,
    list_tasks,
    get_task,
    save_task,
    replay_task_simulate,
    format_task_manifest,
    format_replay_report,
)


def test_save_and_load_task(tmp_path):
    task = TaskDefinition(
        task_id="demo1",
        steps=[
            TaskStep("file_ops", "inspect_path", {"path": "/tmp"}),
            TaskStep("browser_open", "open_url", {"url": "https://example.com"}),
        ],
        notes="Demo task",
    )
    save_task(task, tmp_path)
    loaded = get_task("demo1", tmp_path)
    assert loaded is not None
    assert loaded.task_id == "demo1"
    assert len(loaded.steps) == 2
    assert loaded.steps[0].adapter_id == "file_ops"
    assert loaded.steps[0].action_id == "inspect_path"
    assert loaded.steps[1].params.get("url") == "https://example.com"
    assert loaded.notes == "Demo task"


def test_list_tasks(tmp_path):
    save_task(TaskDefinition("a", [TaskStep("file_ops", "list_dir", {"path": "."})]), tmp_path)
    save_task(TaskDefinition("b", [TaskStep("browser_open", "open_url", {"url": "https://x.com"})]), tmp_path)
    ids = list_tasks(tmp_path)
    assert "a" in ids
    assert "b" in ids


def test_get_task_missing_returns_none(tmp_path):
    assert get_task("nonexistent", tmp_path) is None


def test_replay_task_simulate(tmp_path):
    task = TaskDefinition(
        task_id="replay_test",
        steps=[
            TaskStep("browser_open", "open_url", {"url": "https://example.com"}),
        ],
    )
    save_task(task, tmp_path)
    t, results = replay_task_simulate("replay_test", tmp_path)
    assert t is not None
    assert t.task_id == "replay_test"
    assert len(results) == 1
    assert results[0].success is True
    assert "Simulate" in results[0].preview or "open" in results[0].preview.lower()


def test_replay_task_unknown_returns_none_empty(tmp_path):
    t, results = replay_task_simulate("unknown_task_xyz", tmp_path)
    assert t is None
    assert results == []


def test_format_task_manifest():
    task = TaskDefinition("m1", [TaskStep("file_ops", "inspect_path", {"path": "/tmp"}, "check path")], "My notes")
    report = format_task_manifest(task)
    assert "m1" in report
    assert "file_ops" in report
    assert "inspect_path" in report
    assert "path=/tmp" in report or "path" in report
    assert "My notes" in report


def test_format_replay_report():
    from workflow_dataset.desktop_adapters.simulate import SimulateResult
    task = TaskDefinition("r1", [TaskStep("file_ops", "list_directory", {"path": "."})])
    results = [SimulateResult(True, "file_ops", "list_directory", "ok", "preview here")]
    report = format_replay_report(task, results)
    assert "r1" in report
    assert "simulate" in report.lower()
    assert "ok" in report or "preview" in report
