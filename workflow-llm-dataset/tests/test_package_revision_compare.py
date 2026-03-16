"""
Tests for M21T-F2: Revision lineage and package compare.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from workflow_dataset.release.package_compare import (
    compare_packages,
    format_package_compare_for_console,
    get_package_artifact_files,
    load_package_manifest,
)
from workflow_dataset.release.package_revision import (
    get_lineage,
    load_revision_meta,
    save_revision_meta,
    set_package_status,
    set_supersedes,
)

runner = CliRunner()


def test_load_revision_meta_missing(tmp_path: Path) -> None:
    """Missing revision_meta.json returns defaults (status approved)."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    meta = load_revision_meta(pkg)
    assert meta["status"] == "approved"
    assert meta["supersedes"] is None
    assert meta["superseded_by"] is None


def test_save_and_load_revision_meta(tmp_path: Path) -> None:
    """Round-trip revision metadata."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    save_revision_meta(pkg, status="needs_revision", revision_note="fix section 2")
    meta = load_revision_meta(pkg)
    assert meta["status"] == "needs_revision"
    assert meta["revision_note"] == "fix section 2"
    assert meta["updated_at"] is not None


def test_set_supersedes(tmp_path: Path) -> None:
    """set_supersedes(B, A) writes B.supersedes=A, A.status=superseded, A.superseded_by=B."""
    pkg_a = tmp_path / "pkg_a"
    pkg_b = tmp_path / "pkg_b"
    pkg_a.mkdir()
    pkg_b.mkdir()
    set_supersedes(pkg_b, pkg_a, reason="new run", note="LGTM")
    meta_a = load_revision_meta(pkg_a)
    meta_b = load_revision_meta(pkg_b)
    assert meta_a["status"] == "superseded"
    assert meta_a["superseded_by"] == str(pkg_b.resolve())
    assert meta_b["supersedes"] == str(pkg_a.resolve())
    assert meta_b["revision_reason"] == "new run"
    assert meta_b["revision_note"] == "LGTM"


def test_set_package_status(tmp_path: Path) -> None:
    """set_package_status sets status and updates revision_meta."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    set_package_status(pkg, "archived", note="EOL")
    meta = load_revision_meta(pkg)
    assert meta["status"] == "archived"
    assert meta["revision_note"] == "EOL"


def test_save_revision_meta_invalid_status(tmp_path: Path) -> None:
    """save_revision_meta with invalid status raises ValueError."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    with pytest.raises(ValueError, match="status must be one of"):
        save_revision_meta(pkg, status="invalid")


def test_get_lineage(tmp_path: Path) -> None:
    """get_lineage returns path, name, status, supersedes, superseded_by, notes."""
    pkg = tmp_path / "my_pkg"
    pkg.mkdir()
    save_revision_meta(pkg, status="approved")
    lineage = get_lineage(pkg)
    assert lineage["name"] == "my_pkg"
    assert lineage["path"] == str(pkg.resolve())
    assert lineage["status"] == "approved"


def test_load_package_manifest(tmp_path: Path) -> None:
    """load_package_manifest loads package_manifest.json."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "package_manifest.json").write_text(
        json.dumps({"workflow": "weekly_status", "artifact_count": 2}, indent=2),
        encoding="utf-8",
    )
    manifest = load_package_manifest(pkg)
    assert manifest is not None
    assert manifest["workflow"] == "weekly_status"
    assert manifest["artifact_count"] == 2


def test_load_package_manifest_missing(tmp_path: Path) -> None:
    """load_package_manifest returns None when file missing."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    assert load_package_manifest(pkg) is None


def test_get_package_artifact_files(tmp_path: Path) -> None:
    """get_package_artifact_files excludes meta files."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "package_manifest.json").write_text("{}", encoding="utf-8")
    (pkg / "weekly_status.md").write_text("# Status", encoding="utf-8")
    (pkg / "approved_summary.md").write_text("# Summary", encoding="utf-8")
    (pkg / "revision_meta.json").write_text("{}", encoding="utf-8")
    files = get_package_artifact_files(pkg)
    assert "weekly_status.md" in files
    assert "package_manifest.json" not in files
    assert "approved_summary.md" not in files
    assert "revision_meta.json" not in files


