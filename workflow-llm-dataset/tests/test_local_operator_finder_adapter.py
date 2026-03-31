"""Finder adapter: bounded open-folder; dry-run for CI."""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.local_operator.adapters.finder import run_open_folder


def test_finder_adapter_rejects_missing_dir(tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    r = run_open_folder(str(missing))
    assert r.success is False
    assert r.error == "path_not_found"


def test_finder_adapter_dry_run_bounded(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("WORKFLOW_DATASET_FINDER_DRY_RUN", "1")
    d = tmp_path / "approved"
    d.mkdir()
    r = run_open_folder(str(d))
    assert r.success is True
    assert str(d) in r.path or r.path.endswith("approved")
