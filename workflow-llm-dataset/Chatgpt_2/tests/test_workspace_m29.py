"""
M29: Unified workspace shell + navigation state. Tests for view model, state, home, navigation, empty-state.
"""

from __future__ import annotations

from pathlib import Path

import pytest


def test_workspace_models_roundtrip():
    """Workspace models to_dict/from_dict roundtrip."""
    from workflow_dataset.workspace.models import (
        ActiveWorkContext,
        NavigationState,
        WorkspaceHomeSnapshot,
        WorkspaceArea,
    )
    ctx = ActiveWorkContext(
        active_project_id="p1",
        active_project_title="Proj 1",
        active_goal_text="Goal A",
        active_session_id="s1",
        queued_approvals_count=2,
        next_recommended_action="advance",
        next_recommended_detail="Run agent next",
    )
    back = ActiveWorkContext.from_dict(ctx.to_dict())
    assert back.active_project_id == ctx.active_project_id
    assert back.next_recommended_action == ctx.next_recommended_action

    nav = NavigationState(
        current_view="project",
        current_project_id="p1",
        current_session_id="s1",
        breadcrumbs=["Home", "Portfolio", "p1"],
        quick_actions=[{"label": "Report", "command": "workflow-dataset projects report --id p1"}],
    )
    back_nav = NavigationState.from_dict(nav.to_dict())
    assert back_nav.current_view == nav.current_view
    assert back_nav.breadcrumbs == nav.breadcrumbs

    area = WorkspaceArea("projects", "Projects", "List projects", "workflow-dataset projects list", 5)
    assert area.area_id == "projects" and area.count == 5


def test_workspace_views_constants():
    """WORKSPACE_VIEWS and WORKSPACE_AREAS are non-empty and include home."""
    from workflow_dataset.workspace.models import WORKSPACE_VIEWS, WORKSPACE_AREAS
    assert "home" in WORKSPACE_VIEWS
    assert "portfolio" in WORKSPACE_VIEWS
    assert "project" in WORKSPACE_VIEWS
    assert "session" in WORKSPACE_VIEWS
    assert "home" in WORKSPACE_AREAS
    assert "portfolio" in WORKSPACE_AREAS


def test_build_active_work_context_empty(tmp_path):
    """build_active_work_context on empty repo returns valid context (no project/session)."""
    from workflow_dataset.workspace.state import build_active_work_context
    ctx = build_active_work_context(tmp_path)
    assert hasattr(ctx, "active_project_id")
    assert hasattr(ctx, "active_session_id")
    assert hasattr(ctx, "queued_approvals_count")
    assert hasattr(ctx, "next_recommended_action")
    assert ctx.active_project_id is None or ctx.active_project_id == ""


def test_build_navigation_state_transitions(tmp_path):
    """build_navigation_state produces correct breadcrumbs for view transitions."""
    from workflow_dataset.workspace.state import build_navigation_state
    nav_home = build_navigation_state("home", "", "", tmp_path)
    assert nav_home.current_view == "home"
    assert "Home" in nav_home.breadcrumbs

    nav_portfolio = build_navigation_state("portfolio", "", "", tmp_path)
    assert nav_portfolio.breadcrumbs == ["Home", "Portfolio"]

    nav_project = build_navigation_state("project", "founder_case_alpha", "", tmp_path)
    assert "founder_case_alpha" in nav_project.breadcrumbs
    assert len(nav_project.quick_actions) >= 1


def test_build_workspace_home_snapshot_empty(tmp_path):
    """build_workspace_home_snapshot on empty repo returns snapshot with areas and summaries."""
    from workflow_dataset.workspace.state import build_workspace_home_snapshot
    snap = build_workspace_home_snapshot(tmp_path)
    assert snap.context is not None
    assert snap.navigation is not None
    assert len(snap.areas) >= 8
    assert snap.approval_queue_summary is not None
    assert snap.blocked_summary is not None
    assert snap.updated_at_iso


def test_format_workspace_home(tmp_path):
    """format_workspace_home returns string with Workspace Home and sections."""
    from workflow_dataset.workspace.home import format_workspace_home
    text = format_workspace_home(repo_root=tmp_path)
    assert "Workspace Home" in text
    assert "Where you are" in text or "Project:" in text
    assert "Areas" in text
    assert "workflow-dataset workspace" in text


def test_resolve_view_target(tmp_path):
    """resolve_view_target returns view, navigation, and suggested_commands."""
    from workflow_dataset.workspace.navigation import resolve_view_target
    out = resolve_view_target("home", repo_root=tmp_path)
    assert out["view"] == "home"
    assert "navigation" in out
    assert "suggested_commands" in out
    assert isinstance(out["suggested_commands"], list)

    out_proj = resolve_view_target("project", project_id="p1", repo_root=tmp_path)
    assert out_proj["view"] == "project"
    assert any("projects" in c for c in out_proj["suggested_commands"])


