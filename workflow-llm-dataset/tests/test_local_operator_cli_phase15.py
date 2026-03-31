"""CLI: local approved-folders + summary (Phase 1.5)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("typer")


def test_cli_approved_folders_empty_list(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from workflow_dataset.cli import app

    runner = CliRunner()
    r = runner.invoke(app, ["local", "approved-folders", "list", "--repo-root", str(tmp_path)])
    assert r.exit_code == 0
    assert "none" in r.output.lower() or "(none)" in r.output


def test_cli_approved_folders_add_list_revoke(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from workflow_dataset.cli import app

    d = tmp_path / "workspace"
    d.mkdir()
    runner = CliRunner()
    r = runner.invoke(
        app,
        [
            "local",
            "approved-folders",
            "add",
            "--path",
            str(d),
            "--ops",
            "read",
            "--repo-root",
            str(tmp_path),
        ],
    )
    assert r.exit_code == 0, r.output
    r2 = runner.invoke(app, ["local", "approved-folders", "list", "--repo-root", str(tmp_path)])
    assert r2.exit_code == 0
    assert str(d) in r2.output or d.name in r2.output
    assert "active" in r2.output.lower()
    r3 = runner.invoke(
        app,
        [
            "local",
            "approved-folders",
            "revoke",
            "--path",
            str(d),
            "--repo-root",
            str(tmp_path),
        ],
    )
    assert r3.exit_code == 0
    r4 = runner.invoke(
        app, ["local", "approved-folders", "list", "--all", "--repo-root", str(tmp_path)]
    )
    assert "revoked" in r4.output.lower()


def test_cli_summary_includes_readiness(tmp_path: Path) -> None:
    from typer.testing import CliRunner
    from workflow_dataset.cli import app

    runner = CliRunner()
    r = runner.invoke(app, ["local", "summary", "--repo-root", str(tmp_path)])
    assert r.exit_code == 0
    assert "Machine:" in r.output or "machine" in r.output.lower()
    assert "Operator:" in r.output or "operator" in r.output.lower()
    assert "Last execution" in r.output
