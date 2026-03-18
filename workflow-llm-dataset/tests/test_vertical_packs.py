"""
M39E–M39H: Tests for curated vertical packs, guided paths, defaults, milestone progress.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from workflow_dataset.vertical_packs.models import (
    CuratedVerticalPack,
    FirstValuePath,
    FirstValuePathStep,
    SuccessMilestone,
    TrustReviewPosture,
    RequiredSurfaces,
)
from workflow_dataset.vertical_packs.registry import (
    get_curated_pack,
    list_curated_pack_ids,
    get_curated_pack_for_value_pack,
    BUILTIN_CURATED_PACKS,
)
from workflow_dataset.vertical_packs.paths import build_path_for_pack
from workflow_dataset.vertical_packs.store import (
    get_vertical_packs_dir,
    get_active_pack,
    set_active_pack,
    clear_active_pack,
    get_path_progress,
    set_path_progress,
    set_milestone_reached,
)
from workflow_dataset.vertical_packs.defaults import apply_vertical_defaults
from workflow_dataset.vertical_packs.progress import (
    get_next_vertical_milestone,
    get_blocked_vertical_onboarding_step,
    build_milestone_progress_output,
)
from workflow_dataset.vertical_packs.playbooks import (
    get_playbook_for_vertical,
    get_recovery_path_for_failure,
    get_operator_guidance_when_stalled,
    list_vertical_playbook_ids,
    BUILTIN_VERTICAL_PLAYBOOKS,
)


def test_curated_pack_model() -> None:
    pack = get_curated_pack("founder_operator_core")
    assert pack is not None
    assert pack.pack_id == "founder_operator_core"
    assert pack.value_pack_id == "founder_ops_plus"
    assert pack.workday_preset_id == "founder_operator"
    assert pack.trust_review_posture.trust_preset_id == "supervised_operator"
    assert pack.first_value_path is not None
    assert pack.first_value_path.path_id == "founder_ops_plus_first_value"
    d = pack.to_dict()
    assert d["pack_id"] == "founder_operator_core"
    assert "first_value_path" in d
    assert "trust_review_posture" in d


def test_guided_path_generation() -> None:
    path = build_path_for_pack("founder_ops_plus")
    assert path is not None
    assert path.entry_point
    assert len(path.steps) >= 4
    assert path.first_value_milestone_id == "first_simulate_done"
    assert len(path.common_failure_points) >= 1
    path2 = build_path_for_pack("analyst_research_plus")
    assert path2 is not None
    assert path2.pack_id == "analyst_research_plus"


def test_vertical_defaults_apply() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        result = apply_vertical_defaults("founder_operator_core", repo_root=root, dry_run=True, persist_active=False)
        assert "error" not in result
        assert result.get("pack_id") == "founder_operator_core"
        assert result.get("value_pack_id") == "founder_ops_plus"
        assert result.get("trust_preset_id") == "supervised_operator"
        assert "applied_commands" in result
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        result = apply_vertical_defaults("founder_operator_core", repo_root=root, dry_run=False, persist_active=True)
        assert result.get("applied") is True
        active = get_active_pack(repo_root=root)
        assert active.get("active_curated_pack_id") == "founder_operator_core"


def test_first_value_milestone_tracking() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        set_active_pack("founder_operator_core", repo_root=root)
        set_path_progress(
            "founder_operator_core",
            "founder_ops_plus_first_value",
            ["first_run_completed", "runtime_check_done"],
            next_milestone_id="onboard_approvals_done",
            repo_root=root,
        )
        out = get_next_vertical_milestone(repo_root=root)
        assert out.get("active_curated_pack_id") == "founder_operator_core"
        assert out.get("next_milestone_id") == "onboard_approvals_done"
        assert "first_run_completed" in out.get("reached_milestone_ids", [])
        set_milestone_reached("founder_operator_core", "founder_ops_plus_first_value", "onboard_approvals_done", repo_root=root)
        progress = get_path_progress(repo_root=root)
        assert "onboard_approvals_done" in progress.get("reached_milestone_ids", [])


def test_weak_incomplete_path_behavior() -> None:
    path = build_path_for_pack("nonexistent_pack_xyz")
    assert path is None
    pack = get_curated_pack("nonexistent")
    assert pack is None
    ids = list_curated_pack_ids()
    assert "founder_operator_core" in ids
    assert get_curated_pack_for_value_pack("founder_ops_plus") is not None
    assert get_curated_pack_for_value_pack("nonexistent") is None
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        out = get_next_vertical_milestone(repo_root=root)
        assert out.get("active_curated_pack_id") == ""
        assert "suggested_next_command" in out
    blocked = get_blocked_vertical_onboarding_step(repo_root=Path("/nonexistent"))
    assert blocked == {} or "blocked_step_index" in blocked


# ----- M39H.1 Vertical playbooks + recovery -----


def test_playbook_for_vertical() -> None:
    playbook = get_playbook_for_vertical("founder_operator_core")
    assert playbook is not None
    assert playbook.playbook_id == "founder_operator_playbook"
    assert playbook.curated_pack_id == "founder_operator_core"
    assert len(playbook.failure_entries) >= 4
    assert len(playbook.recovery_paths) >= 4
    assert "stalled" in playbook.operator_guidance_stalled.lower()
    assert len(playbook.operator_commands_stalled) >= 1
    d = playbook.to_dict()
    assert d["playbook_id"] == "founder_operator_playbook"
    assert "failure_entries" in d and "recovery_paths" in d


def test_recovery_path_for_failure() -> None:
    playbook = get_playbook_for_vertical("founder_operator_core")
    recovery = get_recovery_path_for_failure(playbook, 3)
    assert recovery is not None
    assert recovery.recovery_path_id == "recover_after_approval_block"
    assert recovery.target_milestone_id == "first_simulate_done"
    assert len(recovery.steps) >= 2
    recovery_none = get_recovery_path_for_failure(playbook, 99)
    assert recovery_none is None
    recovery_none_pb = get_recovery_path_for_failure(None, 1)
    assert recovery_none_pb is None


def test_operator_guidance_when_stalled() -> None:
    out = get_operator_guidance_when_stalled("founder_operator_core", 3)
    assert out["playbook_id"] == "founder_operator_playbook"
    assert "guidance" in out and len(out["guidance"]) > 0
    assert "commands" in out and len(out["commands"]) >= 1
    assert "recovery_path" in out
    assert out["recovery_path"] is not None
    assert out["recovery_path"]["recovery_path_id"] == "recover_after_approval_block"
    assert "failure_entry" in out
    assert out["failure_entry"].get("step_index") == 3
    assert "symptom" in out["failure_entry"]
    # No playbook for unknown pack: fallback guidance
    fallback = get_operator_guidance_when_stalled("nonexistent_pack", 1)
    assert fallback["playbook_id"] == ""
    assert "first-value" in fallback["guidance"].lower() or "vertical-packs" in fallback["guidance"]


def test_list_vertical_playbook_ids() -> None:
    ids = list_vertical_playbook_ids()
    assert "founder_operator_core" in ids
    assert "analyst_core" in ids
    assert "developer_core" in ids
    assert "document_worker_core" in ids
    assert len(ids) == len(BUILTIN_VERTICAL_PLAYBOOKS)


def test_progress_includes_operator_guidance_when_blocked() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        set_active_pack("founder_operator_core", repo_root=root)
        set_path_progress(
            "founder_operator_core",
            "founder_ops_plus_first_value",
            ["first_run_completed"],
            next_milestone_id="runtime_check_done",
            blocked_step_index=3,
            repo_root=root,
        )
        out = build_milestone_progress_output(repo_root=root)
        assert out.get("blocked_step_index") == 3
        assert "operator_guidance_when_stalled" in out
        og = out["operator_guidance_when_stalled"]
        assert og["playbook_id"] == "founder_operator_playbook"
        assert "recovery_path" in og and og["recovery_path"] is not None
        assert og["failure_entry"].get("step_index") == 3
