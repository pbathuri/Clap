"""
M26I–M26L: Teaching studio + skill capture — skill model, store, demo-to-skill, review, report.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.teaching.skill_models import Skill, SKILL_STATUSES, TRUST_READINESS_LEVELS
from workflow_dataset.teaching.skill_store import (
    get_skills_dir,
    save_skill,
    load_skill,
    list_skills,
    delete_skill,
)
from workflow_dataset.teaching.normalize import (
    demo_to_skill_draft,
    correction_to_skill_draft,
    manual_skill_draft,
)
from workflow_dataset.teaching.review import (
    list_candidate_skills,
    accept_skill,
    reject_skill,
    attach_skill_to_pack,
)
from workflow_dataset.teaching.report import build_skill_report, format_skill_report
from workflow_dataset.teaching.scorecard import (
    build_skill_scorecard,
    format_skill_scorecard,
    build_pack_goal_coverage_report,
    format_pack_goal_coverage_report,
)


def test_skill_model_roundtrip():
    s = Skill(
        skill_id="skill_1",
        source_type="task_demo",
        source_reference_id="demo_123",
        goal_family="reporting",
        task_family="weekly",
        status="draft",
        normalized_steps=[{"adapter_id": "file_ops", "action_id": "inspect_path", "params": {}, "notes": ""}],
    )
    d = s.to_dict()
    assert d["skill_id"] == "skill_1"
    assert d["status"] == "draft"
    assert len(d["normalized_steps"]) == 1
    loaded = Skill.from_dict(d)
    assert loaded.skill_id == s.skill_id
    assert loaded.normalized_steps == s.normalized_steps


def test_skill_store_save_load_list(tmp_path):
    skill = Skill(skill_id="test_skill", source_type="manual", status="draft")
    save_skill(skill, tmp_path)
    assert get_skills_dir(tmp_path).exists()
    loaded = load_skill("test_skill", tmp_path)
    assert loaded is not None
    assert loaded.skill_id == "test_skill"
    all_ = list_skills(repo_root=tmp_path)
    assert len(all_) >= 1
    assert any(s.skill_id == "test_skill" for s in all_)
    draft_only = list_skills(status="draft", repo_root=tmp_path)
    assert any(s.skill_id == "test_skill" for s in draft_only)


def test_skill_store_delete(tmp_path):
    skill = Skill(skill_id="to_delete", source_type="manual", status="draft")
    save_skill(skill, tmp_path)
    assert load_skill("to_delete", tmp_path) is not None
    ok = delete_skill("to_delete", tmp_path)
    assert ok is True
    assert load_skill("to_delete", tmp_path) is None


def test_demo_to_skill_draft(tmp_path):
    from workflow_dataset.task_demos.models import TaskDefinition, TaskStep
    from workflow_dataset.task_demos.store import save_task as save_task_demo
    (tmp_path / "data/local/task_demonstrations").mkdir(parents=True, exist_ok=True)
    task = TaskDefinition(
        task_id="demo_weekly",
        steps=[
            TaskStep("file_ops", "inspect_path", {"path": "/tmp"}),
            TaskStep("browser_open", "open_url", {"url": "https://example.com"}),
        ],
        notes="Weekly demo",
    )
    save_task_demo(task, tmp_path)
    skill = demo_to_skill_draft("demo_weekly", goal_family="reporting", repo_root=tmp_path)
    assert skill is not None
    assert skill.source_type == "task_demo"
    assert skill.source_reference_id == "demo_weekly"
    assert skill.status == "draft"
    assert len(skill.normalized_steps) == 2
    assert skill.normalized_steps[0].get("adapter_id") == "file_ops"
    assert skill.normalized_steps[1].get("action_id") == "open_url"


def test_demo_to_skill_missing_returns_none(tmp_path):
    out = demo_to_skill_draft("nonexistent_demo", repo_root=tmp_path)
    assert out is None


def test_correction_to_skill_draft(tmp_path):
    from workflow_dataset.corrections.schema import CorrectionEvent
    from workflow_dataset.corrections.store import save_correction
    (tmp_path / "data/local/corrections/events").mkdir(parents=True, exist_ok=True)
    ev = CorrectionEvent(
        correction_id="corr_1",
        timestamp="2026-01-01T00:00:00Z",
        source_type="job_run",
        source_reference_id="job_weekly",
        operator_action="corrected",
        correction_category="bad_job_parameter_default",
        original_value={"path": "/old"},
        corrected_value={"path": "/new"},
        correction_reason="Wrong default",
    )
    save_correction(ev, tmp_path)
    skill = correction_to_skill_draft("corr_1", goal_family="reporting", repo_root=tmp_path)
    assert skill is not None
    assert skill.source_type == "correction"
    assert skill.source_reference_id == "corr_1"
    assert skill.status == "draft"
    assert len(skill.normalized_steps) == 1
    assert skill.normalized_steps[0].get("category") == "bad_job_parameter_default"


def test_correction_to_skill_missing_returns_none(tmp_path):
    out = correction_to_skill_draft("nonexistent_corr", repo_root=tmp_path)
    assert out is None


def test_manual_skill_draft(tmp_path):
    skill = manual_skill_draft(
        "manual_1",
        goal_family="ops",
        task_family="deploy",
        normalized_steps=[{"kind": "manual", "description": "Run deploy script"}],
        expected_inputs=["repo_path"],
        expected_outputs=["artifact_path"],
        operator_notes="First draft",
        repo_root=tmp_path,
    )
    assert skill.skill_id == "manual_1"
    assert skill.source_type == "manual"
    assert skill.status == "draft"
    assert skill.operator_notes == "First draft"
    loaded = load_skill("manual_1", tmp_path)
    assert loaded is not None
    assert loaded.expected_inputs == ["repo_path"]


def test_accept_reject_skill(tmp_path):
    skill = Skill(skill_id="review_me", source_type="manual", status="draft")
    save_skill(skill, tmp_path)
    accepted = accept_skill("review_me", simulate_only_or_trusted_real="simulate_only", repo_root=tmp_path)
    assert accepted is not None
    assert accepted.status == "accepted"
    assert accepted.accepted_at
    loaded = load_skill("review_me", tmp_path)
    assert loaded.status == "accepted"

    skill2 = Skill(skill_id="reject_me", source_type="manual", status="draft")
    save_skill(skill2, tmp_path)
    rejected = reject_skill("reject_me", operator_notes="Not reusable", repo_root=tmp_path)
    assert rejected is not None
    assert rejected.status == "rejected"
    assert load_skill("reject_me", tmp_path).status == "rejected"


def test_attach_skill_to_pack(tmp_path):
    skill = Skill(skill_id="attach_me", source_type="manual", status="accepted", pack_associations=[])
    save_skill(skill, tmp_path)
    updated = attach_skill_to_pack("attach_me", "founder_ops_plus", tmp_path)
    assert updated is not None
    assert "founder_ops_plus" in updated.pack_associations
    updated2 = attach_skill_to_pack("attach_me", "founder_ops_plus", tmp_path)
    assert updated2.pack_associations.count("founder_ops_plus") == 1


def test_list_candidate_skills(tmp_path):
    save_skill(Skill(skill_id="c1", source_type="manual", status="draft"), tmp_path)
    save_skill(Skill(skill_id="c2", source_type="manual", status="accepted"), tmp_path)
    candidates = list_candidate_skills(status="draft", repo_root=tmp_path)
    assert any(s.skill_id == "c1" for s in candidates)
    assert not any(s.skill_id == "c2" for s in candidates)


def test_skill_report(tmp_path):
    save_skill(Skill(skill_id="d1", source_type="manual", status="draft"), tmp_path)
    save_skill(Skill(skill_id="a1", source_type="manual", status="accepted"), tmp_path)
    report = build_skill_report(tmp_path)
    assert report["draft_count"] >= 1
    assert report["accepted_count"] >= 1
    assert "d1" in report["draft_ids"] or report["draft_count"] >= 1
    text = format_skill_report(report)
    assert "draft" in text
    assert "accepted" in text


def test_weak_unclear_skills_in_report(tmp_path):
    save_skill(
        Skill(skill_id="weak1", source_type="manual", status="draft", trust_readiness_status="unclear", normalized_steps=[]),
        tmp_path,
    )
    report = build_skill_report(tmp_path)
    assert report["weak_unclear_count"] >= 1
    assert "weak1" in report["weak_unclear_ids"] or report["weak_unclear_count"] >= 1


def test_blocked_skill_status(tmp_path):
    skill = Skill(
        skill_id="blocked_1",
        source_type="manual",
        status="draft",
        trust_readiness_status="blocked",
        normalized_steps=[],
    )
    save_skill(skill, tmp_path)
    report = build_skill_report(tmp_path)
    assert any(sid == "blocked_1" for sid in report["weak_unclear_ids"])


def test_skill_scorecard(tmp_path):
    save_skill(Skill(skill_id="s1", source_type="manual", status="draft", goal_family="reporting"), tmp_path)
    save_skill(Skill(skill_id="s2", source_type="manual", status="accepted", goal_family="reporting", pack_associations=["founder_ops_plus"]), tmp_path)
    save_skill(Skill(skill_id="s3", source_type="manual", status="accepted", goal_family="reporting", pack_associations=["founder_ops_plus"], simulate_only_or_trusted_real="trusted_real_candidate"), tmp_path)
    sc = build_skill_scorecard(tmp_path)
    assert sc["summary"]["draft_count"] >= 1
    assert sc["summary"]["accepted_count"] >= 2
    assert sc["summary"]["trusted_real_count"] >= 1
    assert "founder_ops_plus" in sc["by_pack"]
    assert sc["by_pack"]["founder_ops_plus"]["accepted"] >= 2
    assert "founder_ops_plus" in sc["packs_strong_coverage"]
    assert "reporting" in sc["by_goal_family"]
    text = format_skill_scorecard(sc)
    assert "Skill scorecard" in text
    assert "strong" in text or "weak" in text


def test_pack_goal_coverage_report(tmp_path):
    save_skill(Skill(skill_id="g1", source_type="manual", status="accepted", goal_family="ops", pack_associations=["analyst_pack"]), tmp_path)
    report = build_pack_goal_coverage_report(tmp_path)
    assert "packs" in report
    assert "goal_families" in report
    pack_ids = [r["pack_id"] for r in report["packs"]]
    assert "analyst_pack" in pack_ids
    goal_names = [r["goal_family"] for r in report["goal_families"]]
    assert "ops" in goal_names
    text = format_pack_goal_coverage_report(report)
    assert "Pack / Goal" in text
    assert "analyst_pack" in text
    assert "ops" in text
