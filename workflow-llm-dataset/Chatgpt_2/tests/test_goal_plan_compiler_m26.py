"""
M26A–M26D: Goal-to-plan compiler — schema, compilation, dependency graph, blocked, explain, pack/macro influence.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_dataset.planner.schema import (
    GoalRequest,
    Plan,
    PlanStep,
    DependencyEdge,
    Checkpoint,
    ExpectedArtifact,
    BlockedCondition,
    ProvenanceSource,
    STEP_CLASS_BLOCKED,
    STEP_CLASS_REASONING,
)
from workflow_dataset.planner.compile import compile_goal_to_plan, _tokenize, _score_match
from workflow_dataset.planner.explain import explain_plan
from workflow_dataset.planner.preview import format_plan_preview, format_plan_graph
from workflow_dataset.planner.store import save_current_goal, load_current_goal, save_latest_plan, load_latest_plan
from workflow_dataset.planner.classify import classify_plan_step


def test_goal_request_schema():
    g = GoalRequest(goal_text="Prepare weekly update", context_session_id="s1")
    assert g.goal_text == "Prepare weekly update"
    assert g.context_session_id == "s1"


def test_plan_step_to_dict():
    ps = PlanStep(
        step_index=0,
        label="Run report",
        step_class="sandbox_write",
        provenance=ProvenanceSource(kind="job", ref="weekly_report", label="Weekly report"),
    )
    d = ps.to_dict()
    assert d["step_index"] == 0
    assert d["label"] == "Run report"
    assert d["provenance"]["kind"] == "job"
    assert d["provenance"]["ref"] == "weekly_report"


def test_plan_roundtrip():
    plan = Plan(
        plan_id="p1",
        goal_text="Test goal",
        steps=[
            PlanStep(0, "Step 1", step_class="local_inspect", provenance=ProvenanceSource("job", "j1", "J1")),
            PlanStep(1, "Step 2", step_class="sandbox_write", provenance=ProvenanceSource("macro", "m1", "M1")),
        ],
        edges=[DependencyEdge(0, 1, "sequence")],
        checkpoints=[Checkpoint(0, "approval")],
        expected_artifacts=[ExpectedArtifact("out1", step_index=0)],
        blocked_conditions=[BlockedCondition("policy", step_index=1)],
        sources_used=["job:j1", "macro:m1"],
        created_at="2024-01-01T00:00:00Z",
    )
    d = plan.to_dict()
    plan2 = Plan.from_dict(d)
    assert plan2.plan_id == plan.plan_id
    assert len(plan2.steps) == 2
    assert len(plan2.edges) == 1
    assert plan2.steps[1].provenance is not None
    assert plan2.steps[1].provenance.kind == "macro"


def test_tokenize():
    assert "weekly" in _tokenize("Prepare weekly stakeholder update")
    assert "update" in _tokenize("Prepare weekly stakeholder update")


def test_score_match():
    tokens = _tokenize("weekly report")
    assert _score_match(tokens, "Weekly report", "weekly_report") >= 2
    assert _score_match(tokens, "Other job", "other") == 0


def test_compile_goal_no_sources(tmp_path):
    """With no jobs/routines, compiler returns a single reasoning step."""
    plan = compile_goal_to_plan("Do something unknown", tmp_path)
    assert plan.plan_id
    assert plan.goal_text == "Do something unknown"
    assert len(plan.steps) >= 1
    assert plan.steps[0].step_class in (STEP_CLASS_REASONING, "reasoning_only")
    assert "no_match" in plan.sources_used or "planning" in str(plan.sources_used).lower()


def test_compile_goal_with_routine(tmp_path):
    """When a routine matches goal keywords, plan may have steps from that routine."""
    # Create minimal routine and job under tmp_path as repo root
    routines_dir = tmp_path / "data/local/copilot/routines"
    routines_dir.mkdir(parents=True)
    (routines_dir / "weekly_stakeholder_update.yaml").write_text(
        "routine_id: weekly_stakeholder_update\ntitle: Weekly stakeholder update\njob_pack_ids:\n  - weekly_report\n",
        encoding="utf-8",
    )
    job_packs_dir = tmp_path / "data/local/job_packs"
    job_packs_dir.mkdir(parents=True)
    (job_packs_dir / "weekly_report.yaml").write_text(
        "job_pack_id: weekly_report\ntitle: Weekly report\ndescription: Generate weekly report\n"
        "simulate_support: true\nreal_mode_eligibility: false\n",
        encoding="utf-8",
    )
    plan = compile_goal_to_plan("Prepare weekly stakeholder update", tmp_path)
    assert plan.plan_id
    assert plan.goal_text == "Prepare weekly stakeholder update"
    assert isinstance(plan.steps, list)
    # With matching routine title, compiler may produce steps from routine or fallback to reasoning step
    assert len(plan.steps) >= 1


def test_blocked_condition_in_plan():
    plan = Plan(
        plan_id="p1",
        goal_text="Goal",
        steps=[PlanStep(0, "S1", step_class=STEP_CLASS_BLOCKED, blocked_reason="Policy blocks")],
        blocked_conditions=[BlockedCondition("Policy blocks", step_index=0)],
    )
    assert len(plan.blocked_conditions) == 1
    assert plan.blocked_conditions[0].reason == "Policy blocks"


def test_explain_plan():
    plan = Plan(
        plan_id="ex1",
        goal_text="Weekly update",
        steps=[
            PlanStep(0, "Run report", step_class="sandbox_write", provenance=ProvenanceSource("job", "r1", "Report")),
            PlanStep(1, "Review", step_class="human_required", approval_required=True, provenance=ProvenanceSource("macro", "m1", "Review")),
        ],
        checkpoints=[Checkpoint(0, "approval")],
        expected_artifacts=[ExpectedArtifact("report.pdf", step_index=0)],
        sources_used=["job:r1"],
    )
    text = explain_plan(plan)
    assert "Weekly update" in text
    assert "job:r1" in text
    assert "Human approval" in text
    assert "report.pdf" in text


def test_format_plan_preview():
    plan = Plan(
        plan_id="pv1",
        goal_text="Preview goal",
        steps=[PlanStep(0, "Step one", step_class="local_inspect")],
    )
    out = format_plan_preview(plan)
    assert "pv1" in out
    assert "Preview goal" in out
    assert "Step one" in out
    assert "local_inspect" in out


def test_format_plan_graph():
    plan = Plan(
        plan_id="g1",
        steps=[
            PlanStep(0, "A"),
            PlanStep(1, "B"),
        ],
        edges=[DependencyEdge(0, 1, "sequence")],
    )
    out = format_plan_graph(plan)
    assert "node_0" in out
    assert "node_1" in out
    assert "node_0 -> node_1" in out


def test_store_goal_and_plan(tmp_path):
    save_current_goal("My goal", tmp_path)
    assert load_current_goal(tmp_path) == "My goal"
    plan = Plan(plan_id="store1", goal_text="My goal", steps=[PlanStep(0, "One")])
    save_latest_plan(plan, tmp_path)
    loaded = load_latest_plan(tmp_path)
    assert loaded is not None
    assert loaded.plan_id == "store1"
    assert len(loaded.steps) == 1


def test_classify_plan_step_blocked():
    step = PlanStep(0, "X", blocked_reason="Not allowed")
    out = classify_plan_step(step, None)
    assert out == STEP_CLASS_BLOCKED
