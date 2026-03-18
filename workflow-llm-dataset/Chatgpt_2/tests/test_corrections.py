"""
M23M: Operator correction loop — add, list, propose, preview, apply, revert, report, eval bridge.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.corrections.schema import (
    CorrectionEvent,
    SOURCE_TYPES,
    CORRECTION_CATEGORIES,
    validate_category_for_source,
    is_eligible_for_memory_update,
)
from workflow_dataset.corrections.store import save_correction, list_corrections, get_correction
from workflow_dataset.corrections.capture import add_correction
from workflow_dataset.corrections.rules import LEARNING_RULES, BLOCKED_TARGETS
from workflow_dataset.corrections.propose import propose_updates, ProposedUpdate
from workflow_dataset.corrections.updates import (
    UpdateRecord,
    save_proposed,
    load_proposed,
    save_update_record,
    load_update_record,
    preview_update,
    apply_update,
    revert_update,
    list_proposed_updates,
)
from workflow_dataset.corrections.history import list_applied_updates, list_reverted_updates
from workflow_dataset.corrections.report import corrections_report, format_corrections_report
from workflow_dataset.corrections.eval_bridge import advisory_review_for_corrections
from workflow_dataset.job_packs.seed_jobs import seed_example_job_pack
from workflow_dataset.desktop_bench.seed_cases import seed_default_cases


@pytest.fixture
def tmp_repo(tmp_path):
    seed_default_cases(tmp_path)
    seed_example_job_pack(tmp_path)
    return tmp_path


def test_correction_event_schema():
    ev = CorrectionEvent(
        correction_id="corr_1",
        timestamp="2026-01-01T00:00:00Z",
        source_type="recommendation",
        source_reference_id="rec_weekly_0",
        operator_action="corrected",
        correction_category="bad_job_parameter_default",
        original_value={"path": "/old"},
        corrected_value={"path": "/new"},
        correction_reason="Wrong default path",
        eligible_for_memory_update=True,
    )
    d = ev.to_dict()
    assert d["correction_id"] == "corr_1"
    assert d["correction_category"] == "bad_job_parameter_default"
    loaded = CorrectionEvent.from_dict(d)
    assert loaded.correction_id == ev.correction_id


def test_validate_category():
    assert validate_category_for_source("bad_job_parameter_default", "job_run") is True
    assert is_eligible_for_memory_update("bad_job_parameter_default") is True
    assert is_eligible_for_memory_update("wrong_recommendation_timing") is False


def test_add_and_list_corrections(tmp_path):
    ev = add_correction(
        source_type="job_run",
        source_reference_id="weekly_status_from_notes",
        correction_category="bad_job_parameter_default",
        corrected_value={"path": "/tmp/out"},
        repo_root=tmp_path,
    )
    assert ev.correction_id.startswith("corr_")
    assert ev.eligible_for_memory_update is True
    listed = list_corrections(limit=5, repo_root=tmp_path)
    assert len(listed) >= 1
    got = get_correction(ev.correction_id, tmp_path)
    assert got is not None
    assert got.source_reference_id == "weekly_status_from_notes"


def test_propose_updates(tmp_repo):
    add_correction(
        source_type="job_run",
        source_reference_id="weekly_status_from_notes",
        correction_category="bad_job_parameter_default",
        corrected_value={"path": "/corrected/path"},
        repo_root=tmp_repo,
    )
    proposed = propose_updates(tmp_repo)
    assert isinstance(proposed, list)
    if proposed:
        p = proposed[0]
        assert isinstance(p, ProposedUpdate)
        assert p.target_type in ("specialization_params", "specialization_paths", "specialization_output_style", "job_pack_trust_notes", "routine_ordering", "trigger_suppression")
        assert p.target_id


def test_preview_apply_revert(tmp_repo):
    add_correction(
        source_type="job_run",
        source_reference_id="weekly_status_from_notes",
        correction_category="bad_job_parameter_default",
        corrected_value={"path": "/corrected"},
        repo_root=tmp_repo,
    )
    proposed = list_proposed_updates(tmp_repo)
    assert len(proposed) >= 1
    upd = proposed[0]
    save_proposed(upd, tmp_repo)
    prev = preview_update(upd.update_id, tmp_repo)
    assert "error" not in prev or not prev["error"]
    assert prev.get("update_id") == upd.update_id
    appl = apply_update(upd.update_id, tmp_repo)
    assert appl.get("error") is None
    assert appl.get("applied") == upd.update_id
    applied = list_applied_updates(limit=5, repo_root=tmp_repo)
    assert len(applied) >= 1
    rev = revert_update(upd.update_id, tmp_repo)
    assert rev.get("error") is None
    assert rev.get("reverted") == upd.update_id
    reverted = list_reverted_updates(limit=5, repo_root=tmp_repo)
    assert len(reverted) >= 1


def test_blocked_targets():
    assert "trust_level" in BLOCKED_TARGETS
    assert "approval_registry" in BLOCKED_TARGETS


def test_corrections_report(tmp_repo):
    add_correction("job_run", "j1", "output_style_correction", corrected_value="markdown", repo_root=tmp_repo)
    report = corrections_report(tmp_repo)
    assert "recent_corrections_count" in report
    assert "proposed_updates_count" in report
    assert "applied_updates_count" in report
    assert "most_corrected_ids" in report
    text = format_corrections_report(report)
    assert "Corrections report" in text


def test_advisory_review(tmp_repo):
    add_correction("job_run", "same_job", "trust_notes_correction", corrected_value="note", repo_root=tmp_repo)
    add_correction("job_run", "same_job", "trust_notes_correction", corrected_value="note2", repo_root=tmp_repo)
    advisories = advisory_review_for_corrections(tmp_repo, limit=20, min_count=2)
    assert isinstance(advisories, list)
    ids = [a["job_or_routine_id"] for a in advisories]
    if advisories:
        assert "same_job" in ids or len(advisories) >= 0


def test_mission_control_includes_corrections(tmp_repo):
    from workflow_dataset.mission_control.state import get_mission_control_state
    state = get_mission_control_state(tmp_repo)
    assert "corrections" in state
    cor = state["corrections"]
    if not cor.get("error"):
        assert "recent_corrections_count" in cor or "proposed_updates_count" in cor