def test_deep_link_commands(tmp_path):
    """deep_link_commands returns list of commands for view transition."""
    from workflow_dataset.workspace.navigation import deep_link_commands
    cmds = deep_link_commands("home", "project", project_id="p1", repo_root=tmp_path)
    assert isinstance(cmds, list)
    assert any("project" in c for c in cmds)

    cmds_home = deep_link_commands("portfolio", "home", repo_root=tmp_path)
    assert any("workspace home" in c for c in cmds_home)


def test_cmd_context_no_project_no_session(tmp_path):
    """cmd_context with no project/session returns dict with null/empty ids."""
    from workflow_dataset.workspace.cli import cmd_context
    out = cmd_context(repo_root=tmp_path)
    assert "active_project_id" in out
    assert "active_session_id" in out
    assert "navigation" in out
    assert "next_action" in out


def test_cmd_next_empty(tmp_path):
    """cmd_next returns dict with next_action and optional portfolio fields."""
    from workflow_dataset.workspace.cli import cmd_next
    out = cmd_next(repo_root=tmp_path)
    assert "next_action" in out
    assert "next_detail" in out


# ----- M29D.1 Workspace presets -----


def test_preset_get_and_list():
    """get_preset returns preset by id (hyphen or underscore); list_preset_ids returns all."""
    from workflow_dataset.workspace.presets import get_preset, list_preset_ids, PRESET_FOUNDER_OPERATOR
    ids = list_preset_ids()
    assert PRESET_FOUNDER_OPERATOR in ids
    assert "analyst" in ids
    assert "developer" in ids
    assert "document_heavy" in ids
    p = get_preset("founder-operator")
    assert p is not None
    assert p.preset_id == PRESET_FOUNDER_OPERATOR
    assert p.recommended_first_view == "portfolio"
    assert get_preset("unknown") is None


def test_preset_model_roundtrip():
    """WorkspacePreset to_dict/from_dict roundtrip."""
    from workflow_dataset.workspace.models import WorkspacePreset
    from workflow_dataset.workspace.presets import get_preset
    p = get_preset("analyst")
    assert p is not None
    back = WorkspacePreset.from_dict(p.to_dict())
    assert back.preset_id == p.preset_id
    assert back.recommended_first_view == p.recommended_first_view
    assert len(back.default_quick_actions) == len(p.default_quick_actions)


def test_format_workspace_home_with_preset(tmp_path):
    """format_workspace_home with preset_id includes preset label and role-specific quick actions."""
    from workflow_dataset.workspace.home import format_workspace_home
    text = format_workspace_home(repo_root=tmp_path, preset_id="founder-operator")
    assert "Workspace Home" in text
    assert "Founder" in text or "Operator" in text
    assert "Recommended first view" in text
    assert "portfolio" in text
    assert "mission-control" in text
    assert "agent-loop queue" in text


def test_founder_preset_section_order(tmp_path):
    """Founder preset shows Approvals before Top priority."""
    from workflow_dataset.workspace.home import format_workspace_home
    text = format_workspace_home(repo_root=tmp_path, preset_id="founder_operator")
    idx_approvals = text.find("[Approvals]")
    idx_top = text.find("[Top priority")
    assert idx_approvals >= 0 and idx_top >= 0
    assert idx_approvals < idx_top


def test_cmd_presets_list():
    """cmd_presets_list returns list of dicts with preset_id, label, description, recommended_first_view."""
    from workflow_dataset.workspace.cli import cmd_presets_list
    out = cmd_presets_list()
    assert len(out) >= 4
    for p in out:
        assert "preset_id" in p and "label" in p and "recommended_first_view" in p
    ids = [x["preset_id"] for x in out]
    assert "founder_operator" in ids
    assert "analyst" in ids


def test_workspace_views_include_integrated_ask_timeline_inbox():
    """M29 integration: WORKSPACE_VIEWS includes ask, timeline, inbox."""
    from workflow_dataset.workspace.models import WORKSPACE_VIEWS
    assert "ask" in WORKSPACE_VIEWS
    assert "timeline" in WORKSPACE_VIEWS
    assert "inbox" in WORKSPACE_VIEWS


def test_resolve_view_target_ask_timeline_inbox(tmp_path):
    """M29 integration: resolve_view_target for ask, timeline, inbox returns suggested_commands."""
    from workflow_dataset.workspace.navigation import resolve_view_target
    out_ask = resolve_view_target("ask", repo_root=tmp_path)
    assert out_ask["view"] == "ask"
    assert any("ask" in c for c in out_ask["suggested_commands"])
    out_timeline = resolve_view_target("timeline", repo_root=tmp_path)
    assert out_timeline["view"] == "timeline"
    assert any("timeline" in c for c in out_timeline["suggested_commands"])
    out_inbox = resolve_view_target("inbox", repo_root=tmp_path)
    assert out_inbox["view"] == "inbox"
    assert any("inbox" in c for c in out_inbox["suggested_commands"])
