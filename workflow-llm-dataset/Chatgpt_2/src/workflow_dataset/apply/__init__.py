"""
User-approved apply-to-project loop (M8).

Sandbox outputs -> plan -> diff preview -> explicit confirm -> copy to target.
Local-only; audit and rollback supported.
"""

from __future__ import annotations

from workflow_dataset.apply.apply_models import (
    ApplyRequest,
    ApplyPlan,
    ApplyResult,
    RollbackRecord,
)
from workflow_dataset.apply.policy_checks import (
    apply_policy_ok,
    require_confirm,
    target_root_allowed,
)
from workflow_dataset.apply.target_validator import validate_target
from workflow_dataset.apply.copy_planner import build_apply_plan
from workflow_dataset.apply.diff_preview import render_diff_preview
from workflow_dataset.apply.apply_executor import execute_apply
from workflow_dataset.apply.rollback_store import create_rollback_record, perform_rollback
from workflow_dataset.apply.apply_manifest_store import (
    save_apply_request,
    save_apply_plan,
    save_apply_result,
    load_apply_result,
)

__all__ = [
    "ApplyRequest",
    "ApplyPlan",
    "ApplyResult",
    "RollbackRecord",
    "apply_policy_ok",
    "require_confirm",
    "target_root_allowed",
    "validate_target",
    "build_apply_plan",
    "render_diff_preview",
    "execute_apply",
    "create_rollback_record",
    "perform_rollback",
    "save_apply_request",
    "save_apply_plan",
    "save_apply_result",
    "load_apply_result",
]
