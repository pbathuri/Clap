"""
M27E–M27H: Supervised agent loop — plan, propose, approve, execute, repeat.
Human-in-the-loop; no hidden autonomy.
"""

from workflow_dataset.supervised_loop.models import (
    AgentCycle,
    QueuedAction,
    ApprovalQueueItem,
    ExecutionHandoff,
    CycleSummary,
    BlockedCycleReason,
    OperatorPolicy,
    RISK_ORDER,
    LOOP_STATUS_IDLE,
    LOOP_STATUS_PROPOSING,
    LOOP_STATUS_AWAITING_APPROVAL,
    LOOP_STATUS_EXECUTING,
    LOOP_STATUS_COMPLETED,
    LOOP_STATUS_BLOCKED,
)
from workflow_dataset.supervised_loop.store import (
    get_loop_dir,
    save_cycle,
    load_cycle,
    load_queue,
    save_queue,
    load_handoffs,
    append_handoff,
    load_operator_policy,
    save_operator_policy,
)
from workflow_dataset.supervised_loop.next_action import propose_next_actions
from workflow_dataset.supervised_loop.queue import (
    enqueue_proposal,
    list_pending,
    list_pending_sorted,
    list_deferred,
    get_item,
    approve,
    reject,
    defer,
    revisit_deferred,
    approve_batch,
)
from workflow_dataset.supervised_loop.handoff import execute_approved
from workflow_dataset.supervised_loop.summary import build_cycle_summary

__all__ = [
    "AgentCycle",
    "QueuedAction",
    "ApprovalQueueItem",
    "ExecutionHandoff",
    "CycleSummary",
    "BlockedCycleReason",
    "OperatorPolicy",
    "RISK_ORDER",
    "LOOP_STATUS_IDLE",
    "LOOP_STATUS_PROPOSING",
    "LOOP_STATUS_AWAITING_APPROVAL",
    "LOOP_STATUS_EXECUTING",
    "LOOP_STATUS_COMPLETED",
    "LOOP_STATUS_BLOCKED",
    "get_loop_dir",
    "save_cycle",
    "load_cycle",
    "load_queue",
    "save_queue",
    "load_handoffs",
    "append_handoff",
    "load_operator_policy",
    "save_operator_policy",
    "propose_next_actions",
    "enqueue_proposal",
    "list_pending",
    "list_pending_sorted",
    "list_deferred",
    "get_item",
    "approve",
    "reject",
    "defer",
    "revisit_deferred",
    "approve_batch",
    "execute_approved",
    "build_cycle_summary",
]
