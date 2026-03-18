"""
M27I–M27L: Impact / progress board — active projects, health, stalled vs advancing, replans, blockers, impact, intervention.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.progress.store import list_projects, load_replan_signals, load_prior_plan
from workflow_dataset.progress.signals import generate_replan_signals
from workflow_dataset.progress.recommendation import recommend_replan


def _root(repo_root):
    if repo_root is not None:
        return __import__("pathlib").Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return __import__("pathlib").Path(get_repo_root()).resolve()
    except Exception:
        return __import__("pathlib").Path.cwd().resolve()


def build_progress_board(repo_root=None) -> dict[str, Any]:
    """
    Build progress board: active_projects, project_health, stalled, advancing,
    recent_replans, recurring_blockers, positive_impact, next_intervention.
    """
    root = _root(repo_root)
    board: dict[str, Any] = {
        "active_projects": [],
        "project_health": {},
        "stalled_projects": [],
        "advancing_projects": [],
        "recent_replan_signals": [],
        "recurring_blockers": [],
        "positive_impact_signals": [],
        "next_intervention_candidate": "",
    }
    projects = list_projects(root)
    board["active_projects"] = projects
    if not projects:
        board["active_projects"] = ["default"]

    # Current goal as project context
    try:
        from workflow_dataset.planner.store import load_current_goal, load_latest_plan
        goal = load_current_goal(root)
        plan = load_latest_plan(root)
        for pid in board["active_projects"]:
            health = "unknown"
            if plan and pid == "default":
                if plan.blocked_conditions:
                    health = "blocked"
                elif plan.steps:
                    health = "active"
                else:
                    health = "empty"
            board["project_health"][pid] = health
    except Exception:
        for pid in board["active_projects"]:
            board["project_health"][pid] = "unknown"

    # Replan signals (recent)
    signals = load_replan_signals(root, limit=20)
    board["recent_replan_signals"] = [s.to_dict() if hasattr(s, "to_dict") else s for s in signals[-10:]]

    # Generate fresh signals to detect replan-needed and stalled
    replan_needed = []
    for pid in board["active_projects"][:5]:
        rec = recommend_replan(project_id=pid, repo_root=root)
        if rec.get("recommended"):
            replan_needed.append(pid)
    board["replan_needed_projects"] = replan_needed
    if replan_needed:
        board["next_intervention_candidate"] = replan_needed[0]

    # Recurring blockers from outcomes
    try:
        from workflow_dataset.outcomes.patterns import repeated_block_patterns
        blocks = repeated_block_patterns(repo_root=root, min_occurrences=2, limit=10)
        board["recurring_blockers"] = [{"cause_code": b["cause_code"], "source_ref": b.get("source_ref", ""), "count": b.get("count", 0)} for b in blocks]
    except Exception:
        pass

    # Positive impact: repeated success patterns
    try:
        from workflow_dataset.outcomes.patterns import repeated_success_patterns
        success = repeated_success_patterns(repo_root=root, min_occurrences=2, limit=10)
        board["positive_impact_signals"] = [{"source_ref": s["source_ref"], "pack_id": s.get("pack_id", ""), "count": s.get("count", 0)} for s in success]
    except Exception:
        pass

    # Stalled: sessions with disposition fix/pause and blocked_count > 0
    try:
        from workflow_dataset.outcomes.store import load_outcome_history
        history = load_outcome_history(root, limit=50)
        stalled_sessions = [e for e in history if e.get("disposition") in ("fix", "pause") and e.get("blocked_count", 0) > 0]
        advancing_sessions = [e for e in history if e.get("disposition") == "continue" and e.get("useful_count", 0) > 0]
        board["stalled_projects"] = ["default"] if len(stalled_sessions) >= 2 else []
        board["advancing_projects"] = ["default"] if advancing_sessions else []
        if not board["next_intervention_candidate"] and board["stalled_projects"]:
            board["next_intervention_candidate"] = board["stalled_projects"][0]
    except Exception:
        pass

    return board


def format_progress_board(board: dict[str, Any] | None = None, repo_root=None) -> str:
    """Operator-readable progress board."""
    if board is None:
        board = build_progress_board(repo_root)
    lines = [
        "=== Impact / Progress board ===",
        "",
        "[Active projects] " + ", ".join(board.get("active_projects", [])[:10]),
        "[Project health] " + ", ".join(f"{k}={v}" for k, v in list(board.get("project_health", {}).items())[:10]),
        "",
        "[Stalled] " + ", ".join(board.get("stalled_projects", []) or ["(none)"]),
        "[Advancing] " + ", ".join(board.get("advancing_projects", []) or ["(none)"]),
        "[Replan needed] " + ", ".join(board.get("replan_needed_projects", []) or ["(none)"]),
        "",
        "[Recurring blockers] " + str(len(board.get("recurring_blockers", []))),
        "[Positive impact signals] " + str(len(board.get("positive_impact_signals", []))),
        "",
        "[Next intervention] " + (board.get("next_intervention_candidate") or "(none)"),
        "",
    ]
    if board.get("recent_replan_signals"):
        lines.append("[Recent replan signals]")
        for s in board["recent_replan_signals"][:5]:
            r = s.get("reason", s) if isinstance(s, dict) else getattr(s, "reason", str(s))
            lines.append("  - " + str(r)[:80])
        lines.append("")
    return "\n".join(lines)
