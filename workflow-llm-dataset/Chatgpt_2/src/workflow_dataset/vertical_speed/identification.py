"""
M47E–M47H: Identify high-frequency workflows for the chosen vertical.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.vertical_speed.models import FrequentWorkflow, WorkflowKind


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _active_vertical_pack_id(repo_root: Path | str | None) -> str:
    try:
        from workflow_dataset.vertical_packs.store import get_active_pack
        active = get_active_pack(repo_root)
        return active.get("active_curated_pack_id", "") or "founder_operator_core"
    except Exception:
        return "founder_operator_core"


def list_frequent_workflows(
    repo_root: Path | str | None = None,
    vertical_pack_id: str | None = None,
) -> list[FrequentWorkflow]:
    """
    Return high-frequency workflows for the (active or specified) vertical.
    Uses vertical pack core_workflow_path, required_surfaces, morning flow, queue.
    """
    root = _root(repo_root)
    pack_id = vertical_pack_id or _active_vertical_pack_id(root)
    out: list[FrequentWorkflow] = []

    try:
        from workflow_dataset.vertical_packs.registry import get_curated_pack
        pack = get_curated_pack(pack_id)
    except Exception:
        pack = None

    # Morning entry → first action (daily)
    morning_entry = FrequentWorkflow(
        workflow_id="morning_entry_first_action",
        kind=WorkflowKind.morning_entry_first_action,
        label="Morning entry → first action",
        description="Start day: change since last, top queue, first recommended action.",
        vertical_pack_id=pack_id,
        estimated_frequency="daily",
        entry_point="continuity morning or day status",
        typical_steps=["day start or resume", "continuity morning", "open queue or inbox", "first action"],
        current_step_count=4,
        suggested_step_count=2,
    )
    out.append(morning_entry)

    # Queue item → action
    queue_to_action = FrequentWorkflow(
        workflow_id="queue_item_to_action",
        kind=WorkflowKind.queue_item_to_action,
        label="Queue item → action",
        description="From queue item to execution or handoff (approval, review, executor).",
        vertical_pack_id=pack_id,
        estimated_frequency="multiple_per_day",
        entry_point="queue view",
        typical_steps=["queue view", "select item", "accept card or open handoff", "execute or review"],
        current_step_count=4,
        suggested_step_count=2,
    )
    out.append(queue_to_action)

    # Review item → decision
    review_to_decision = FrequentWorkflow(
        workflow_id="review_item_to_decision",
        kind=WorkflowKind.review_item_to_decision,
        label="Review item → decision",
        description="Inbox or approval item to apply/reject/defer.",
        vertical_pack_id=pack_id,
        estimated_frequency="multiple_per_day",
        entry_point="inbox list or review studio",
        typical_steps=["open inbox/review", "select item", "review context", "apply or defer"],
        current_step_count=4,
        suggested_step_count=2,
    )
    out.append(review_to_decision)

    # Continuity resume → context
    resume_to_context = FrequentWorkflow(
        workflow_id="continuity_resume_to_context",
        kind=WorkflowKind.continuity_resume_to_context,
        label="Continuity resume → correct context",
        description="Reconnect to interrupted work and next step.",
        vertical_pack_id=pack_id,
        estimated_frequency="daily",
        entry_point="continuity carry-forward or morning",
        typical_steps=["continuity morning or carry-forward", "read recommendation", "run first action command"],
        current_step_count=3,
        suggested_step_count=1,
    )
    out.append(resume_to_context)

    # Operator routine → execution (founder: morning_ops, weekly_status)
    routine_workflow_ids = ["morning_ops", "weekly_status_from_notes", "weekly_status"]
    if pack:
        cw = getattr(pack, "core_workflow_path", None)
        if cw and getattr(cw, "workflow_ids", None):
            routine_workflow_ids = cw.workflow_ids[:5]
    operator_routine = FrequentWorkflow(
        workflow_id="operator_routine_to_execution",
        kind=WorkflowKind.operator_routine_to_execution,
        label="Operator routine → execution",
        description="Run trusted routine (e.g. morning_ops, weekly_status) with approval/review.",
        vertical_pack_id=pack_id,
        estimated_frequency="daily",
        entry_point="copilot recommend or job run",
        typical_steps=["find routine", "approve or confirm", "run", "review outcome"],
        current_step_count=4,
        suggested_step_count=2,
    )
    out.append(operator_routine)

    # Vertical draft/handoff → completion
    draft_to_done = FrequentWorkflow(
        workflow_id="vertical_draft_to_completion",
        kind=WorkflowKind.vertical_draft_to_completion,
        label="Draft/handoff → completion",
        description="From draft or handoff to applied/completed.",
        vertical_pack_id=pack_id,
        estimated_frequency="multiple_per_day",
        entry_point="in-flow or action card",
        typical_steps=["open draft/card", "review", "apply or execute handoff"],
        current_step_count=3,
        suggested_step_count=2,
    )
    out.append(draft_to_done)

    return out


def get_top_workflows(
    limit: int = 5,
    repo_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Return top N frequent workflows as dicts for reports."""
    workflows = list_frequent_workflows(repo_root=repo_root)
    return [w.to_dict() for w in workflows[:limit]]
