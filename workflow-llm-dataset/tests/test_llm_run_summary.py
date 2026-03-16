"""Tests for run_summary, successful-run detection, and latest-adapter resolution."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.llm.run_summary import (
    RUN_SUMMARY_FILENAME,
    find_all_successful_adapters,
    find_latest_successful_adapter,
    find_latest_successful_adapter_by_type,
    get_run_type,
    is_successful_run,
    write_run_summary,
)


def test_write_run_summary_success(tmp_path: Path) -> None:
    """write_run_summary creates run_summary.json with expected keys."""
    write_run_summary(
        tmp_path,
        success=True,
        backend="mlx",
        base_model="test/model",
        llm_config_path="/cfg/llm.yaml",
        adapter_path=str(tmp_path / "adapters"),
        start_time="2025-01-01T00:00:00Z",
        end_time="2025-01-01T00:05:00Z",
    )
    path = tmp_path / RUN_SUMMARY_FILENAME
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["success"] is True
    assert data["backend"] == "mlx"
    assert data["base_model"] == "test/model"
    assert "adapter_path" in data
    assert data["error"] == ""


def test_write_run_summary_failure(tmp_path: Path) -> None:
    """write_run_summary with success=False records error."""
    write_run_summary(
        tmp_path,
        success=False,
        backend="mlx",
        base_model="m",
        error="Training failed",
    )
    data = json.loads((tmp_path / RUN_SUMMARY_FILENAME).read_text())
    assert data["success"] is False
    assert data["error"] == "Training failed"


def test_is_successful_run_false_when_no_summary(tmp_path: Path) -> None:
    """is_successful_run returns False when run_summary.json missing."""
    assert is_successful_run(tmp_path) is False


def test_is_successful_run_false_when_success_false(tmp_path: Path) -> None:
    """is_successful_run returns False when success=false in summary."""
    write_run_summary(tmp_path, success=False, adapter_path="")
    assert is_successful_run(tmp_path) is False


def test_is_successful_run_false_when_adapter_path_empty(tmp_path: Path) -> None:
    """is_successful_run returns False when success=true but adapter_path empty."""
    write_run_summary(tmp_path, success=True, adapter_path="")
    assert is_successful_run(tmp_path) is False


def test_is_successful_run_false_when_adapter_dir_missing(tmp_path: Path) -> None:
    """is_successful_run returns False when adapter_path does not exist."""
    write_run_summary(tmp_path, success=True, adapter_path=str(tmp_path / "adapters"))
    assert is_successful_run(tmp_path) is False


def test_is_successful_run_true_when_adapter_exists(tmp_path: Path) -> None:
    """is_successful_run returns True when success=true and adapter dir exists and non-empty."""
    adapters = tmp_path / "adapters"
    adapters.mkdir()
    (adapters / "adapters.npz").write_bytes(b"x")
    write_run_summary(tmp_path, success=True, adapter_path=str(adapters))
    assert is_successful_run(tmp_path) is True


def test_find_latest_successful_adapter_empty_runs_dir(tmp_path: Path) -> None:
    """find_latest_successful_adapter returns ('','') when runs_dir empty or missing."""
    assert find_latest_successful_adapter(tmp_path) == ("", "")
    assert find_latest_successful_adapter(Path("/nonexistent/runs")) == ("", "")


def test_find_latest_successful_adapter_ignores_failed_run(tmp_path: Path) -> None:
    """Failed run (run_summary success=false) is not returned as latest."""
    run1 = tmp_path / "run1"
    run1.mkdir()
    write_run_summary(run1, success=False, adapter_path="")
    adapter_path, run_dir = find_latest_successful_adapter(tmp_path)
    assert adapter_path == ""
    assert run_dir == ""


def test_find_latest_successful_adapter_returns_newest(tmp_path: Path) -> None:
    """find_latest_successful_adapter returns the newest successful run."""
    run1 = tmp_path / "run1"
    run1.mkdir()
    (run1 / "adapters").mkdir()
    (run1 / "adapters" / "a.npz").write_bytes(b"1")
    write_run_summary(run1, success=True, adapter_path=str(run1 / "adapters"))

    run2 = tmp_path / "run2"
    run2.mkdir()
    (run2 / "adapters").mkdir()
    (run2 / "adapters" / "b.npz").write_bytes(b"2")
    write_run_summary(run2, success=True, adapter_path=str(run2 / "adapters"))

    adapter_path, run_dir = find_latest_successful_adapter(tmp_path)
    assert adapter_path != ""
    assert run_dir != ""
    assert "adapters" in adapter_path
    assert Path(adapter_path).exists()


def test_find_all_successful_adapters(tmp_path: Path) -> None:
    """find_all_successful_adapters returns all successful runs, newest first."""
    run1 = tmp_path / "smoke_001"
    run1.mkdir()
    (run1 / "adapters").mkdir()
    (run1 / "adapters" / "x.npz").write_bytes(b"x")
    write_run_summary(run1, success=True, adapter_path=str(run1 / "adapters"))

    run2 = tmp_path / "smoke_002"
    run2.mkdir()
    (run2 / "adapters").mkdir()
    (run2 / "adapters" / "y.npz").write_bytes(b"y")
    write_run_summary(run2, success=True, adapter_path=str(run2 / "adapters"))

    all_adapters = find_all_successful_adapters(tmp_path)
    assert len(all_adapters) == 2
    paths = [a for a, _ in all_adapters]
    assert all("adapters" in p for p in paths)


def test_write_run_summary_includes_run_type(tmp_path: Path) -> None:
    """write_run_summary persists run_type smoke/full."""
    write_run_summary(tmp_path, success=True, adapter_path="", run_type="smoke")
    data = json.loads((tmp_path / RUN_SUMMARY_FILENAME).read_text())
    assert data["run_type"] == "smoke"
    write_run_summary(tmp_path, success=True, adapter_path="", run_type="full")
    data = json.loads((tmp_path / RUN_SUMMARY_FILENAME).read_text())
    assert data["run_type"] == "full"


def test_get_run_type_from_summary(tmp_path: Path) -> None:
    """get_run_type reads run_type from run_summary.json."""
    write_run_summary(tmp_path, success=True, adapter_path="", run_type="full")
    assert get_run_type(tmp_path) == "full"
    write_run_summary(tmp_path, success=True, adapter_path="", run_type="smoke")
    assert get_run_type(tmp_path) == "smoke"


def test_get_run_type_infers_from_dir_name(tmp_path: Path) -> None:
    """get_run_type infers smoke from smoke_* dir when no summary."""
    smoke_dir = tmp_path / "smoke_20250101_120000"
    smoke_dir.mkdir()
    assert get_run_type(smoke_dir) == "smoke"
    full_dir = tmp_path / "20250101_120000"
    full_dir.mkdir()
    assert get_run_type(full_dir) == "full"


def test_find_latest_successful_adapter_by_type(tmp_path: Path) -> None:
    """find_latest_successful_adapter_by_type returns smoke or full adapter."""
    smoke_run = tmp_path / "smoke_20250101_120000"
    smoke_run.mkdir()
    (smoke_run / "adapters").mkdir()
    (smoke_run / "adapters" / "s.npz").write_bytes(b"s")
    write_run_summary(smoke_run, success=True, adapter_path=str(smoke_run / "adapters"), run_type="smoke")

    full_run = tmp_path / "20250102_120000"
    full_run.mkdir()
    (full_run / "adapters").mkdir()
    (full_run / "adapters" / "f.npz").write_bytes(b"f")
    write_run_summary(full_run, success=True, adapter_path=str(full_run / "adapters"), run_type="full")

    smoke_path, smoke_rdir = find_latest_successful_adapter_by_type(tmp_path, "smoke")
    full_path, full_rdir = find_latest_successful_adapter_by_type(tmp_path, "full")
    assert "adapters" in smoke_path and "smoke" in smoke_rdir
    assert "adapters" in full_path and "20250102" in full_rdir
    assert find_latest_successful_adapter_by_type(tmp_path, "nonexistent") == ("", "")
