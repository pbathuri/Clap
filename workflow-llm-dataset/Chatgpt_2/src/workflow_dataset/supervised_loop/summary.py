"""
M27E–M27H: Build cycle summary for CLI and mission control.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.supervised_loop.models import CycleSummary
from workflow_dataset.supervised_loop.store import load_cycle, load_queue, load_handoffs


def build_cycle_summary(
    repo_root: Path | str | None = None,
) -> CycleSummary:
    """Build summary of current cycle, queue, and latest handoff."""
    cycle = load_cycle(repo_root)
    items = load_queue(repo_root)
    handoffs = load_handoffs(repo_root)

    pending = [q for q in items if q.status == "pending"]
    approved = [q for q in items if q.status == "approved"]
    rejected = [q for q in items if q.status == "rejected"]
    deferred = [q for q in items if q.status == "deferred"]

    last_handoff = handoffs[-1] if handoffs else None
    next_label = ""
    next_id = ""
    if pending:
        next_label = pending[0].action.label
        next_id = pending[0].queue_id

    if not cycle:
        return CycleSummary(
            pending_queue_count=len(pending),
            approved_count=len(approved),
            rejected_count=len(rejected),
            deferred_count=len(deferred),
            last_handoff_status=last_handoff.status if last_handoff else "",
            last_run_id=last_handoff.run_id if last_handoff else "",
            next_proposed_action_label=next_label,
            next_proposed_action_id=next_id,
        )

    blocked_reason = ""
    if cycle.blocked_reason:
        blocked_reason = cycle.blocked_reason.reason

    return CycleSummary(
        cycle_id=cycle.cycle_id,
        project_slug=cycle.project_slug,
        goal_text=cycle.goal_text,
        status=cycle.status,
        blocked_reason=blocked_reason,
        pending_queue_count=len(pending),
        approved_count=len(approved),
        rejected_count=len(rejected),
        deferred_count=len(deferred),
        last_handoff_status=last_handoff.status if last_handoff else "",
        last_run_id=cycle.last_run_id or (last_handoff.run_id if last_handoff else ""),
        next_proposed_action_label=next_label,
        next_proposed_action_id=next_id,
    )
