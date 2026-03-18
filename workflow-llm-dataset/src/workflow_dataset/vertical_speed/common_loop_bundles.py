"""
M47H.1: Common-loop bundles — groups of repeated flows that form a loop.
"""

from __future__ import annotations

from workflow_dataset.vertical_speed.models import CommonLoopBundle


def _builtin_bundles() -> list[CommonLoopBundle]:
    """Built-in common-loop bundles."""
    return [
        CommonLoopBundle(
            bundle_id="morning_loop",
            label="Morning loop",
            description="Day start → continuity morning → first action; repeat daily.",
            workflow_ids=["morning_entry_first_action", "continuity_resume_to_context"],
            step_ids=["day_start", "continuity_morning", "first_action"],
            single_entry_command="continuity morning (or vertical-speed repeat-value morning prefill)",
            fast_path_ids=["morning_entry_fast", "continuity_resume_fast"],
        ),
        CommonLoopBundle(
            bundle_id="queue_to_action_loop",
            label="Queue-to-action loop",
            description="Queue view → select item → action; repeat per item.",
            workflow_ids=["queue_item_to_action"],
            step_ids=["queue_view", "select_item", "action_route"],
            single_entry_command="workflow-dataset vertical-speed action-route",
            fast_path_ids=["queue_item_to_action_fast"],
        ),
        CommonLoopBundle(
            bundle_id="review_batch_loop",
            label="Review batch loop",
            description="Inbox/review → grouped items → apply/defer; repeat per batch.",
            workflow_ids=["review_item_to_decision"],
            step_ids=["open_review", "grouped_recommendation", "apply_or_defer"],
            single_entry_command="workflow-dataset vertical-speed repeat-value (grouped_review)",
            fast_path_ids=["review_item_to_decision_fast"],
        ),
        CommonLoopBundle(
            bundle_id="operator_routine_loop",
            label="Operator routine loop",
            description="Find routine → approve → run → review outcome; still need work.",
            workflow_ids=["operator_routine_to_execution"],
            step_ids=["find_routine", "approve", "run", "review"],
            single_entry_command="",
            fast_path_ids=[],
        ),
    ]


_BUNDLES: list[CommonLoopBundle] | None = None


def list_common_loop_bundles() -> list[CommonLoopBundle]:
    """Return all registered common-loop bundles."""
    global _BUNDLES
    if _BUNDLES is None:
        _BUNDLES = _builtin_bundles()
    return list(_BUNDLES)


def get_common_loop_bundle(bundle_id: str) -> CommonLoopBundle | None:
    """Return the bundle with the given bundle_id, or None."""
    for b in list_common_loop_bundles():
        if b.bundle_id == bundle_id:
            return b
    return None


def get_bundles_for_workflow(workflow_id: str) -> list[CommonLoopBundle]:
    """Return bundles that include the given workflow_id."""
    return [b for b in list_common_loop_bundles() if workflow_id in b.workflow_ids]
