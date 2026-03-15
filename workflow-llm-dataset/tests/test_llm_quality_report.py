"""Tests for quality_report persistence."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.llm.quality_report import write_quality_report, QUALITY_REPORT_FILENAME


def test_write_quality_report_minimal(tmp_path: Path) -> None:
    """write_quality_report creates quality_report.md with run_summary-derived fields."""
    write_quality_report(tmp_path, run_summary={"base_model": "test", "run_type": "full", "adapter_path": "/a/b"})
    path = tmp_path / QUALITY_REPORT_FILENAME
    assert path.exists()
    text = path.read_text()
    assert "test" in text
    assert "full" in text
    assert "Recommendation" in text


def test_write_quality_report_with_comparison(tmp_path: Path) -> None:
    """write_quality_report includes comparison_slice and retrieval_impact."""
    write_quality_report(
        tmp_path,
        run_summary={"base_model": "m", "run_type": "full"},
        comparison_slice={"prediction_mode": "real_model", "retrieval_used": True, "num_examples": 5, "metrics": {"token_overlap": 0.7}},
        retrieval_impact="token_overlap retrieval_off=0.6 retrieval_on=0.7",
        recommendation="iterate",
    )
    text = (tmp_path / QUALITY_REPORT_FILENAME).read_text()
    assert "token_overlap" in text
    assert "0.7" in text
    assert "iterate" in text


def test_write_quality_report_loads_run_summary(tmp_path: Path) -> None:
    """write_quality_report loads run_summary.json when run_summary not provided."""
    (tmp_path / "run_summary.json").write_text('{"base_model": "loaded", "run_type": "smoke"}')
    write_quality_report(tmp_path)
    text = (tmp_path / QUALITY_REPORT_FILENAME).read_text()
    assert "loaded" in text
    assert "smoke" in text
