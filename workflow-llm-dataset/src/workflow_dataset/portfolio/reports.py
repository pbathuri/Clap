"""
M28: Portfolio reports — active by priority, stalled, blocked, best next, needing intervention, ready for execution.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.portfolio.scheduler import build_portfolio, rank_active_projects
from workflow_dataset.portfolio.models import Portfolio, PortfolioEntry


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def report_active_by_priority(repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """Active projects ordered by priority rank. Each: project_id, title, rank_index, tier, health_label, is_current."""
    portfolio = build_portfolio(repo_root)
    return [
        {
            "project_id": e.project_id,
            "title": e.title,
            "rank_index": e.priority.rank_index,
            "tier": e.priority.tier,
            "health_label": e.health_label,
            "is_current": e.is_current,
        }
        for e in portfolio.entries
    ]


def report_stalled(repo_root: Path | str | None = None) -> list[PortfolioEntry]:
    """Projects marked stalled (from progress board)."""
    portfolio = build_portfolio(repo_root)
    return [e for e in portfolio.entries if e.is_stalled]


def report_blocked(repo_root: Path | str | None = None) -> list[PortfolioEntry]:
    """Projects that are blocked (no unblocked work)."""
    portfolio = build_portfolio(repo_root)
    return [e for e in portfolio.entries if e.is_blocked]


def report_best_next(repo_root: Path | str | None = None) -> dict[str, Any] | None:
    """Best next project to advance: project_id, reason, action_hint."""
    portfolio = build_portfolio(repo_root)
    rec = portfolio.next_recommended_project
    if not rec:
        return None
    return {
        "project_id": rec.project_id,
        "reason": rec.reason,
        "action_hint": rec.action_hint,
        "priority_tier": rec.priority_tier,
    }


def report_needing_intervention(repo_root: Path | str | None = None) -> list[PortfolioEntry]:
    """Projects needing operator intervention (stalled or top intervention candidate)."""
    portfolio = build_portfolio(repo_root)
    return [e for e in portfolio.entries if e.needs_intervention]


def report_ready_for_execution(repo_root: Path | str | None = None) -> list[PortfolioEntry]:
    """Projects with unblocked work ready to execute."""
    portfolio = build_portfolio(repo_root)
    return [e for e in portfolio.entries if e.is_ready_for_execution]


def format_portfolio_status(portfolio: Portfolio | None = None, repo_root: Path | str | None = None) -> str:
    """Operator-readable portfolio status: health, ranked list, next, intervention, blocked, ready."""
    if portfolio is None:
        portfolio = build_portfolio(repo_root)
    lines = [
        "=== Portfolio status ===",
        "",
        f"Health: {portfolio.health.total_active} active  " + "  ".join(portfolio.health.labels),
        "",
        "[Ranked active]",
    ]
    for e in portfolio.entries[:20]:
        cur = " (current)" if e.is_current else ""
        lines.append(f"  #{e.priority.rank_index}  {e.project_id}  {e.title or '—'}  tier={e.priority.tier}  health={e.health_label}{cur}")
    lines.append("")
    if portfolio.next_recommended_project:
        r = portfolio.next_recommended_project
        lines.append(f"[Next recommended] {r.project_id}  {r.action_hint}  — {r.reason[:80]}")
    else:
        lines.append("[Next recommended] (none or all deferred)")
    lines.append("")
    if portfolio.top_intervention:
        t = portfolio.top_intervention
        lines.append(f"[Top intervention] {t.project_id}  — {t.reason[:60]}")
    else:
        lines.append("[Top intervention] (none)")
    if portfolio.most_blocked_project_id:
        lines.append(f"[Most blocked] {portfolio.most_blocked_project_id}")
    if portfolio.most_valuable_ready_project_id:
        lines.append(f"[Most valuable ready] {portfolio.most_valuable_ready_project_id}")
    lines.append("")
    return "\n".join(lines)


def format_portfolio_list(portfolio: Portfolio | None = None, repo_root: Path | str | None = None) -> str:
    """Short list: rank, project_id, title, tier, health."""
    if portfolio is None:
        portfolio = build_portfolio(repo_root)
    lines = ["=== Portfolio (active by priority) ===", ""]
    for e in portfolio.entries:
        cur = " (current)" if e.is_current else ""
        lines.append(f"  #{e.priority.rank_index}  {e.project_id}  {e.title or '—'}  {e.priority.tier}  {e.health_label}{cur}")
    if not portfolio.entries:
        lines.append("  (no active projects; create with projects create --id <id>)")
    return "\n".join(lines)


def format_stalled_report(repo_root: Path | str | None = None) -> str:
    """Stalled projects only."""
    stalled = report_stalled(repo_root)
    lines = ["=== Stalled projects ===", ""]
    for e in stalled:
        lines.append(f"  {e.project_id}  {e.title or '—'}  {e.priority.blocker.blocked_reason_summary[:60] or '—'}")
    if not stalled:
        lines.append("  (none)")
    return "\n".join(lines)


def format_blocked_report(repo_root: Path | str | None = None) -> str:
    """Blocked projects only."""
    blocked = report_blocked(repo_root)
    lines = ["=== Blocked projects ===", ""]
    for e in blocked:
        lines.append(f"  {e.project_id}  {e.title or '—'}  goals_blocked={e.priority.blocker.blocked_goals_count}")
    if not blocked:
        lines.append("  (none)")
    return "\n".join(lines)
