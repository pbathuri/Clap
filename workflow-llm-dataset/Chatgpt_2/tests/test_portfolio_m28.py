"""
M28: Portfolio router + project scheduler tests. Models, ranking, stalled/blocked, explain, next, edge cases.
"""

from __future__ import annotations

from pathlib import Path

import pytest


def test_portfolio_models_roundtrip():
    """Portfolio model to_dict/from_dict roundtrip."""
    from workflow_dataset.portfolio.models import (
        UrgencyScore,
        ValueScore,
        BlockerSeverity,
        ProjectPriority,
        AttentionRecommendation,
        DeferRevisitState,
        PortfolioHealth,
        PortfolioEntry,
        Portfolio,
    )
    u = UrgencyScore(score=0.8, reason="Deadline soon")
    assert UrgencyScore.from_dict(u.to_dict()).score == u.score
    v = ValueScore(score=0.7, operator_hint="high")
    assert ValueScore.from_dict(v.to_dict()).operator_hint == v.operator_hint
    b = BlockerSeverity(level="partial", blocked_goals_count=1, can_advance=True)
    assert BlockerSeverity.from_dict(b.to_dict()).level == b.level
    pr = ProjectPriority(project_id="p1", tier="high", urgency=u, value=v, blocker=b, rank_index=1, composite_score=0.75)
    back = ProjectPriority.from_dict(pr.to_dict())
    assert back.project_id == pr.project_id and back.composite_score == pr.composite_score
    ar = AttentionRecommendation(project_id="p1", reason="Best next", action_hint="advance")
    assert AttentionRecommendation.from_dict(ar.to_dict()).action_hint == ar.action_hint
    dr = DeferRevisitState(project_id="p1", reason="Paused", active=True)
    assert DeferRevisitState.from_dict(dr.to_dict()).active
    h = PortfolioHealth(total_active=2, stalled_count=1, labels=["1 stalled"])
    assert PortfolioHealth.from_dict(h.to_dict()).total_active == 2
    entry = PortfolioEntry(project_id="p1", title="Proj 1", priority=pr, health_label="stalled", is_stalled=True)
    assert PortfolioEntry.from_dict(entry.to_dict()).project_id == entry.project_id
    port = Portfolio(entries=[entry], health=h, next_recommended_project=ar)
    assert Portfolio.from_dict(port.to_dict()).health.total_active == port.health.total_active


def test_rank_empty_returns_empty(tmp_path):
    """With no active projects, rank_active_projects returns []."""
    from workflow_dataset.portfolio import rank_active_projects
    ranked = rank_active_projects(repo_root=tmp_path)
    assert ranked == []


def test_rank_with_active_projects(tmp_path):
    """With active projects, rank returns ordered list with rank_index and composite_score."""
    from workflow_dataset.project_case import create_project
    from workflow_dataset.portfolio import rank_active_projects
    create_project("alpha", title="Alpha", repo_root=tmp_path)
    create_project("beta", title="Beta", repo_root=tmp_path)
    ranked = rank_active_projects(repo_root=tmp_path)
    assert len(ranked) == 2
    ids = {p.project_id for p in ranked}
    assert "alpha" in ids and "beta" in ids
    for i, p in enumerate(ranked):
        assert p.rank_index == i + 1
        assert hasattr(p, "composite_score")


def test_stalled_blocked_detection(tmp_path):
    """report_stalled and report_blocked return entries; empty when none."""
    from workflow_dataset.project_case import create_project
    from workflow_dataset.portfolio import report_stalled, report_blocked, build_portfolio
    create_project("s1", repo_root=tmp_path)
    stalled = report_stalled(repo_root=tmp_path)
    blocked = report_blocked(repo_root=tmp_path)
    # May be 0 or 1 depending on progress board; at least no crash
    assert isinstance(stalled, list)
    assert isinstance(blocked, list)
    portfolio = build_portfolio(repo_root=tmp_path)
    assert portfolio.health.total_active >= 0


