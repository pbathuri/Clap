"""M24H.1: Pack-specific demo assets, golden first-value bundles, pack operator summary."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.value_packs.golden_bundles import (
    get_golden_bundle,
    list_golden_bundle_pack_ids,
    GoldenFirstValueBundle,
)
from workflow_dataset.value_packs.pack_operator_summary import (
    build_pack_operator_summary,
    format_pack_operator_summary,
)
from workflow_dataset.value_packs.first_run_flow import get_sample_asset_path
from workflow_dataset.value_packs.registry import get_value_pack


def test_list_golden_bundle_pack_ids():
    ids = list_golden_bundle_pack_ids()
    assert "founder_ops_plus" in ids
    assert "analyst_research_plus" in ids
    assert "developer_plus" in ids
    assert "document_worker_plus" in ids
    assert len(ids) == 4


def test_get_golden_bundle_founder():
    b = get_golden_bundle("founder_ops_plus")
    assert b is not None
    assert b.pack_id == "founder_ops_plus"
    assert b.bundle_id == "founder_ops_golden"
    assert b.example_macro_id == "morning_ops"
    assert b.example_job_id == "weekly_status_from_notes"
    assert len(b.steps) >= 4
    assert "founder_ops/morning_brief_notes.txt" in b.sample_input_refs or "morning_ops" in b.first_simulate_command


def test_get_golden_bundle_developer():
    b = get_golden_bundle("developer_plus")
    assert b is not None
    assert b.example_job_id == "replay_cli_demo"
    assert "replay_cli_demo" in b.first_simulate_command


def test_get_golden_bundle_unknown():
    assert get_golden_bundle("nonexistent") is None


def test_golden_bundle_steps_have_commands():
    b = get_golden_bundle("document_worker_plus")
    assert b is not None
    for s in b.steps:
        assert s.step_number >= 1
        assert s.title
        assert s.command


def test_build_pack_operator_summary_founder(tmp_path):
    summary = build_pack_operator_summary("founder_ops_plus", repo_root=tmp_path)
    assert summary.get("pack_id") == "founder_ops_plus"
    assert summary.get("pack_name")
    assert "first_value_steps" in summary
    assert "demo_assets" in summary
    assert "golden_bundle" in summary
    assert "next_step" in summary
    assert "expected_outputs" in summary
    assert "trust_notes" in summary


def test_build_pack_operator_summary_unknown(tmp_path):
    summary = build_pack_operator_summary("nonexistent", repo_root=tmp_path)
    assert summary.get("error")
    assert summary.get("first_value_steps") == []


def test_format_pack_operator_summary(tmp_path):
    summary = build_pack_operator_summary("analyst_research_plus", repo_root=tmp_path)
    text = format_pack_operator_summary(summary)
    assert "Pack operator summary" in text
    assert "analyst_research_plus" in text
    assert "First-value steps" in text or "Demo assets" in text
    assert "Golden bundle" in text or "next step" in text


def test_pack_sample_asset_paths_include_pack_specific():
    pack = get_value_pack("founder_ops_plus")
    assert pack is not None
    assert any("founder_ops" in p for p in (pack.sample_asset_paths or []))
    pack = get_value_pack("developer_plus")
    assert pack is not None
    assert any("developer" in p for p in (pack.sample_asset_paths or []))


def test_get_sample_asset_path_resolves_subdir(tmp_path):
    # Create pack-specific sample subdir and file
    samples_dir = tmp_path / "data/local/value_packs/samples/founder_ops"
    samples_dir.mkdir(parents=True)
    (samples_dir / "morning_brief_notes.txt").write_text("demo")
    path = get_sample_asset_path("founder_ops/morning_brief_notes.txt", repo_root=tmp_path)
    assert path is not None
    assert path.exists()
    assert path.read_text() == "demo"
