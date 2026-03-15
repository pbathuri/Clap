"""Tests for workflow inference: workflow_steps.parquet from tasks and DWA evidence."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from workflow_dataset.infer.workflow import (
    WORKFLOW_STEP_COLUMNS,
    INFERENCE_METHOD,
    run_workflow_inference,
)


class _FakePaths:
    def __init__(self, processed: str):
        self.processed = processed


class _FakeSettings:
    def __init__(self, processed_dir: str):
        self.paths = _FakePaths(processed_dir)


def test_workflow_inference_produces_parquet_with_required_columns(tmp_path: Path) -> None:
    """With no task/DWA data, inference writes empty workflow_steps.parquet with correct schema."""
    settings = _FakeSettings(str(tmp_path))
    run_workflow_inference(settings)
    out = tmp_path / "workflow_steps.parquet"
    assert out.exists()
    df = pd.read_parquet(out)
    for col in WORKFLOW_STEP_COLUMNS:
        assert col in df.columns, f"missing column {col}"
    assert len(df) == 0


def test_workflow_inference_from_tasks_and_dwa(tmp_path: Path) -> None:
    """With tasks and DWA fixtures for 2 occupations, inference produces ordered steps per occupation."""
    tasks = pd.DataFrame([
        {"task_id": "t1", "occupation_id": "occ_a", "task_text": "First task for A", "source_id": "src1"},
        {"task_id": "t2", "occupation_id": "occ_a", "task_text": "Second task for A", "source_id": "src1"},
        {"task_id": "t3", "occupation_id": "occ_b", "task_text": "Only task for B", "source_id": "src1"},
    ])
    dwa = pd.DataFrame([
        {"dwa_id": "d1", "occupation_id": "occ_c", "dwa_title": "DWA for C only", "source_id": "src2"},
    ])
    tasks.to_parquet(tmp_path / "tasks.parquet", index=False)
    dwa.to_parquet(tmp_path / "detailed_work_activities.parquet", index=False)

    settings = _FakeSettings(str(tmp_path))
    run_workflow_inference(settings)

    out = tmp_path / "workflow_steps.parquet"
    assert out.exists()
    df = pd.read_parquet(out)
    for col in WORKFLOW_STEP_COLUMNS:
        assert col in df.columns, f"missing column {col}"

    # Occ A: 2 tasks → 2 steps; Occ B: 1 task → 1 step; Occ C: DWA only → 1 step
    by_occ = df.groupby("occupation_id")
    assert len(by_occ) >= 2
    occ_a = df[df["occupation_id"] == "occ_a"]
    occ_b = df[df["occupation_id"] == "occ_b"]
    occ_c = df[df["occupation_id"] == "occ_c"]
    assert len(occ_a) == 2
    assert len(occ_b) == 1
    assert len(occ_c) == 1

    assert list(occ_a["step_order"]) == [1, 2]
    assert list(occ_b["step_order"]) == [1]
    assert list(occ_c["step_order"]) == [1]

    assert (df["workflow_step_id"].str.len() > 0).all()
    assert (df["inference_method"] == INFERENCE_METHOD).all()

    assert "First task for A" in occ_a["step_description"].iloc[0]
    assert "DWA for C only" in occ_c["step_description"].iloc[0]


def test_workflow_inference_deterministic(tmp_path: Path) -> None:
    """Running inference twice yields identical workflow_step_id and step_order."""
    tasks = pd.DataFrame([
        {"task_id": "t1", "occupation_id": "occ_x", "task_text": "Task X", "source_id": "s1"},
    ])
    tasks.to_parquet(tmp_path / "tasks.parquet", index=False)
    settings = _FakeSettings(str(tmp_path))

    run_workflow_inference(settings)
    df1 = pd.read_parquet(tmp_path / "workflow_steps.parquet")

    run_workflow_inference(settings)
    df2 = pd.read_parquet(tmp_path / "workflow_steps.parquet")

    pd.testing.assert_frame_equal(df1.sort_values("workflow_step_id").reset_index(drop=True),
                                  df2.sort_values("workflow_step_id").reset_index(drop=True))
