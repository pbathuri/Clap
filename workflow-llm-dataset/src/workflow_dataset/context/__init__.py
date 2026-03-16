"""
M23L: Work state engine + context-aware trigger policies.
Local, inspectable, no background monitoring.
"""

from workflow_dataset.context.config import (
    get_context_root,
    get_snapshots_dir,
    get_latest_snapshot_path,
)
from workflow_dataset.context.work_state import (
    build_work_state,
    WorkState,
    work_state_to_dict,
    work_state_summary_md,
)
from workflow_dataset.context.snapshot import (
    save_snapshot,
    load_snapshot,
    list_snapshots,
)
from workflow_dataset.context.triggers import (
    evaluate_trigger_for_job,
    evaluate_trigger_for_routine,
    evaluate_all_triggers,
    TriggerResult,
)
from workflow_dataset.context.drift import (
    compare_snapshots,
    load_latest_and_previous,
)

__all__ = [
    "get_context_root",
    "get_snapshots_dir",
    "get_latest_snapshot_path",
    "build_work_state",
    "WorkState",
    "work_state_to_dict",
    "work_state_summary_md",
    "save_snapshot",
    "load_snapshot",
    "list_snapshots",
    "evaluate_trigger_for_job",
    "evaluate_trigger_for_routine",
    "evaluate_all_triggers",
    "TriggerResult",
    "compare_snapshots",
    "load_latest_and_previous",
]