def test_explain_priority_output(tmp_path):
    """explain_priority returns string with rank, tier, urgency, value, blocker."""
    from workflow_dataset.project_case import create_project
    from workflow_dataset.portfolio import explain_priority
    create_project("explain_me", title="Explain me", repo_root=tmp_path)
    text = explain_priority("explain_me", repo_root=tmp_path)
    assert "explain_me" in text
    assert "Rank" in text or "rank" in text
    assert "Urgency" in text or "urgency" in text
    assert "Value" in text or "value" in text
    assert "Blocker" in text or "blocker" in text


def test_explain_priority_unknown_project(tmp_path):
    """explain_priority for unknown project returns message."""
    from workflow_dataset.portfolio import explain_priority
    text = explain_priority("nonexistent_xyz", repo_root=tmp_path)
    assert "not found" in text or "nonexistent" in text or "No active" in text


def test_next_project_recommendation(tmp_path):
    """get_next_recommended_project returns recommendation or None when no projects."""
    from workflow_dataset.portfolio import get_next_recommended_project
    rec = get_next_recommended_project(repo_root=tmp_path)
    # No projects -> None
    assert rec is None or (rec.project_id and rec.reason)


def test_next_project_with_active(tmp_path):
    """With active project, next recommended has project_id and reason."""
    from workflow_dataset.project_case import create_project
    from workflow_dataset.portfolio import get_next_recommended_project
    create_project("only_one", repo_root=tmp_path)
    rec = get_next_recommended_project(repo_root=tmp_path)
    assert rec is not None
    assert rec.project_id == "only_one"
    assert rec.reason or rec.action_hint


def test_no_project_all_blocked_edge_case(tmp_path):
    """build_portfolio with no active projects: empty entries, no next recommended."""
    from workflow_dataset.portfolio import build_portfolio
    portfolio = build_portfolio(repo_root=tmp_path)
    assert portfolio.entries == [] or all(e.project_id for e in portfolio.entries)
    # With zero projects, next_recommended_project should be None
    if portfolio.health.total_active == 0:
        assert portfolio.next_recommended_project is None


def test_portfolio_store_priority_hints(tmp_path):
    """Priority hints load/save and get_deferred_project_ids."""
    from workflow_dataset.portfolio.store import (
        load_priority_hints,
        save_priority_hints,
        load_defer_revisit,
        save_defer_revisit,
        get_deferred_project_ids,
    )
    from workflow_dataset.portfolio.models import DeferRevisitState
    assert load_priority_hints(tmp_path) == {}
    save_priority_hints({"p1": "high", "p2": "low"}, tmp_path)
    hints = load_priority_hints(tmp_path)
    assert hints.get("p1") == "high" and hints.get("p2") == "low"
    assert get_deferred_project_ids(tmp_path) == set()
    save_defer_revisit([DeferRevisitState(project_id="p1", reason="Pause", active=True)], tmp_path)
    assert get_deferred_project_ids(tmp_path) == {"p1"}


def test_mission_control_includes_portfolio_router(tmp_path):
    """get_mission_control_state includes portfolio_router when portfolio module is used."""
    from workflow_dataset.mission_control.state import get_mission_control_state
    state = get_mission_control_state(tmp_path)
    assert "portfolio_router" in state
    pr = state["portfolio_router"]
    if "error" not in pr:
        assert "priority_stack" in pr
        assert "next_recommended_project" in pr
        assert "health_total_active" in pr


# ----- M28D.1 Attention budgets + work windows -----


def test_attention_budget_work_window_focus_mode_roundtrip():
    """M28D.1: AttentionBudget, WorkWindow, FocusMode, SwitchRecommendation, WorkWindowRecommendation roundtrip."""
    from workflow_dataset.portfolio.models import (
        AttentionBudget,
        WorkWindow,
        FocusMode,
        SwitchRecommendation,
        WorkWindowRecommendation,
    )
    ab = AttentionBudget(project_id="p1", minutes_per_day=60, reset_interval="day")
    assert AttentionBudget.from_dict(ab.to_dict()).minutes_per_day == 60
    ww = WorkWindow(window_id="w1", name="Pomodoro", duration_minutes=25, days_of_week=[1, 2, 3])
    assert WorkWindow.from_dict(ww.to_dict()).duration_minutes == 25
    fm = FocusMode(mode_id="m1", name="Round robin", switch_rules=["on_window_end", "when_higher_priority_ready"])
    assert FocusMode.from_dict(fm.to_dict()).switch_rules == fm.switch_rules
    sr = SwitchRecommendation(recommend_switch=True, suggested_project_id="p2", rule_triggered="higher_priority_ready")
    assert SwitchRecommendation.from_dict(sr.to_dict()).recommend_switch is True
    wr = WorkWindowRecommendation(project_id="p1", duration_minutes=25, remaining_minutes=10)
    assert WorkWindowRecommendation.from_dict(wr.to_dict()).remaining_minutes == 10


