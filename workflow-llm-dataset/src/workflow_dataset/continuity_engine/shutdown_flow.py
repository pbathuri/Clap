"""
M36I–M36L: Shutdown / wrap-up flow — completed, unresolved, carry-forward, tomorrow start, blocked.
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

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:14]

from workflow_dataset.continuity_engine.models import (
    ShutdownSummary,
    CarryForwardItem,
    NextSessionRecommendation,
)
from workflow_dataset.continuity_engine.store import (
    save_last_shutdown,
    save_carry_forward,
    save_next_session_recommendation,
)
from workflow_dataset.continuity_engine.carry_forward_policy import (
    apply_carry_forward_policy,
    build_next_day_operating_recommendation,
)
from workflow_dataset.workday.store import load_workday_state, current_day_id
from workflow_dataset.workday.surface import build_daily_operating_surface


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_shutdown_summary(
    repo_root: Path | str | None = None,
    queue_limit: int = 30,
) -> ShutdownSummary:
    """Build shutdown summary: completed, unresolved, carry-forward, tomorrow start, blocked."""
    root = _root(repo_root)
    now = utc_now_iso()
    day_id = current_day_id()
    summary_id = stable_id("shutdown", day_id, now[:16], prefix="shutdown_")

    record = load_workday_state(root)
    completed_work: list[str] = []
    if record.transition_history:
        completed_work.append(f"Workday states: {', '.join(t.to_state for t in record.transition_history[-5:])}")
    completed_work.append(f"Day {day_id} — final state: {record.state}")

    unresolved_items: list[dict[str, Any]] = []
    blocked_or_high_risk: list[str] = []
    queue_items: list[Any] = []

    try:
        from workflow_dataset.unified_queue import build_unified_queue
        queue_items = build_unified_queue(repo_root=root, limit=queue_limit)
        for i in queue_items[:15]:
            unresolved_items.append({
                "item_id": getattr(i, "item_id", ""),
                "label": (getattr(i, "label", "") or getattr(i, "summary", ""))[:80],
                "source": getattr(getattr(i, "source_subsystem", None), "value", ""),
            })
            if getattr(i, "actionability_class", None) and str(getattr(i, "actionability_class", "")).endswith("BLOCKED"):
                blocked_or_high_risk.append(getattr(i, "label", "")[:60])
    except Exception:
        pass

    # M36L.1: Apply carry-forward policy -> urgent, optional, automated_follow_up
    policy_output = apply_carry_forward_policy(queue_items, repo_root=root)
    cf_items_with_class = (
        policy_output.urgent_items
        + policy_output.optional_items
        + policy_output.automated_follow_up_items
    )
    carry_forward_items = [
        {
            "kind": c.kind,
            "carry_forward_class": c.carry_forward_class,
            "label": c.label,
            "ref": c.ref,
            "command": c.command,
        }
        for c in cf_items_with_class
    ]

    tomorrow_start = "Resume from queue and inbox"
    tomorrow_first_action = "workflow-dataset continuity morning"
    try:
        surf = build_daily_operating_surface(root)
        if surf.active_project_id:
            tomorrow_start = f"Project: {surf.active_project_id}"
            tomorrow_first_action = "workflow-dataset workspace open"
    except Exception:
        pass

    readiness = "ready"
    if blocked_or_high_risk:
        readiness = "has_blocked"
    elif unresolved_items:
        readiness = "has_unresolved"

    summary = ShutdownSummary(
        summary_id=summary_id,
        generated_at_utc=now,
        day_id=day_id,
        completed_work=completed_work,
        unresolved_items=unresolved_items,
        carry_forward_items=carry_forward_items,
        tomorrow_likely_start=tomorrow_start,
        tomorrow_first_action=tomorrow_first_action,
        blocked_or_high_risk=blocked_or_high_risk[:10],
        end_of_day_readiness=readiness,
    )
    save_last_shutdown(summary, root)

    save_carry_forward(cf_items_with_class, root)

    first_label, first_cmd, rationale = build_next_day_operating_recommendation(
        policy_output, tomorrow_start=tomorrow_start, repo_root=root
    )
    if tomorrow_first_action == "workflow-dataset workspace open" and not policy_output.urgent_items:
        first_label = "Resume project"
        first_cmd = tomorrow_first_action
        rationale = [f"Active project: {tomorrow_start}"] + rationale
    operating_mode = "review_first" if policy_output.urgent_items else "startup"

    rec = NextSessionRecommendation(
        generated_at_utc=now,
        day_id=day_id,
        likely_start_context=tomorrow_start,
        first_action_label=first_label,
        first_action_command=first_cmd,
        carry_forward_count=len(cf_items_with_class),
        blocked_count=len(blocked_or_high_risk),
        urgent_carry_forward_count=len(policy_output.urgent_items),
        optional_carry_forward_count=len(policy_output.optional_items),
        automated_follow_up_count=len(policy_output.automated_follow_up_items),
        operating_mode=operating_mode,
        rationale_lines=rationale,
    )
    save_next_session_recommendation(rec, root)

    return summary


def build_carry_forward_list(repo_root: Path | str | None = None) -> list[CarryForwardItem]:
    """Return current carry-forward items from store."""
    from workflow_dataset.continuity_engine.store import load_carry_forward
    return load_carry_forward(repo_root=repo_root)