def test_compare_packages_inventory(tmp_path: Path) -> None:
    """compare_packages returns inventory diff (only_in_a, only_in_b, common)."""
    pkg_a = tmp_path / "a"
    pkg_b = tmp_path / "b"
    pkg_a.mkdir()
    pkg_b.mkdir()
    (pkg_a / "package_manifest.json").write_text(
        json.dumps({"workflow": "w", "approved_artifacts": ["x.md", "y.md"]}, indent=2),
        encoding="utf-8",
    )
    (pkg_b / "package_manifest.json").write_text(
        json.dumps({"workflow": "w", "approved_artifacts": ["y.md", "z.md"]}, indent=2),
        encoding="utf-8",
    )
    (pkg_a / "x.md").write_text("x", encoding="utf-8")
    (pkg_a / "y.md").write_text("y", encoding="utf-8")
    (pkg_b / "y.md").write_text("y changed", encoding="utf-8")
    (pkg_b / "z.md").write_text("z", encoding="utf-8")
    result = compare_packages(pkg_a, pkg_b, include_content_diff=True)
    assert result["files_only_in_a"] == ["x.md"]
    assert result["files_only_in_b"] == ["z.md"]
    assert result["files_common"] == ["y.md"]
    assert "y.md" in result["artifact_deltas"]
    assert result["artifact_deltas"]["y.md"]["diff_lines"] > 0


def test_compare_packages_no_diffs(tmp_path: Path) -> None:
    """compare_packages with include_content_diff=False has empty artifact_deltas."""
    pkg_a = tmp_path / "a"
    pkg_b = tmp_path / "b"
    pkg_a.mkdir()
    pkg_b.mkdir()
    (pkg_a / "package_manifest.json").write_text(json.dumps({"workflow": "w"}, indent=2), encoding="utf-8")
    (pkg_b / "package_manifest.json").write_text(json.dumps({"workflow": "w"}, indent=2), encoding="utf-8")
    result = compare_packages(pkg_a, pkg_b, include_content_diff=False)
    assert result["artifact_deltas"] == {}


def test_format_package_compare_for_console(tmp_path: Path) -> None:
    """format_package_compare_for_console returns readable string."""
    pkg_a = tmp_path / "a"
    pkg_b = tmp_path / "b"
    pkg_a.mkdir()
    pkg_b.mkdir()
    (pkg_a / "package_manifest.json").write_text(json.dumps({"workflow": "w1"}, indent=2), encoding="utf-8")
    (pkg_b / "package_manifest.json").write_text(json.dumps({"workflow": "w2"}, indent=2), encoding="utf-8")
    result = compare_packages(pkg_a, pkg_b, include_content_diff=False)
    out = format_package_compare_for_console(result)
    assert "Package compare" in out
    assert "A:" in out and "B:" in out
    assert "Artifact inventory" in out
    assert "Manifest" in out or "workflow" in out


def _has_yaml() -> bool:
    import importlib.util
    return importlib.util.find_spec("yaml") is not None


@pytest.mark.skipif(not _has_yaml(), reason="CLI tests require pyyaml")
def test_review_package_compare_cli_help() -> None:
    """review package-compare --help shows options."""
    from workflow_dataset.cli import app
    result = runner.invoke(app, ["review", "package-compare", "--help"])
    assert result.exit_code == 0
    assert "package-a" in result.output or "package_a" in result.output
    assert "package-b" in result.output or "package_b" in result.output


@pytest.mark.skipif(not _has_yaml(), reason="CLI tests require pyyaml")
def test_review_mark_superseded_cli_help() -> None:
    """review mark-superseded --help shows options."""
    from workflow_dataset.cli import app
    result = runner.invoke(app, ["review", "mark-superseded", "--help"])
    assert result.exit_code == 0
    assert "supersedes" in result.output.lower()


@pytest.mark.skipif(not _has_yaml(), reason="CLI tests require pyyaml")
def test_review_package_lineage_cli_help() -> None:
    """review package-lineage --help shows argument."""
    from workflow_dataset.cli import app
    result = runner.invoke(app, ["review", "package-lineage", "--help"])
    assert result.exit_code == 0
    assert "package" in result.output.lower()


@pytest.mark.skipif(not _has_yaml(), reason="CLI tests require pyyaml")
def test_review_set_package_status_cli_help() -> None:
    """review set-package-status --help shows status options."""
    from workflow_dataset.cli import app
    result = runner.invoke(app, ["review", "set-package-status", "--help"])
    assert result.exit_code == 0
    assert "status" in result.output.lower()
