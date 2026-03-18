"""
M22A / M23W: Workflow incubator — track, gate, and promote experimental workflows. Local-only; operator-controlled.
"""

from __future__ import annotations

from workflow_dataset.incubator.registry import (
    list_candidates,
    add_candidate,
    get_candidate,
    update_candidate,
    set_promotion_decision,
    mark_stage,
    attach_evidence,
)
from workflow_dataset.incubator.gates import evaluate_gates, promotion_report

__all__ = [
    "list_candidates",
    "add_candidate",
    "get_candidate",
    "update_candidate",
    "set_promotion_decision",
    "mark_stage",
    "attach_evidence",
    "evaluate_gates",
    "promotion_report",
]
