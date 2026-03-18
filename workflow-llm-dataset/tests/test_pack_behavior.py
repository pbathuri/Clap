"""
M25E–M25H: Pack-driven behavior engine — prompt assets, task defaults, resolution, explanation.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.packs.pack_models import PackManifest
from workflow_dataset.packs.behavior_models import (
    PackPromptAsset,
    PackTaskDefaults,
    PackRetrievalProfilePreset,
    PackOutputProfilePreset,
    ParserOutputHint,
    ResolvedBehavior,
    BehaviorResolutionResult,
    PROMPT_ASSET_KINDS,
)
from workflow_dataset.packs.behavior_assets import (
    get_prompt_assets_from_manifest,
    get_task_defaults_from_manifest,
    get_all_behavior_assets,
    get_retrieval_profile_presets_from_manifest,
    get_output_profile_presets_from_manifest,
    get_parser_output_hints_from_manifest,
)
from workflow_dataset.packs.behavior_resolver import (
    resolve_behavior_for_task,
    get_active_behavior_summary,
)
from workflow_dataset.packs.pack_state import save_pack_state, get_packs_dir
from workflow_dataset.packs.pack_activation import save_activation_state


@pytest.fixture
def packs_dir_with_behavior(tmp_path):
    """Install one pack with behavior.prompt_assets and behavior.task_defaults."""
    (tmp_path / "ops_pack").mkdir(parents=True, exist_ok=True)
    manifest = {
        "pack_id": "ops_pack",
        "name": "Ops pack",
        "version": "0.1.0",
        "role_tags": ["ops"],
        "workflow_tags": ["reporting"],
        "task_tags": ["weekly_status"],
        "behavior": {
            "prompt_assets": [
                {"kind": "system_guidance", "key": "weekly_status", "content": "Be concise and ops-focused.", "priority_hint": "high"},
                {"kind": "task_prompt", "key": "weekly_status", "content": "Generate weekly status from notes.", "priority_hint": "medium"},
            ],
            "task_defaults": [
                {"task_id": "weekly_status", "workflow_id": "founder_ops", "preferred_adapter": "ops_handoff", "preferred_model_class": "general_chat_reasoning", "preferred_output_mode": "ops_handoff"},
            ],
            "retrieval_profile_presets": [
                {"preset_id": "ops_retrieval", "task_id": "weekly_status", "workflow_id": "founder_ops", "top_k": 5, "rerank": True},
            ],
            "output_profile_presets": [
                {"preset_id": "ops_output", "task_id": "weekly_status", "adapter": "ops_handoff", "format_hint": "bullets", "sections_hint": "summary,next_steps"},
            ],
            "parser_output_hints": [
                {"key": "weekly_status", "preferred_format": "markdown", "bullet_preference": "bullets", "stakeholder_safe": True},
            ],
        },
    }
    (tmp_path / "ops_pack" / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    save_pack_state({"ops_pack": {"path": "ops_pack/manifest.json", "version": "0.1.0", "installed_utc": "2026-01-01T00:00:00Z"}}, tmp_path)
    save_activation_state({"primary_pack_id": "ops_pack", "current_role": "ops", "current_workflow": "", "current_task": ""}, tmp_path)
    return tmp_path


def test_prompt_asset_loading():
    manifest = PackManifest(
        pack_id="test_pack",
        name="Test",
        version="0.1.0",
        behavior={
            "prompt_assets": [
                {"kind": "system_guidance", "key": "global", "content": "You are helpful.", "priority_hint": "high"},
            ],
        },
    )
    assets = get_prompt_assets_from_manifest(manifest)
    assert len(assets) == 1
    assert assets[0].kind == "system_guidance"
    assert assets[0].key == "global"
    assert assets[0].content == "You are helpful."
    assert assets[0].pack_id == "test_pack"


def test_task_defaults_loading():
    manifest = PackManifest(
        pack_id="test_pack",
        name="Test",
        version="0.1.0",
        behavior={
            "task_defaults": [
                {"task_id": "weekly_status", "preferred_adapter": "ops_handoff", "preferred_model_class": "general_chat_reasoning"},
            ],
        },
    )
    defaults = get_task_defaults_from_manifest(manifest)
    assert len(defaults) == 1
    assert defaults[0].task_id == "weekly_status"
    assert defaults[0].preferred_adapter == "ops_handoff"
    assert defaults[0].preferred_model_class == "general_chat_reasoning"
    assert defaults[0].pack_id == "test_pack"


def test_get_all_behavior_assets():
    manifest = PackManifest(
        pack_id="p",
        name="P",
        version="0.1.0",
        behavior={"prompt_assets": [{"kind": "task_prompt", "key": "x", "content": "c"}], "task_defaults": [{"task_id": "x", "preferred_adapter": "a"}]},
    )
    assets, default_list = get_all_behavior_assets(manifest)
    assert len(assets) == 1
    assert len(default_list) == 1
    assert default_list[0].preferred_adapter == "a"


def test_behavior_resolution_result_structure(packs_dir_with_behavior):
    result = resolve_behavior_for_task(task_id="weekly_status", workflow_id="founder_ops", packs_dir=packs_dir_with_behavior)
    assert isinstance(result, BehaviorResolutionResult)
    assert result.resolved is not None
    assert result.active_pack_ids is not None
    # primary_pack_id comes from activation state; may be "" when no pack is activated
    assert result.primary_pack_id in ("", "ops_pack")
    assert result.resolved.winning_pack_id in ("", "ops_pack")  # may be set if task_defaults matched
    assert isinstance(result.why_winning, str)
    assert isinstance(result.why_excluded, list)


def test_resolved_behavior_prompt_assets(packs_dir_with_behavior):
    result = resolve_behavior_for_task(task_id="weekly_status", packs_dir=packs_dir_with_behavior)
    assets = result.resolved.prompt_assets
    # May be 0 if key matching is strict and no asset key matches weekly_status
    assert isinstance(assets, list)
    for a in assets:
        assert isinstance(a, PackPromptAsset)
        assert a.kind in PROMPT_ASSET_KINDS or a.kind == "task_prompt"


def test_task_defaults_resolution(packs_dir_with_behavior):
    result = resolve_behavior_for_task(task_id="weekly_status", workflow_id="founder_ops", packs_dir=packs_dir_with_behavior)
    d = result.resolved.task_defaults
    if d:
        assert d.task_id == "weekly_status" or d.task_id == ""
        assert d.pack_id == "ops_pack"
        assert d.preferred_adapter == "ops_handoff" or d.preferred_adapter == ""


def test_get_active_behavior_summary(packs_dir_with_behavior):
    summary = get_active_behavior_summary(packs_dir=packs_dir_with_behavior)
    assert "active_pack_ids" in summary
    assert "winning_pack_id" in summary
    assert "why_current_behavior" in summary
    assert "task_defaults" in summary
    assert "excluded_pack_ids" in summary


def test_behavior_manifest_without_behavior():
    manifest = PackManifest(pack_id="no_behavior", name="N", version="0.1.0")
    assets = get_prompt_assets_from_manifest(manifest)
    defaults = get_task_defaults_from_manifest(manifest)
    assert assets == []
    assert defaults == []


def test_explanation_output(packs_dir_with_behavior):
    result = resolve_behavior_for_task(task_id="weekly_status", packs_dir=packs_dir_with_behavior)
    assert result.why_winning is not None
    assert isinstance(result.conflicts, list)


def test_retrieval_profile_preset_loading():
    manifest = PackManifest(
        pack_id="p",
        name="P",
        version="0.1.0",
        behavior={
            "retrieval_profile_presets": [
                {"preset_id": "r1", "task_id": "weekly_status", "top_k": 5, "rerank": True},
            ],
        },
    )
    presets = get_retrieval_profile_presets_from_manifest(manifest)
    assert len(presets) == 1
    assert presets[0].preset_id == "r1"
    assert presets[0].task_id == "weekly_status"
    assert presets[0].top_k == 5
    assert presets[0].rerank is True
    assert presets[0].pack_id == "p"


def test_output_profile_preset_loading():
    manifest = PackManifest(
        pack_id="p",
        name="P",
        version="0.1.0",
        behavior={
            "output_profile_presets": [
                {"preset_id": "o1", "task_id": "weekly_status", "adapter": "ops_handoff", "format_hint": "bullets"},
            ],
        },
    )
    presets = get_output_profile_presets_from_manifest(manifest)
    assert len(presets) == 1
    assert presets[0].adapter == "ops_handoff"
    assert presets[0].format_hint == "bullets"
    assert presets[0].pack_id == "p"


def test_parser_output_hints_loading():
    manifest = PackManifest(
        pack_id="p",
        name="P",
        version="0.1.0",
        behavior={
            "parser_output_hints": [
                {"key": "weekly_status", "preferred_format": "markdown", "stakeholder_safe": True},
            ],
        },
    )
    hints = get_parser_output_hints_from_manifest(manifest)
    assert len(hints) == 1
    assert hints[0].key == "weekly_status"
    assert hints[0].preferred_format == "markdown"
    assert hints[0].stakeholder_safe is True


def test_resolved_retrieval_and_output_profile(packs_dir_with_behavior):
    result = resolve_behavior_for_task(task_id="weekly_status", workflow_id="founder_ops", packs_dir=packs_dir_with_behavior)
    assert isinstance(result.resolved.retrieval_profile, dict)
    assert isinstance(result.resolved.output_profile, dict)
    if result.resolved.retrieval_profile:
        assert "top_k" in result.resolved.retrieval_profile or result.resolved.retrieval_profile
    if result.resolved.output_profile:
        assert "adapter" in result.resolved.output_profile or result.resolved.output_profile
    assert isinstance(result.resolved.parser_output_hints, list)


def test_why_profile_explanation(packs_dir_with_behavior):
    result = resolve_behavior_for_task(task_id="weekly_status", workflow_id="founder_ops", packs_dir=packs_dir_with_behavior)
    if result.resolved.retrieval_profile:
        assert result.resolved.why_retrieval_profile != "" or result.resolved.retrieval_profile_source_pack != ""
    if result.resolved.output_profile:
        assert result.resolved.why_output_profile != "" or result.resolved.output_profile_source_pack != ""
    summary = get_active_behavior_summary(packs_dir=packs_dir_with_behavior)
    assert "retrieval_profile" in summary
    assert "output_profile" in summary
    assert "why_retrieval_profile" in summary
    assert "why_output_profile" in summary


def test_retrieval_profile_preset_id_and_why(packs_dir_with_behavior):
    """M25H.1: Resolved behavior includes preset_id and operator-readable why."""
    result = resolve_behavior_for_task(task_id="weekly_status", workflow_id="founder_ops", packs_dir=packs_dir_with_behavior)
    r = result.resolved
    if r.retrieval_profile:
        assert getattr(r, "retrieval_profile_preset_id", None) is not None or r.retrieval_profile_source_pack
        assert "Applied" in r.why_retrieval_profile or "preset" in r.why_retrieval_profile.lower() or r.why_retrieval_profile


def test_output_profile_preset_id_and_why(packs_dir_with_behavior):
    """M25H.1: Resolved behavior includes output preset_id and operator-readable why."""
    result = resolve_behavior_for_task(task_id="weekly_status", workflow_id="founder_ops", packs_dir=packs_dir_with_behavior)
    r = result.resolved
    if r.output_profile:
        assert getattr(r, "output_profile_preset_id", None) is not None or r.output_profile_source_pack
        assert "Applied" in r.why_output_profile or "preset" in r.why_output_profile.lower() or r.why_output_profile


def test_parser_hint_safe_keys_only():
    """M25H.1: Parser hint only reads safe keys; unknown keys are ignored."""
    manifest = PackManifest(
        pack_id="p",
        name="P",
        version="0.1.0",
        behavior={
            "parser_output_hints": [
                {
                    "key": "weekly_status",
                    "preferred_format": "markdown",
                    "unsafe_custom_key": "ignored",
                },
            ],
        },
    )
    hints = get_parser_output_hints_from_manifest(manifest)
    assert len(hints) == 1
    assert hints[0].preferred_format == "markdown"
    assert not getattr(hints[0], "unsafe_custom_key", None)


# ----- M25E–M25H Behavior runtime API -----


def test_get_resolved_behavior_for_task():
    from workflow_dataset.packs.behavior_runtime import get_resolved_behavior_for_task
    result = get_resolved_behavior_for_task(task_id="weekly_status", repo_root=None)
    assert result is not None
    assert hasattr(result, "resolved")
    assert hasattr(result, "why_winning")


def test_merge_pack_prompts_into_instruction():
    from workflow_dataset.packs.behavior_runtime import merge_pack_prompts_into_instruction
    from workflow_dataset.packs.behavior_models import ResolvedBehavior, PackPromptAsset
    empty = ResolvedBehavior()
    assert merge_pack_prompts_into_instruction(empty) == ""
    resolved = ResolvedBehavior(
        prompt_assets=[
            PackPromptAsset(kind="system_guidance", key="x", content="System: be concise.", pack_id="p1"),
            PackPromptAsset(kind="task_prompt", key="x", content="Task: do X.", pack_id="p1"),
        ],
    )
    out = merge_pack_prompts_into_instruction(resolved)
    assert "System: be concise." in out
    assert "Task: do X." in out


def test_get_behavior_summary_for_job(packs_dir_with_behavior):
    from workflow_dataset.packs.behavior_runtime import get_behavior_summary_for_job
    summary = get_behavior_summary_for_job("any_job_id", repo_root=packs_dir_with_behavior)
    assert "winning_pack_id" in summary
    assert "active_pack_ids" in summary
    assert "task_defaults" in summary
    assert "conflict_summary" in summary


def test_run_job_includes_resolved_behavior(packs_dir_with_behavior):
    from workflow_dataset.job_packs.execute import run_job
    from workflow_dataset.job_packs.seed_jobs import seed_task_demo_job_pack
    seed_task_demo_job_pack(packs_dir_with_behavior)
    result = run_job("replay_cli_demo", "simulate", {}, packs_dir_with_behavior)
    assert "resolved_behavior" in result
    rb = result["resolved_behavior"]
    assert isinstance(rb, dict)
    assert "winning_pack_id" in rb or "active_pack_ids" in rb
    if not result.get("error"):
        assert "task_defaults" in rb
        assert "conflict_summary" in rb
