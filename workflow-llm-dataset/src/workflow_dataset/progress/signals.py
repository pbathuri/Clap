"""
M27I–M27L: Generate replan signals from outcomes, planner, context drift, teaching.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

from workflow_dataset.progress.models import ReplanSignal
from workflow_dataset.progress.store import save_replan_signals


def _root(repo_root: Path | str | None):
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def generate_replan_signals(
    project_id: str = "default",
    repo_root: Path | str | None = None,
) -> list[ReplanSignal]:
    """
    Produce replan signals from: new blocker (plan or outcomes), capability change (context drift),
    repeated failed action (outcomes), new skill accepted (teaching), context drift affecting goal.
    """
    root = _root(repo_root)
    signals: list[ReplanSignal] = []
    now = utc_now_iso()

    # Plan blocked conditions
    try:
        from workflow_dataset.planner.store import load_latest_plan
        plan = load_latest_plan(root)
        if plan and plan.blocked_conditions:
            for b in plan.blocked_conditions[:3]:
                signals.append(ReplanSignal(
                    signal_type="new_blocker_detected",
                    project_id=project_id,
                    reason=b.reason or "Plan has blocked condition",
                    ref=b.approval_scope or "",
                    evidence=[f"step_index={b.step_index}"],
                    created_at=now,
                ))
    except Exception:
        pass

    # Recurring blockers from outcomes
    try:
        from workflow_dataset.outcomes.patterns import repeated_block_patterns
        blocks = repeated_block_patterns(repo_root=root, min_occurrences=2, limit=10)
        for b in blocks[:5]:
            signals.append(ReplanSignal(
                signal_type="repeated_failed_action",
                project_id=project_id,
                reason=f"Recurring block: {b['cause_code']}",
                ref=b.get("source_ref", ""),
                evidence=[f"count={b.get('count', 0)}"],
                created_at=now,
            ))
    except Exception:
        pass

    # Context drift: newly blocked jobs
    try:
        from workflow_dataset.context.snapshot import load_snapshot
        from workflow_dataset.context.drift import compare_snapshots
        latest = load_snapshot("latest", root)
        previous = load_snapshot("previous", root)
        if latest and previous:
            drift = compare_snapshots(previous, latest)
            if drift.newly_blocked_jobs:
                signals.append(ReplanSignal(
                    signal_type="capability_changed",
                    project_id=project_id,
                    reason="Context: newly blocked jobs",
                    ref=",".join(drift.newly_blocked_jobs[:5]),
                    evidence=drift.newly_blocked_jobs[:5],
                    created_at=now,
                ))
            if drift.newly_recommendable_jobs:
                signals.append(ReplanSignal(
                    signal_type="capability_changed",
                    project_id=project_id,
                    reason="Context: newly recommendable jobs",
                    ref=",".join(drift.newly_recommendable_jobs[:5]),
                    evidence=drift.newly_recommendable_jobs[:5],
                    created_at=now,
                ))
    except Exception:
        pass

    # New skill accepted (teaching)
    try:
        from workflow_dataset.teaching.skill_store import list_skills
        accepted = list_skills(status="accepted", repo_root=root, limit=5)
        if accepted:
            for s in accepted[:2]:
                signals.append(ReplanSignal(
                    signal_type="new_skill_accepted",
                    project_id=project_id,
                    reason="New skill accepted; plan may use it",
                    ref=s.skill_id,
                    evidence=[s.source_type],
                    created_at=now,
                ))
    except Exception:
        pass

    return signals