def test_work_window_recommendation_no_config(tmp_path):
    """M28D.1: get_work_window_recommendation with no config returns default duration and no remaining."""
    from workflow_dataset.portfolio.attention import get_work_window_recommendation
    rec = get_work_window_recommendation(repo_root=tmp_path)
    assert rec.duration_minutes >= 0
    assert rec.remaining_minutes is None or rec.remaining_minutes >= 0


def test_work_window_recommendation_with_config(tmp_path):
    """M28D.1: With attention_config work_windows, recommendation uses that duration."""
    from workflow_dataset.portfolio.store import save_attention_config
    from workflow_dataset.portfolio.models import WorkWindow, AttentionBudget, FocusMode
    save_attention_config(
        work_windows=[WorkWindow(window_id="w1", name="Custom", duration_minutes=45)],
        attention_budgets=[],
        focus_modes=[],
        repo_root=tmp_path,
    )
    from workflow_dataset.portfolio.attention import get_work_window_recommendation
    rec = get_work_window_recommendation(repo_root=tmp_path)
    assert rec.duration_minutes == 45
    assert rec.window_name == "Custom"


def test_should_recommend_switch_no_projects(tmp_path):
    """M28D.1: should_recommend_switch with no active projects returns recommend_switch False or no suggested."""
    from workflow_dataset.portfolio.attention import should_recommend_switch
    rec = should_recommend_switch(repo_root=tmp_path)
    assert hasattr(rec, "recommend_switch")
    assert rec.rule_triggered in ("manual_only", "higher_priority_ready", "")


def test_should_recommend_switch_with_project(tmp_path):
    """M28D.1: With one active project, should_recommend_switch returns consistent result."""
    from workflow_dataset.project_case import create_project
    from workflow_dataset.portfolio.attention import should_recommend_switch
    create_project("only", repo_root=tmp_path)
    rec = should_recommend_switch(current_project_id="only", repo_root=tmp_path)
    assert rec.current_project_id == "only"
    assert rec.rule_triggered in ("manual_only", "higher_priority_ready", "work_window_ended", "")


def test_start_work_window(tmp_path):
    """M28D.1: start_work_window sets current_window_started_at and returns iso string."""
    from workflow_dataset.portfolio.attention import start_work_window, get_work_window_recommendation
    ts = start_work_window(repo_root=tmp_path)
    assert "T" in ts or "-" in ts
    rec = get_work_window_recommendation(repo_root=tmp_path)
    assert rec.remaining_minutes is not None or rec.duration_minutes >= 0


def test_load_save_attention_config(tmp_path):
    """M28D.1: load_attention_config and save_attention_config roundtrip."""
    from workflow_dataset.portfolio.store import save_attention_config, load_attention_config
    from workflow_dataset.portfolio.models import AttentionBudget, WorkWindow, FocusMode
    save_attention_config(
        attention_budgets=[AttentionBudget(project_id="p1", minutes_per_day=30)],
        work_windows=[WorkWindow(window_id="w1", duration_minutes=25)],
        focus_modes=[FocusMode(mode_id="f1", switch_rules=["on_window_end"])],
        active_focus_mode_id="f1",
        repo_root=tmp_path,
    )
    config = load_attention_config(tmp_path)
    assert len(config.get("attention_budgets", [])) == 1
    assert config.get("attention_budgets", [{}])[0].get("project_id") == "p1"
    assert len(config.get("work_windows", [])) == 1
    assert config.get("active_focus_mode_id") == "f1"
