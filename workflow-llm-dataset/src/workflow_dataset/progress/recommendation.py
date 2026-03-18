"""
M27I–M27L: Replan recommendation, plan diff, explain. No auto-replan.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.progress.signals import generate_replan_signals
from workflow_dataset.progress.store import load_prior_plan, load_replan_signals
from workflow_dataset.progress.models import ReplanSignal


def recommend_replan(
    project_id: str = "default",
    repo_root=None,
) -> dict[str, Any]:
    """
    Recommend whether to replan: run signal generation, then decide.
    Returns: recommended (bool), reason (str), signals (list), prior_plan_id, current_plan_id.
    """
    signals = generate_replan_signals(project_id=project_id, repo_root=repo_root)
    recommended = len(signals) > 0
    reason = ""
    if signals:
        reason = "; ".join(s.reason for s in signals[:3])
    prior = load_prior_plan(project_id, repo_root)
    current = None
    try:
        from workflow_dataset.planner.store import load_latest_plan
        current = load_latest_plan(repo_root)
    except Exception:
        pass
    return {
        "recommended": recommended,
        "reason": reason or "No replan signals",
        "signals": [s.to_dict() for s in signals],
        "prior_plan_id": prior.get("plan_id", "") if prior else "",
        "current_plan_id": current.plan_id if current else "",
    }


def compare_plans(
    prior: dict[str, Any],
    new_plan_or_dict: Any,
) -> dict[str, Any]:
    """Compare prior plan vs new plan. Return diff: steps_added, steps_removed, blocked_changed, checkpoints_changed."""
    if hasattr(new_plan_or_dict, "to_dict"):
        new = new_plan_or_dict.to_dict()
    else:
        new = new_plan_or_dict
    prior_steps = {s.get("step_index"): s.get("label") for s in prior.get("steps", [])}
    new_steps = {s.get("step_index"): s.get("label") for s in new.get("steps", [])}
    steps_added = [new_steps[i] for i in new_steps if i not in prior_steps]
    steps_removed = [prior_steps[i] for i in prior_steps if i not in new_steps]
    prior_blocked = [(b.get("reason"), b.get("step_index")) for b in prior.get("blocked_conditions", [])]
    new_blocked = [(b.get("reason"), b.get("step_index")) for b in new.get("blocked_conditions", [])]
    blocked_changed = len(prior_blocked) != len(new_blocked) or set(prior_blocked) != set(new_blocked)
    prior_cp = [(c.get("step_index"), c.get("label")) for c in prior.get("checkpoints", [])]
    new_cp = [(c.get("step_index"), c.get("label")) for c in new.get("checkpoints", [])]
    checkpoints_changed = set(prior_cp) != set(new_cp)
    return {
        "steps_added": steps_added,
        "steps_removed": steps_removed,
        "blocked_changed": blocked_changed,
        "checkpoints_changed": checkpoints_changed,
        "prior_step_count": len(prior.get("steps", [])),
        "new_step_count": len(new.get("steps", [])),
        "prior_blocked_count": len(prior.get("blocked_conditions", [])),
        "new_blocked_count": len(new.get("blocked_conditions", [])),
    }


def explain_replan(signals: list[ReplanSignal] | list[dict]) -> str:
    """Human-readable explanation of why replanning is suggested."""
    if not signals:
        return "No replan signals."
    lines = ["Replan suggested because:"]
    for s in (signals[:5] if isinstance(signals[0], dict) else signals[:5]):
        if isinstance(s, dict):
            lines.append(f"  - {s.get('signal_type', '')}: {s.get('reason', '')}")
        else:
            lines.append(f"  - {s.signal_type}: {s.reason}")
    return "\n".join(lines)


def format_plan_diff(diff: dict[str, Any]) -> str:
    """Human-readable plan diff."""
    lines = [
        "=== Plan diff ===",
        "",
        f"Steps: prior={diff.get('prior_step_count', 0)}  new={diff.get('new_step_count', 0)}",
        f"Blocked: prior={diff.get('prior_blocked_count', 0)}  new={diff.get('new_blocked_count', 0)}",
        "",
    ]
    if diff.get("steps_added"):
        lines.append("Steps added: " + ", ".join(str(x) for x in diff["steps_added"][:10]))
    if diff.get("steps_removed"):
        lines.append("Steps removed: " + ", ".join(str(x) for x in diff["steps_removed"][:10]))
    if diff.get("blocked_changed"):
        lines.append("Blocked conditions changed: yes")
    if diff.get("checkpoints_changed"):
        lines.append("Checkpoints changed: yes")
    lines.append("")
    return "\n".join(lines)
