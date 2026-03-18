"""
M23P: Tests for macro composer — schema, step classification, checkpointed run, pause/resume, blocked steps.
"""

from pathlib import Path

import pytest


def test_macro_schema_step_types() -> None:
    """MacroStep and step type constants exist."""
    from workflow_dataset.macros.schema import (
        MacroStep,
        STEP_TYPE_SAFE_INSPECT,
        STEP_TYPE_BLOCKED,
        STEP_TYPE_TRUSTED_REAL,
        STEP_TYPE_SANDBOX_WRITE,
    )
    step = MacroStep(job_pack_id="j1", step_type=STEP_TYPE_SAFE_INSPECT)
    assert step.job_pack_id == "j1"
    assert step.step_type == STEP_TYPE_SAFE_INSPECT
    assert STEP_TYPE_BLOCKED != STEP_TYPE_TRUSTED_REAL
    assert STEP_TYPE_SANDBOX_WRITE


def test_macro_schema_checkpoint_fields() -> None:
    """Macro has checkpoint_after_step_indices and stop_conditions."""
    from workflow_dataset.macros.schema import Macro
    m = Macro(
        macro_id="m1",
        title="T",
        description="D",
        checkpoint_after_step_indices=[1],
        stop_conditions=["user cancelled"],
        expected_outputs=["out1"],
    )
    assert m.checkpoint_after_step_indices == [1]
    assert "user cancelled" in m.stop_conditions
    assert m.expected_outputs == ["out1"]


def test_classify_step_missing_job(tmp_path: Path) -> None:
    """classify_step returns blocked for missing job pack."""
    from workflow_dataset.macros.step_classifier import classify_step, STEP_TYPE_BLOCKED
    step = classify_step("no_such_job", "simulate", tmp_path)
    assert step.step_type == STEP_TYPE_BLOCKED
    assert step.job_pack_id == "no_such_job"


def test_explain_step_categories() -> None:
    """explain_step_categories returns non-empty string."""
    from workflow_dataset.macros.step_classifier import explain_step_categories
    text = explain_step_categories()
    assert "safe_inspect" in text
    assert "blocked" in text


def test_run_state_save_load(tmp_path: Path) -> None:
    """save_run_state and load_run_state round-trip."""
    from workflow_dataset.macros.run_state import save_run_state, load_run_state
    import os
    os.chdir(tmp_path)
    (tmp_path / "data/local/copilot/runs").mkdir(parents=True)
    save_run_state(
        "run1", "macro1", "awaiting_approval", "plan1", ["j1", "j2"], "simulate",
        1, [{"job_pack_id": "j1"}], [], str(tmp_path / "data/local/copilot/runs/run1"),
        repo_root=tmp_path,
        approval_required_before_step=1,
        errors=["e1"],
    )
    state = load_run_state("run1", tmp_path)
    assert state is not None
    assert state["run_id"] == "run1"
    assert state["macro_id"] == "macro1"
    assert state["status"] == "awaiting_approval"
    assert state["current_step_index"] == 1
    assert state["errors"] == ["e1"]


def test_list_paused_and_awaiting_empty(tmp_path: Path) -> None:
    """list_paused_runs and list_awaiting_approval_runs return empty when no runs."""
    from workflow_dataset.macros.run_state import list_paused_runs, list_awaiting_approval_runs
    assert list_paused_runs(tmp_path) == []
    assert list_awaiting_approval_runs(tmp_path) == []


def test_get_macro_steps_empty(tmp_path: Path) -> None:
    """get_macro_steps returns [] for unknown routine."""
    from workflow_dataset.macros.runner import get_macro_steps
    steps = get_macro_steps("nonexistent", mode="simulate", repo_root=tmp_path)
    assert steps == []


def test_get_macro_steps_with_routine(tmp_path: Path) -> None:
    """get_macro_steps returns classified steps when routine exists."""
    pytest.importorskip("yaml")
    from workflow_dataset.copilot.config import get_routines_dir
    routines_dir = get_routines_dir(tmp_path)
    routines_dir.mkdir(parents=True, exist_ok=True)
    (routines_dir / "morning_ops.yaml").write_text(
        "routine_id: morning_ops\ntitle: Morning operations\ndescription: Daily morning check\n"
        "job_pack_ids: [job_a, job_b]\nstop_on_first_blocked: true\nsimulate_only: true\n",
        encoding="utf-8",
    )
    (tmp_path / "data/local/job_packs").mkdir(parents=True, exist_ok=True)
    from workflow_dataset.macros.runner import get_macro_steps
    steps = get_macro_steps("morning_ops", mode="simulate", repo_root=tmp_path)
    assert len(steps) == 2
    assert steps[0].job_pack_id == "job_a"
    assert steps[1].job_pack_id == "job_b"
    assert steps[0].step_type in ("blocked", "safe_inspect", "sandbox_write")


def test_resume_macro_run_not_found(tmp_path: Path) -> None:
    """resume_macro_run returns error for unknown run_id."""
    from workflow_dataset.macros.runner import resume_macro_run
    result = resume_macro_run("nonexistent_run_id", repo_root=tmp_path)
    assert result.get("error") is not None


def test_macro_run_simulate_no_stop_at_checkpoints(tmp_path: Path) -> None:
    """macro_run with simulate and no stop_at_checkpoints runs via run_plan (no macro_run_status)."""
    pytest.importorskip("yaml")
    from workflow_dataset.copilot.config import get_routines_dir, get_runs_dir
    routines_dir = get_routines_dir(tmp_path)
    routines_dir.mkdir(parents=True, exist_ok=True)
    (routines_dir / "morning_ops.yaml").write_text(
        "routine_id: morning_ops\ntitle: Morning operations\njob_pack_ids: [job_a, job_b]\n"
        "stop_on_first_blocked: true\nsimulate_only: true\n",
        encoding="utf-8",
    )
    get_runs_dir(tmp_path).mkdir(parents=True, exist_ok=True)
    (tmp_path / "data/local/job_packs").mkdir(parents=True, exist_ok=True)
    from workflow_dataset.macros.runner import macro_run
    result = macro_run("morning_ops", mode="simulate", repo_root=tmp_path, stop_at_checkpoints=False)
    assert result.get("error") is None
    assert result.get("plan_run_id") is not None
    assert result.get("executed_count") is not None


def test_macro_run_stop_at_checkpoints_completes_when_no_next_trusted(tmp_path: Path) -> None:
    """With stop_at_checkpoints, simulate run with empty job list completes (status=completed)."""
    pytest.importorskip("yaml")
    from workflow_dataset.copilot.config import get_routines_dir, get_runs_dir
    routines_dir = get_routines_dir(tmp_path)
    routines_dir.mkdir(parents=True, exist_ok=True)
    (routines_dir / "empty_routine.yaml").write_text(
        "routine_id: empty_routine\ntitle: Empty\njob_pack_ids: []\n"
        "stop_on_first_blocked: true\nsimulate_only: true\n",
        encoding="utf-8",
    )
    get_runs_dir(tmp_path).mkdir(parents=True, exist_ok=True)
    (tmp_path / "data/local/job_packs").mkdir(parents=True, exist_ok=True)
    from workflow_dataset.macros.runner import macro_run
    result = macro_run("empty_routine", mode="simulate", repo_root=tmp_path, stop_at_checkpoints=True)
    assert result.get("error") is None
    assert result.get("macro_run_status") == "completed"
    assert result.get("executed_count") == 0
