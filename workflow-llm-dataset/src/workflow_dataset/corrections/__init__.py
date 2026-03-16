"""
M23M: Operator correction loop + explicit learning updates.
Local, inspectable, reversible; no hidden continual learning.
"""

from workflow_dataset.corrections.schema import (
    CorrectionEvent,
    SOURCE_TYPES,
    CORRECTION_CATEGORIES,
    validate_category_for_source,
)
from workflow_dataset.corrections.store import (
    save_correction,
    list_corrections,
    get_correction,
)
from workflow_dataset.corrections.capture import add_correction
from workflow_dataset.corrections.rules import LEARNING_RULES, BLOCKED_TARGETS
from workflow_dataset.corrections.propose import propose_updates, ProposedUpdate
from workflow_dataset.corrections.updates import (
    UpdateRecord,
    save_update_record,
    load_update_record,
    preview_update,
    apply_update,
    revert_update,
    list_proposed_updates,
)
from workflow_dataset.corrections.history import (
    list_applied_updates,
    list_reverted_updates,
)
from workflow_dataset.corrections.report import corrections_report, format_corrections_report
from workflow_dataset.corrections.eval_bridge import advisory_review_for_corrections

__all__ = [
    "CorrectionEvent",
    "SOURCE_TYPES",
    "CORRECTION_CATEGORIES",
    "validate_category_for_source",
    "save_correction",
    "list_corrections",
    "get_correction",
    "add_correction",
    "LEARNING_RULES",
    "BLOCKED_TARGETS",
    "propose_updates",
    "ProposedUpdate",
    "UpdateRecord",
    "save_update_record",
    "load_update_record",
    "preview_update",
    "apply_update",
    "revert_update",
    "list_proposed_updates",
    "list_applied_updates",
    "list_reverted_updates",
    "corrections_report",
    "format_corrections_report",
    "advisory_review_for_corrections",
]
