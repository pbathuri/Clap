"""
Tests for M17 workflow trials: schema, registry, runner (mocked), scoring, report.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.trials.trial_models import (
    WorkflowTrial,
    WorkflowTrialResult,
    WorkflowTrialBundle,
    TrialMode,
)
from workflow_dataset.trials.trial_registry import (
    register_trial,
    get_trial,
    list_trials,
    clear_registry,
)
from workflow_dataset.trials.trial_scoring import score_result
from workflow_dataset.trials.trial_report import load_trial_results, write_trial_report


def test_workflow_trial_model() -> None:
    t = WorkflowTrial(
        trial_id="test_ops",
        scenario_id="ops",
        domain="ops",
        workflow_type="summarize",
        task_goal="Summarize reporting workflow",
    )
    assert t.trial_id == "test_ops"
    assert t.domain == "ops"


def test_trial_mode_enum() -> None:
    assert TrialMode.BASELINE.value == "baseline"
    assert TrialMode.ADAPTER_RETRIEVAL.value == "adapter_retrieval"


def test_register_and_get_trial() -> None:
    clear_registry()
    t = WorkflowTrial(trial_id="t1", domain="ops", task_goal="Goal")
    register_trial(t)
    assert get_trial("t1") is not None
    assert get_trial("t1").domain == "ops"
    assert get_trial("missing") is None


def test_list_trials_filter_domain() -> None:
    clear_registry()
    register_trial(WorkflowTrial(trial_id="a1", domain="ops", task_goal="A"))
    register_trial(WorkflowTrial(trial_id="b1", domain="spreadsheet", task_goal="B"))
    all_t = list_trials()
    assert len(all_t) == 2
    ops_t = list_trials(domain="ops")
    assert len(ops_t) == 1
    assert ops_t[0].trial_id == "a1"


def test_score_result_baseline_error() -> None:
    t = WorkflowTrial(trial_id="x", domain="ops", task_goal="G")
    scores = score_result(t, TrialMode.BASELINE, "[inference error: fail]", {}, False)
    assert scores["task_completion"] == 0.0
    assert scores["safety"] == 1.0


def test_score_result_substantive_response() -> None:
    t = WorkflowTrial(trial_id="x", domain="ops", task_goal="G")
    long_ok = "This is a long response that suggests a workflow structure based on the user's style and prior patterns."
    scores = score_result(t, TrialMode.ADAPTER, long_ok, {}, False)
    assert scores["task_completion"] > 0.5
    assert scores["style_match"] > 0.0


def test_load_trial_results_empty_dir(tmp_path: Path) -> None:
    assert load_trial_results(tmp_path) == []


def test_write_trial_report(tmp_path: Path) -> None:
    results = [
        WorkflowTrialResult(
            result_id="res_1",
            trial_id="ops_1",
            model_mode="adapter",
            retrieval_used=False,
            adapter_used=True,
            task_completion_score=0.7,
            style_match_score=0.5,
            completion_status="completed",
        ),
        WorkflowTrialResult(
            result_id="res_2",
            trial_id="ops_1",
            model_mode="adapter_retrieval",
            retrieval_used=True,
            adapter_used=True,
            task_completion_score=0.8,
            style_match_score=0.6,
            completion_status="completed",
        ),
    ]
    report_path = tmp_path / "report.md"
    write_trial_report(results, report_path)
    assert report_path.exists()
    text = report_path.read_text()
    assert "ops_1" in text
    assert "adapter" in text
    assert "0.70" in text or "0.7" in text


def test_trial_runner_baseline_no_llm(tmp_path: Path) -> None:
    """Run trial in baseline mode does not require LLM config."""
    from workflow_dataset.trials.trial_runner import run_trial
    clear_registry()
    t = WorkflowTrial(
        trial_id="baseline_test",
        scenario_id="ops",
        domain="ops",
        task_goal="Summarize workflow",
        prompt_template="Task: {task_goal}\n\nContext:\n{context}",
    )
    register_trial(t)
    result = run_trial(
        t,
        TrialMode.BASELINE,
        context_bundle={"project_context": {"projects": [{"label": "p1"}]}},
        output_dir=tmp_path,
    )
    assert result.model_mode == "baseline"
    assert result.completion_status == "completed"
    assert "[Baseline]" in result.model_response
    assert (tmp_path / f"{result.result_id}.json").exists()
