"""
M47H.1: Fast paths for the most repeated vertical workflows.
Registry of compressed paths (one or few steps) keyed by workflow_id.
"""

from __future__ import annotations

from workflow_dataset.vertical_speed.models import FastPath


def _builtin_fast_paths() -> list[FastPath]:
    """Built-in fast paths aligned with list_frequent_workflows workflow kinds."""
    return [
        FastPath(
            path_id="morning_entry_fast",
            workflow_id="morning_entry_first_action",
            label="Morning entry → first action (fast)",
            description="Single continuity morning + first recommended action.",
            compressed_steps=["continuity morning", "run first recommended action"],
            single_command="workflow-dataset vertical-speed repeat-value (use morning prefill)",
            step_count_before=4,
            step_count_after=2,
            precondition="Day started; continuity morning available.",
        ),
        FastPath(
            path_id="queue_item_to_action_fast",
            workflow_id="queue_item_to_action",
            label="Queue item → action (fast)",
            description="Route top queue item to single command without opening card.",
            compressed_steps=["workflow-dataset vertical-speed action-route --item <item_id>"],
            single_command="workflow-dataset vertical-speed action-route",
            step_count_before=4,
            step_count_after=1,
            precondition="Queue has at least one item.",
        ),
        FastPath(
            path_id="review_item_to_decision_fast",
            workflow_id="review_item_to_decision",
            label="Review item → decision (fast)",
            description="Grouped review recommendation: one command for batch apply/defer.",
            compressed_steps=["workflow-dataset vertical-speed action-route (review mode)"],
            single_command="workflow-dataset vertical-speed repeat-value (grouped_review command)",
            step_count_before=4,
            step_count_after=2,
            precondition="Inbox/review has items; grouped recommendation available.",
        ),
        FastPath(
            path_id="continuity_resume_fast",
            workflow_id="continuity_resume_to_context",
            label="Continuity resume → context (fast)",
            description="Resume via continuity morning first-command prefill.",
            compressed_steps=["continuity morning", "run prefilled first action"],
            single_command="workflow-dataset vertical-speed repeat-value (morning prefill)",
            step_count_before=3,
            step_count_after=1,
            precondition="Continuity carry-forward or morning available.",
        ),
        # operator_routine_to_execution and vertical_draft_to_completion: no fast path yet (still need work)
    ]


_FAST_PATHS: list[FastPath] | None = None


def list_fast_paths() -> list[FastPath]:
    """Return all registered fast paths."""
    global _FAST_PATHS
    if _FAST_PATHS is None:
        _FAST_PATHS = _builtin_fast_paths()
    return list(_FAST_PATHS)


def get_fast_path_by_workflow_id(workflow_id: str) -> FastPath | None:
    """Return the fast path for the given workflow_id, or None."""
    for p in list_fast_paths():
        if p.workflow_id == workflow_id:
            return p
    return None


def get_fast_path_by_path_id(path_id: str) -> FastPath | None:
    """Return the fast path with the given path_id, or None."""
    for p in list_fast_paths():
        if p.path_id == path_id:
            return p
    return None
