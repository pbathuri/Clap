"""Tests for compare_runs: comparison report generation without real inference."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.llm.compare_runs import run_comparison, _write_comparison_md


@pytest.fixture
def test_jsonl(tmp_path: Path) -> Path:
    p = tmp_path / "test.jsonl"
    ex = {
        "eval_id": "1",
        "task_type": "knowledge_qa",
        "messages": [
            {"role": "user", "content": "What does an operator do?"},
            {"role": "assistant", "content": "They coordinate tasks."},
        ],
        "reference": "They coordinate tasks.",
    }
    with open(p, "w", encoding="utf-8") as f:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    return p


def test_run_comparison_baseline_only(test_jsonl: Path, tmp_path: Path) -> None:
    """run_comparison with no adapters still runs baseline slices and writes report."""
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    cfg = {"backend": "mlx", "base_model": "test", "corpus_path": str(tmp_path / "corpus.jsonl")}
    out_dir = tmp_path / "comparison_out"
    payload = run_comparison(cfg, test_jsonl, runs_dir, output_dir=out_dir, skip_missing=True)
    assert "error" not in payload or payload.get("error") is None
    assert "slices" in payload
    baseline_slices = [s for s in payload["slices"] if s.get("slice_id") == "baseline"]
    assert len(baseline_slices) == 1
    assert baseline_slices[0].get("skipped") is not True
    assert "metrics" in baseline_slices[0]
    assert (runs_dir / "comparison_latest.json").exists()
    assert (runs_dir / "comparison_latest.md").exists()


def test_write_comparison_md(tmp_path: Path) -> None:
    """_write_comparison_md produces markdown with slice metrics."""
    payload = {
        "comparison_time": "2025-01-01T12:00:00Z",
        "test_path": "/test.jsonl",
        "output_dir": str(tmp_path),
        "slices": [
            {"slice_id": "baseline", "retrieval_used": False, "num_examples": 10, "metrics": {"token_overlap": 0.5}},
            {"slice_id": "baseline_retrieval", "retrieval_used": True, "num_examples": 10, "metrics": {"token_overlap": 0.6}},
        ],
    }
    report_path = _write_comparison_md(tmp_path, payload)
    assert report_path.exists()
    text = report_path.read_text()
    assert "baseline" in text
    assert "0.5" in text or "0.6" in text
    assert "Retrieval impact" in text
