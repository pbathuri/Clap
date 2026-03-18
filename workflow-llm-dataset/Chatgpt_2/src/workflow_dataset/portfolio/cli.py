"""
M28: Portfolio CLI helpers — list, status, rank, next, explain, stalled. No auto-run.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.portfolio import (
    build_portfolio,
    rank_active_projects,
    get_next_recommended_project,
    explain_priority,
    format_portfolio_list,
    format_portfolio_status,
    format_stalled_report,
    format_blocked_report,
    report_best_next,
    report_needing_intervention,
    report_ready_for_execution,
)


def cmd_list(repo_root: Path | str | None = None) -> str:
    """Portfolio list: active projects by priority."""
    return format_portfolio_list(repo_root=repo_root)


def cmd_status(repo_root: Path | str | None = None) -> str:
    """Portfolio status: health, ranked list, next, intervention, most blocked, most valuable ready."""
    return format_portfolio_status(repo_root=repo_root)


def cmd_rank(repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """Portfolio rank: return ranked list of project priorities (for CLI to format)."""
    return [p.to_dict() for p in rank_active_projects(repo_root)]


def cmd_next(repo_root: Path | str | None = None) -> dict[str, Any] | None:
    """Next recommended project: project_id, reason, action_hint."""
    rec = get_next_recommended_project(repo_root)
    return rec.to_dict() if rec else None


def cmd_explain(project_id: str, repo_root: Path | str | None = None) -> str:
    """Explain why a project has its priority and rank."""
    return explain_priority(project_id, repo_root)


def cmd_stalled(repo_root: Path | str | None = None) -> str:
    """Stalled projects report."""
    return format_stalled_report(repo_root)


def cmd_blocked(repo_root: Path | str | None = None) -> str:
    """Blocked projects report."""
    return format_blocked_report(repo_root)


# ----- M28D.1 Attention budgets + work windows -----


def cmd_attention_show(repo_root: Path | str | None = None) -> str:
    """Show attention config: budgets, work windows, focus modes. Operator-readable."""
    from workflow_dataset.portfolio.store import load_attention_config
    from workflow_dataset.portfolio.models import AttentionBudget, WorkWindow, FocusMode
    root = Path(repo_root).resolve() if repo_root else None
    config = load_attention_config(root)
    lines = ["=== Attention config (M28D.1) ===", ""]
    budgets = config.get("attention_budgets", [])
    lines.append("[Attention budgets]")
    if not budgets:
        lines.append("  (none; add in data/local/portfolio/attention_config.json)")
    for b in budgets:
        ab = AttentionBudget.from_dict(b) if isinstance(b, dict) else b
        cap = []
        if ab.minutes_per_day is not None:
            cap.append(f"{ab.minutes_per_day} min/day")
        if ab.minutes_per_week is not None:
            cap.append(f"{ab.minutes_per_week} min/week")
        lines.append(f"  {ab.project_id}: " + ", ".join(cap) if cap else f"  {ab.project_id}: (no cap)")
    lines.append("")
    windows = config.get("work_windows", [])
    lines.append("[Work windows]")
    if not windows:
        lines.append("  (none; default 25 min slice)")
    for w in windows:
        ww = WorkWindow.from_dict(w) if isinstance(w, dict) else w
        lines.append(f"  {ww.window_id}: {ww.name}  duration={ww.duration_minutes} min")
    lines.append("")
    modes = config.get("focus_modes", [])
    lines.append("[Focus modes]")
    if not modes:
        lines.append("  (none)")
    for m in modes:
        fm = FocusMode.from_dict(m) if isinstance(m, dict) else m
        active = " (active)" if config.get("active_focus_mode_id") == fm.mode_id else ""
        lines.append(f"  {fm.mode_id}: {fm.name}{active}  rules={fm.switch_rules}")
    lines.append("")
    if config.get("current_window_started_at_iso"):
        lines.append(f"[Current window started] {config['current_window_started_at_iso']}")
    return "\n".join(lines)


def cmd_work_window(current_project: str | None = None, repo_root: Path | str | None = None) -> dict:
    """Work window recommendation: duration, remaining, suggested next. Returns dict for CLI format."""
    from workflow_dataset.portfolio.attention import get_work_window_recommendation
    from workflow_dataset.project_case.store import get_current_project_id
    root = Path(repo_root).resolve() if repo_root else None
    pid = current_project or (get_current_project_id(root) if root else None)
    rec = get_work_window_recommendation(current_project_id=pid, repo_root=root)
    return rec.to_dict()


def cmd_should_switch(current_project: str | None = None, repo_root: Path | str | None = None) -> dict:
    """Should the operator switch project? Rules: window ended, higher_priority_ready. Returns SwitchRecommendation dict."""
    from workflow_dataset.portfolio.attention import should_recommend_switch
    from workflow_dataset.project_case.store import get_current_project_id
    root = Path(repo_root).resolve() if repo_root else None
    pid = current_project or (get_current_project_id(root) if root else None)
    rec = should_recommend_switch(current_project_id=pid, repo_root=root)
    return rec.to_dict()


def cmd_start_window(repo_root: Path | str | None = None) -> str:
    """Start a work window (set current_window_started_at to now). Returns iso timestamp."""
    from workflow_dataset.portfolio.attention import start_work_window
    root = Path(repo_root).resolve() if repo_root else None
    return start_work_window(repo_root=root)
