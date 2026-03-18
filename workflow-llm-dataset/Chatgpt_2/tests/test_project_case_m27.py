"""
M27A–M27D: Project/case and goal stack tests. First-draft coverage.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_create_and_load_project(tmp_path):
    from workflow_dataset.project_case import create_project, load_project
    proj = create_project("founder_case_alpha", title="Founder case alpha", repo_root=tmp_path)
    assert proj.project_id == "founder_case_alpha"
    assert proj.title == "Founder case alpha"
    assert proj.state == "active"
    loaded = load_project("founder_case_alpha", tmp_path)
    assert loaded is not None
    assert loaded.project_id == proj.project_id


def test_list_projects(tmp_path):
    from workflow_dataset.project_case import create_project, list_projects
    create_project("p1", repo_root=tmp_path)
    create_project("p2", title="Second", repo_root=tmp_path)
    projects = list_projects(repo_root=tmp_path)
    assert len(projects) == 2
    ids = {p["project_id"] for p in projects}
    assert "p1" in ids and "p2" in ids


def test_archive_project(tmp_path):
    from workflow_dataset.project_case import create_project, load_project, archive_project
    create_project("to_archive", repo_root=tmp_path)
    assert archive_project("to_archive", tmp_path) is True
    proj = load_project("to_archive", tmp_path)
    assert proj is not None
    assert proj.state == "archived"


def test_goal_stack_ordering(tmp_path):
    from workflow_dataset.project_case import create_project, add_goal, list_goals, set_goal_order
    create_project("gstack", repo_root=tmp_path)
    add_goal("gstack", "g1", title="First", order=10, repo_root=tmp_path)
    add_goal("gstack", "g2", title="Second", order=0, repo_root=tmp_path)
    goals = list_goals("gstack", tmp_path)
    assert len(goals) == 2
    orders = [g.order for g in goals]
    assert 0 in orders and 10 in orders
    set_goal_order("gstack", "g1", 0, tmp_path)
    set_goal_order("gstack", "g2", 1, tmp_path)
    goals = list_goals("gstack", tmp_path)
    assert goals[0].goal_id == "g1" and goals[0].order == 0


def test_goal_status_active_blocked(tmp_path):
    from workflow_dataset.project_case import create_project, add_goal, set_goal_status, get_blocked_goals
    create_project("status_proj", repo_root=tmp_path)
    add_goal("status_proj", "blocked_goal", title="Blocked", repo_root=tmp_path)
    set_goal_status("status_proj", "blocked_goal", "blocked", blocked_reason="Waiting on approval", repo_root=tmp_path)
    blocked = get_blocked_goals("status_proj", tmp_path)
    assert len(blocked) == 1
    assert blocked[0][0].goal_id == "blocked_goal"
    assert "approval" in blocked[0][1].lower()


def test_recommended_next_goal(tmp_path):
    from workflow_dataset.project_case import create_project, add_goal, recommended_next_goal
    create_project("rec", repo_root=tmp_path)
    add_goal("rec", "first", title="First active", repo_root=tmp_path)
    next_act = recommended_next_goal("rec", tmp_path)
    assert next_act is not None
    assert next_act.action_type == "work_goal"
    assert next_act.ref == "first"


def test_attach_session_and_run(tmp_path):
    from workflow_dataset.project_case import create_project, attach_session, attach_run, get_linked_sessions, get_linked_runs
    create_project("links", repo_root=tmp_path)
    attach_session("links", "sess_1", tmp_path)
    attach_session("links", "sess_2", tmp_path)
    attach_run("links", "run_abc", tmp_path)
    sessions = get_linked_sessions("links", tmp_path)
    runs = get_linked_runs("links", tmp_path)
    assert len(sessions) == 2
    assert len(runs) == 1
    assert runs[0].run_id == "run_abc"


def test_project_report_format(tmp_path):
    from workflow_dataset.project_case import create_project, add_goal, set_goal_status, format_project_report
    create_project("report_proj", title="Report project", repo_root=tmp_path)
    add_goal("report_proj", "g1", title="Goal one", repo_root=tmp_path)
    set_goal_status("report_proj", "g1", "blocked", blocked_reason="Depends on X", repo_root=tmp_path)
    report = format_project_report("report_proj", tmp_path)
    assert "Report project" in report
    assert "blocked" in report.lower()
    assert "g1" in report or "Goal one" in report


def test_current_project_id(tmp_path):
    from workflow_dataset.project_case import create_project, set_current_project_id, get_current_project_id
    create_project("cur", repo_root=tmp_path)
    assert get_current_project_id(tmp_path) is None
    set_current_project_id("cur", tmp_path)
    assert get_current_project_id(tmp_path) == "cur"
    set_current_project_id(None, tmp_path)
    assert get_current_project_id(tmp_path) is None


def test_project_summary_for_mission_control(tmp_path):
    from workflow_dataset.project_case import create_project, add_goal, get_project_summary
    create_project("mc_proj", title="MC project", repo_root=tmp_path)
    add_goal("mc_proj", "g1", repo_root=tmp_path)
    summary = get_project_summary("mc_proj", tmp_path)
    assert summary.get("error") is None
    assert summary.get("project_id") == "mc_proj"
    assert summary.get("goals_count") == 1
    assert "project_state" in summary
    assert summary.get("project_state", {}).get("active_goals_count") == 1


# ----- M27D.1 Project templates + goal archetypes -----


def test_list_templates():
    from workflow_dataset.project_case import list_templates
    templates = list_templates()
    assert len(templates) >= 4
    ids = {t.template_id for t in templates}
    assert "founder_ops" in ids
    assert "analyst_research" in ids
    assert "document_review" in ids
    assert "developer_feature" in ids


def test_get_template():
    from workflow_dataset.project_case import get_template
    t = get_template("founder_ops")
    assert t is not None
    assert t.template_id == "founder_ops"
    assert "Founder" in t.title
    assert len(t.default_goal_stack) >= 2
    assert t.recommended_pack_ids or t.recommended_value_pack_ids


def test_create_project_from_template(tmp_path):
    from workflow_dataset.project_case import create_project_from_template, load_project, list_goals, get_linked_artifacts
    proj = create_project_from_template("from_founder", "founder_ops", repo_root=tmp_path)
    assert proj is not None
    assert proj.project_id == "from_founder"
    goals = list_goals("from_founder", tmp_path)
    assert len(goals) >= 2
    goal_ids = {g.goal_id for g in goals}
    assert "ship_weekly_report" in goal_ids
    artifacts = get_linked_artifacts("from_founder", tmp_path)
    assert len(artifacts) >= 1
    assert any("weekly" in a.path_or_label for a in artifacts) or any(a.path_or_label for a in artifacts)


def test_goal_archetype_output():
    from workflow_dataset.project_case import format_goal_archetype, get_template
    t = get_template("analyst_research")
    assert t is not None
    out = format_goal_archetype("analyst_research")
    assert "analyst_research" in out
    assert "Default goal stack" in out
    assert "gather_sources" in out or "Synthesize" in out
    assert "Common artifacts" in out
    assert "Recommended" in out or "recommended" in out.lower()
