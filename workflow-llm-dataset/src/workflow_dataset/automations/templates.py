"""
M34D.1: Instantiate trigger + workflow from an automation template.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.automations.models import (
    AutomationTemplate,
    TriggerDefinition,
    TriggerKind,
    RecurringWorkflowDefinition,
)
from workflow_dataset.automations.store import get_template, get_trigger, get_workflow
from workflow_dataset.utils.dates import utc_now_iso


def instantiate_from_template(
    template_id: str,
    instance_id: str,
    repo_root: Path | str | None = None,
    overrides: dict[str, Any] | None = None,
) -> tuple[TriggerDefinition, RecurringWorkflowDefinition] | None:
    """
    Create a trigger and workflow pair from a template.
    instance_id is used for both trigger_id and workflow_id (with optional suffix).
    overrides can include trigger_*, workflow_* keys to override template defaults.
    Returns (trigger, workflow) or None if template not found.
    """
    template = get_template(template_id, repo_root=repo_root) if isinstance(template_id, str) else template_id
    if not template or not isinstance(template, AutomationTemplate):
        return None
    overrides = overrides or {}
    now = utc_now_iso()
    trigger_id = overrides.get("trigger_id", instance_id)
    workflow_id = overrides.get("workflow_id", instance_id)

    try:
        kind = TriggerKind(template.default_trigger_kind)
    except ValueError:
        kind = TriggerKind.RECURRING_DIGEST

    trigger = TriggerDefinition(
        trigger_id=trigger_id,
        kind=kind,
        label=overrides.get("trigger_label", template.label or instance_id),
        scope=overrides.get("trigger_scope", template.default_trigger_scope),
        enabled=True,
        condition=dict(template.default_trigger_condition),
        debounce_seconds=overrides.get("debounce_seconds", 0),
        repeat_limit_per_day=overrides.get("repeat_limit_per_day", 0),
        required_policy_trust=overrides.get("required_policy_trust", "simulate"),
        retention_days=overrides.get("retention_days", 30),
        created_utc=now,
        updated_utc=now,
    )
    for k, v in overrides.items():
        if k.startswith("trigger_") and k != "trigger_id" and hasattr(trigger, k[8:]):
            setattr(trigger, k[8:], v)

    workflow = RecurringWorkflowDefinition(
        workflow_id=workflow_id,
        label=overrides.get("workflow_label", template.label or instance_id),
        description=template.description,
        trigger_ids=[trigger_id],
        planner_goal=overrides.get("planner_goal", template.default_planner_goal),
        plan_ref=overrides.get("plan_ref", template.default_plan_ref),
        plan_source="goal" if template.default_planner_goal else "routine",
        execution_mode=overrides.get("execution_mode", template.default_execution_mode),
        stop_conditions=list(template.default_stop_conditions),
        enabled=True,
        created_utc=now,
        updated_utc=now,
    )
    for k, v in overrides.items():
        if k.startswith("workflow_") and k != "workflow_id" and hasattr(workflow, k[9:]):
            setattr(workflow, k[9:], v)

    return trigger, workflow
