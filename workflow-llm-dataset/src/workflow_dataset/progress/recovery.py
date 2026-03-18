"""
M27L.1: Stalled-project recovery — match board/outcomes to playbooks, format recovery output.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.progress.board import build_progress_board
from workflow_dataset.progress.playbooks import (
    InterventionPlaybook,
    list_playbooks,
    get_default_playbooks,
)


def _root(repo_root):
    if repo_root is not None:
        return __import__("pathlib").Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return __import__("pathlib").Path(get_repo_root()).resolve()
    except Exception:
        return __import__("pathlib").Path.cwd().resolve()


def match_playbook(
    project_id: str,
    board: dict[str, Any],
    cause_codes: list[str],
    pack_id: str = "",
    goal_hint: str = "",
) -> InterventionPlaybook | None:
    """
    Match first playbook whose trigger_keywords or trigger_cause_codes match.
    cause_codes from board recurring_blockers; pack_id/goal_hint from session/outcomes.
    """
    playbooks = get_default_playbooks()
    cause_set = set(cause_codes)
    hint_lower = (goal_hint or "").lower() + " " + (pack_id or "").lower()
    for pb in playbooks:
        if cause_set and pb.trigger_cause_codes and (cause_set & set(pb.trigger_cause_codes)):
            return pb
        if hint_lower and any(kw in hint_lower for kw in pb.trigger_keywords):
            return pb
    # Default: stalled with no specific match -> first playbook (founder ops as generic ops)
    if board.get("stalled_projects") and project_id in board.get("stalled_projects", []):
        return playbooks[0]
    if board.get("replan_needed_projects") and project_id in board.get("replan_needed_projects", []):
        return playbooks[0]
    return None


def build_stalled_recovery(
    project_id: str = "default",
    repo_root=None,
) -> dict[str, Any]:
    """
    Build stalled-project recovery: board snapshot, matched playbook, recommended actions.
    """
    root = _root(repo_root)
    board = build_progress_board(root)
    cause_codes = [b.get("cause_code", "") for b in board.get("recurring_blockers", []) if b.get("cause_code")]
    pack_id = ""
    goal_hint = ""
    try:
        from workflow_dataset.planner.store import load_current_goal
        goal_hint = load_current_goal(root) or ""
    except Exception:
        pass
    playbook = match_playbook(project_id, board, cause_codes, pack_id=pack_id, goal_hint=goal_hint)
    return {
        "project_id": project_id,
        "board_snapshot": {
            "stalled_projects": board.get("stalled_projects", []),
            "replan_needed_projects": board.get("replan_needed_projects", []),
            "recurring_blockers": board.get("recurring_blockers", [])[:5],
            "project_health": board.get("project_health", {}).get(project_id, "unknown"),
        },
        "matched_playbook": playbook.to_dict() if playbook else None,
        "matched_playbook_id": playbook.playbook_id if playbook else None,
    }


def format_stalled_recovery(recovery: dict[str, Any] | None = None, project_id: str = "default", repo_root=None) -> str:
    """Operator-readable stalled-project recovery output."""
    if recovery is None:
        recovery = build_stalled_recovery(project_id=project_id, repo_root=repo_root)
    lines = [
        "=== Stalled-project recovery: " + recovery.get("project_id", "") + " ===",
        "",
    ]
    snap = recovery.get("board_snapshot", {})
    lines.append("[Board snapshot]")
    lines.append("  stalled: " + ", ".join(snap.get("stalled_projects", []) or ["(none)"]))
    lines.append("  replan_needed: " + ", ".join(snap.get("replan_needed_projects", []) or ["(none)"]))
    lines.append("  project_health: " + snap.get("project_health", "unknown"))
    if snap.get("recurring_blockers"):
        lines.append("  recurring_blockers: " + ", ".join(f"{b.get('cause_code')}({b.get('source_ref')})" for b in snap["recurring_blockers"][:5]))
    lines.append("")

    pb = recovery.get("matched_playbook")
    if not pb:
        lines.append("[Matched playbook] (none — no stall/replan or no matching playbook)")
        lines.append("")
        return "\n".join(lines)

    lines.append("[Matched playbook] " + pb.get("title", pb.get("playbook_id", "")))
    lines.append("  Trigger: " + (pb.get("trigger_pattern", "")[:200] + "…" if len(pb.get("trigger_pattern", "")) > 200 else pb.get("trigger_pattern", "")))
    lines.append("")
    lines.append("[Recommended operator intervention]")
    lines.append("  " + pb.get("operator_intervention", "").replace("\n", "\n  "))
    lines.append("")
    lines.append("[Recommended agent next step]")
    lines.append("  " + pb.get("agent_next_step", ""))
    lines.append("")
    lines.append("[Escalation / defer guidance]")
    lines.append("  " + pb.get("escalation_defer_guidance", ""))
    lines.append("")
    return "\n".join(lines)
