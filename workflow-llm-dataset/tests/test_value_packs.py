"""M24B: Value packs — registry, recommendation, first-run flow, compare, missing prereqs, sample assets."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.value_packs.registry import list_value_packs, get_value_pack
from workflow_dataset.value_packs.recommend import recommend_value_pack
from workflow_dataset.value_packs.compare import compare_value_packs
from workflow_dataset.value_packs.first_run_flow import build_first_run_flow, get_sample_asset_path
from workflow_dataset.value_packs.report import (
    format_pack_show,
    format_recommendation,
    format_first_run_flow,
    format_compare,
)


def test_list_value_packs():
    ids = list_value_packs()
    assert isinstance(ids, list)
    assert "founder_ops_plus" in ids
    assert "analyst_research_plus" in ids
    assert "developer_plus" in ids
    assert len(ids) >= 5


def test_get_value_pack():
    p = get_value_pack("founder_ops_plus")
    assert p is not None
    assert p.pack_id == "founder_ops_plus"
    assert p.target_field == "operations"
    assert get_value_pack("nonexistent") is None


def test_recommend_value_pack(tmp_path):
    result = recommend_value_pack(profile=None, repo_root=tmp_path)
    assert "pack" in result
    assert "score" in result
    assert "reason" in result
    assert "missing_prerequisites" in result
    assert "simulate_only_summary" in result


def test_recommend_value_pack_with_profile(tmp_path):
    result = recommend_value_pack(profile={"field": "research", "job_family": "analyst"}, repo_root=tmp_path)
    assert result.get("pack") is not None
    assert "alternatives" in result


def test_build_first_run_flow(tmp_path):
    result = build_first_run_flow("founder_ops_plus", repo_root=tmp_path)
    assert "steps" in result
    assert "pack_id" in result
    assert len(result["steps"]) >= 4
    assert result["steps"][0]["title"]
    assert result["steps"][0]["command"]


def test_build_first_run_flow_unknown(tmp_path):
    result = build_first_run_flow("unknown_pack", repo_root=tmp_path)
    assert result.get("error")
    assert result.get("steps") == []


def test_compare_value_packs(tmp_path):
    result = compare_value_packs("founder_ops_plus", "developer_plus", repo_root=tmp_path)
    assert "pack_a" in result
    assert "pack_b" in result
    assert result["pack_a"].pack_id == "founder_ops_plus"
    assert result["pack_b"].pack_id == "developer_plus"
    assert "missing_prerequisites_a" in result
    assert "overlap_jobs" in result
    assert "which_fits_better" in result


def test_compare_value_packs_missing():
    result = compare_value_packs("founder_ops_plus", "nonexistent", profile=None, repo_root=None)
    assert result.get("error") and "nonexistent" in result["error"]
    assert result.get("pack_b") is None


def test_missing_prerequisites_in_recommendation(tmp_path):
    result = recommend_value_pack(profile={"field": "operations"}, repo_root=tmp_path)
    assert "missing_prerequisites" in result
    # May be empty or list of missing jobs/routines/approval
    assert isinstance(result["missing_prerequisites"], list)


def test_format_pack_show():
    p = get_value_pack("analyst_research_plus")
    text = format_pack_show(p)
    assert "analyst_research_plus" in text
    assert "First-value" in text or "first-value" in text.lower()


def test_format_recommendation(tmp_path):
    result = recommend_value_pack(repo_root=tmp_path)
    text = format_recommendation(result)
    assert "Value pack recommendation" in text
    assert "Recommended:" in text


def test_format_first_run_flow(tmp_path):
    result = build_first_run_flow("developer_plus", tmp_path)
    text = format_first_run_flow(result)
    assert "First-value flow" in text or "developer_plus" in text
    assert "Command:" in text or "command" in text.lower()


def test_format_compare(tmp_path):
    result = compare_value_packs("founder_ops_plus", "document_worker_plus", repo_root=tmp_path)
    text = format_compare(result)
    assert "comparison" in text.lower()
    assert "founder_ops_plus" in text or "document_worker_plus" in text


def test_get_sample_asset_path(tmp_path):
    # Without samples dir, returns None
    p = get_sample_asset_path("example_notes.txt", repo_root=tmp_path)
    assert p is None or (p and p.exists())


def test_get_sample_asset_path_with_samples_dir(tmp_path):
    # Create samples dir and file
    samples_dir = tmp_path / "data" / "local" / "value_packs" / "samples"
    samples_dir.mkdir(parents=True)
    (samples_dir / "example_notes.txt").write_text("sample")
    p = get_sample_asset_path("example_notes.txt", repo_root=tmp_path)
    assert p is not None
    assert p.exists()
    assert p.read_text() == "sample"
    assert get_sample_asset_path("nonexistent.txt", repo_root=tmp_path) is None
