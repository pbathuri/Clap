"""Tests for LLM eval: metrics, run_eval on toy fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.llm.eval import (
    exact_match,
    token_overlap,
    explanation_completeness,
    compute_metrics,
    run_eval,
)


def test_exact_match() -> None:
    assert exact_match("yes", "yes") == 1.0
    assert exact_match("yes", "no") == 0.0
    assert exact_match("  yes  ", "yes") == 1.0


def test_token_overlap() -> None:
    assert token_overlap("hello world", "hello world") == 1.0
    assert token_overlap("hello", "world") == 0.0
    assert token_overlap("a b c", "a b") > 0.5


def test_explanation_completeness() -> None:
    assert explanation_completeness("short") == 0.0
    long_no_signal = "one two three four five six seven eight nine ten"
    assert explanation_completeness(long_no_signal) == 0.5
    long_with_because = "one two three four five six seven eight nine ten because the user did this."
    assert explanation_completeness(long_with_because) == 1.0


def test_compute_metrics_empty() -> None:
    assert compute_metrics([]) == {}


def test_compute_metrics_from_predictions() -> None:
    preds = [
        {"eval_id": "1", "task_type": "knowledge_qa", "reference": "An operator coordinates tasks.", "predicted": "An operator coordinates tasks."},
        {"eval_id": "2", "task_type": "knowledge_qa", "reference": "Data entry.", "predicted": "Something else."},
    ]
    m = compute_metrics(preds)
    assert "token_overlap" in m or "explanation_completeness" in m


@pytest.fixture
def test_jsonl(tmp_path: Path) -> Path:
    p = tmp_path / "test.jsonl"
    ex = {
        "eval_id": "1",
        "task_type": "knowledge_qa",
        "messages": [{"role": "user", "content": "What does an operations coordinator do?"}, {"role": "assistant", "content": "They coordinate operations."}],
        "reference": None,
    }
    with open(p, "w", encoding="utf-8") as f:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    return p


def test_run_eval_on_toy_fixtures(test_jsonl: Path, tmp_path: Path) -> None:
    def predict(ex: dict) -> str:
        for m in reversed(ex.get("messages", [])):
            if m.get("role") == "assistant":
                return m.get("content", "")
        return ""

    out_dir = tmp_path / "eval_out"
    result = run_eval(test_jsonl, predict, out_dir, run_id="test", model_id="dummy", retrieval_used=False)
    assert result.num_examples == 1
    assert Path(result.predictions_path).exists()
    assert (out_dir / "metrics.json").exists()
    assert (out_dir / "eval_summary.md").exists()


def test_run_eval_missing_file(tmp_path: Path) -> None:
    def predict(ex: dict) -> str:
        return ""

    result = run_eval(tmp_path / "nonexistent.jsonl", predict, tmp_path / "out", run_id="x", model_id="y", retrieval_used=False)
    assert result.num_examples == 0
    assert result.metrics == {}
