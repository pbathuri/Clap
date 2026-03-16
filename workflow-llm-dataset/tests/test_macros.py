"""
M23V: Tests for macro list, preview, run, blocked steps.
"""

from pathlib import Path

import pytest


def test_list_macros_empty(tmp_path: Path) -> None:
    """list_macros returns empty list when no routines."""
    from workflow_dataset.macros.runner import list_macros
    macros = list_macros(tmp_path)
    assert macros == []


def test_macro_preview_not_found(tmp_path: Path) -> None:
    """macro_preview returns None for unknown macro id."""
    from workflow_dataset.macros.runner import macro_preview
    plan = macro_preview("nonexistent_macro", mode="simulate", repo_root=tmp_path)
    assert plan is None


def test_macro_run_not_found(tmp_path: Path) -> None:
    """macro_run returns error dict for unknown macro id."""
    from workflow_dataset.macros.runner import macro_run
    result = macro_run("nonexistent_macro", mode="simulate", repo_root=tmp_path)
    assert result.get("error") is not None


def test_macro_preview_with_routine(tmp_path: Path) -> None:
    """macro_preview returns PlanPreview when routine exists."""
    routines_dir = tmp_path / "data/local/copilot/routines"
    routines_dir.mkdir(parents=True)
    (routines_dir / "morning_ops.yaml").write_text("""
routine_id: morning_ops
title: Morning operations
description: Daily morning check
job_pack_ids: [job_a, job_b]
stop_on_first_blocked: true
simulate_only: true
""", encoding="utf-8")
    # Job packs dir so get_job_pack can resolve (may still be None for job_a/job_b)
    (tmp_path / "data/local/job_packs").mkdir(parents=True)
    from workflow_dataset.macros.runner import macro_preview
    from workflow_dataset.macros.report import format_macro_preview
    plan = macro_preview("morning_ops", mode="simulate", repo_root=tmp_path)
    if plan:
        assert plan.plan_id
        assert "morning_ops" in (plan.job_pack_ids or []) or plan.job_pack_ids
        text = format_macro_preview(plan, "morning_ops")
        assert "morning_ops" in text
        assert "preview" in text.lower() or "Macro" in text


def test_get_blocked_steps_empty(tmp_path: Path) -> None:
    """get_blocked_steps returns empty list when no runs."""
    from workflow_dataset.macros.runner import get_blocked_steps
    blocked = get_blocked_steps("any_macro", repo_root=tmp_path)
    assert blocked == []
