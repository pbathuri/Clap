"""M22D: Local Knowledge Intake Center — registry, snapshot, load, report. Local-only."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.intake.registry import (
    INTAKE_ROOT,
    INPUT_TYPES,
    add_intake,
    get_intake,
    list_intakes,
)
from workflow_dataset.intake.load import load_intake_content
from workflow_dataset.intake.report import intake_report, format_intake_report_text


def test_input_types_constant():
    assert "notes" in INPUT_TYPES
    assert "mixed" in INPUT_TYPES


def test_add_intake_creates_snapshot(tmp_path):
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes" / "a.md").write_text("# Note", encoding="utf-8")
    (tmp_path / "notes" / "b.txt").write_text("text", encoding="utf-8")
    entry = add_intake("sprint_notes", [tmp_path / "notes"], input_type="notes", repo_root=tmp_path)
    assert entry["label"] == "sprint_notes"
    assert entry["input_type"] == "notes"
    assert entry["file_count"] >= 1
    assert "sprint_notes" in (entry.get("snapshot_dir") or "")
    reg_dir = tmp_path / INTAKE_ROOT
    assert reg_dir.exists()
    assert (reg_dir / "registry.json").exists()


def test_get_intake(tmp_path):
    (tmp_path / "d").mkdir()
    (tmp_path / "d" / "x.md").write_text("x", encoding="utf-8")
    add_intake("my_set", [tmp_path / "d"], repo_root=tmp_path)
    entry = get_intake("my_set", repo_root=tmp_path)
    assert entry is not None
    assert entry.get("label") == "my_set"


def test_list_intakes(tmp_path):
    (tmp_path / "d").mkdir()
    (tmp_path / "d" / "f.md").write_text("f", encoding="utf-8")
    add_intake("a", [tmp_path / "d"], repo_root=tmp_path)
    add_intake("b", [tmp_path / "d"], repo_root=tmp_path)
    items = list_intakes(repo_root=tmp_path)
    labels = [i["label"] for i in items]
    assert "a" in labels
    assert "b" in labels


def test_load_intake_content(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "one.md").write_text("Hello", encoding="utf-8")
    add_intake("test_load", [tmp_path / "src"], repo_root=tmp_path)
    content, sources = load_intake_content("test_load", repo_root=tmp_path)
    assert "Hello" in content
    assert len(sources) >= 1
    assert sources[0].get("type") == "intake"
    assert sources[0].get("path_or_name") == "test_load"


def test_intake_report(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "readme.md").write_text("# Doc", encoding="utf-8")
    add_intake("docs_set", [tmp_path / "docs"], input_type="docs", repo_root=tmp_path)
    report = intake_report("docs_set", repo_root=tmp_path)
    assert report.get("error") is None
    assert report.get("label") == "docs_set"
    assert "file_inventory" in report
    assert "parse_summary" in report
    assert "suggested_workflows" in report


def test_format_intake_report_text(tmp_path):
    (tmp_path / "x").mkdir()
    (tmp_path / "x" / "y.md").write_text("y", encoding="utf-8")
    add_intake("fmt", [tmp_path / "x"], repo_root=tmp_path)
    report = intake_report("fmt", repo_root=tmp_path)
    text = format_intake_report_text(report)
    assert "Intake:" in text
    assert "fmt" in text
    assert "Suggested workflows" in text
