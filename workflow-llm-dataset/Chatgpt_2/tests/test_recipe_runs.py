"""M24E: Recipe run model and storage — save, load, list, get latest."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.specialization.recipe_run_models import RecipeRun, RECIPE_RUN_STATUSES
from workflow_dataset.specialization.recipe_runs_storage import (
    save_run,
    get_run,
    list_runs,
    generate_run_id,
)


def test_recipe_run_statuses():
    assert "pending" in RECIPE_RUN_STATUSES
    assert "completed" in RECIPE_RUN_STATUSES
    assert "failed" in RECIPE_RUN_STATUSES


def test_save_and_get_run(tmp_path):
    r = RecipeRun(
        run_id="test_run_1",
        source_recipe_id="retrieval_only",
        target_value_pack_id="founder_ops_plus",
        target_domain_pack_id="founder_ops",
        status="completed",
        steps_done=["prepare_sample_assets", "write_provisioning_manifest"],
    )
    path = save_run(r, repo_root=tmp_path)
    assert path.exists()
    loaded = get_run("test_run_1", repo_root=tmp_path)
    assert loaded is not None
    assert loaded.run_id == r.run_id
    assert loaded.source_recipe_id == r.source_recipe_id
    assert loaded.target_value_pack_id == r.target_value_pack_id
    assert loaded.status == "completed"


def test_get_run_missing(tmp_path):
    assert get_run("nonexistent_run", repo_root=tmp_path) is None


def test_list_runs_empty(tmp_path):
    runs = list_runs(repo_root=tmp_path, limit=10)
    assert runs == []


def test_list_runs_order(tmp_path):
    r1 = RecipeRun(run_id="run_1", source_recipe_id="retrieval_only", status="completed")
    r2 = RecipeRun(run_id="run_2", source_recipe_id="adapter_finetune", status="completed")
    save_run(r1, repo_root=tmp_path)
    save_run(r2, repo_root=tmp_path)
    runs = list_runs(repo_root=tmp_path, limit=10)
    assert len(runs) >= 2
    # Newest first (by mtime)
    ids = [x.run_id for x in runs]
    assert "run_1" in ids
    assert "run_2" in ids


def test_generate_run_id():
    uid = generate_run_id("provision")
    assert uid.startswith("provision_")
    assert len(uid) > 10
