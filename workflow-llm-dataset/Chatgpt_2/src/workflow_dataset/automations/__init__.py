"""
M34A–M34D (+ M34D.1): Trigger engine, recurring workflows, automation templates, guardrail profiles.

Bounded automation triggers and reusable recurring workflow definitions.
Templates (morning digest, blocked-work follow-up, approval sweep, end-of-day wrap) and
guardrail profiles (strict, supervised, bounded-recurring) with explicit suppression rules.
"""

from workflow_dataset.automations.models import (
    TriggerKind,
    TriggerDefinition,
    RecurringWorkflowDefinition,
    TriggerMatchResult,
    TriggerEvaluationSummary,
    AutomationTemplateKind,
    AutomationTemplate,
    GuardrailProfileKind,
    GuardrailProfile,
    SuppressionRule,
)
from workflow_dataset.automations.store import (
    list_trigger_ids,
    get_trigger,
    save_trigger,
    list_workflow_ids,
    get_workflow,
    save_workflow,
    list_template_ids,
    get_template,
    save_template,
    list_guardrail_profile_ids,
    get_guardrail_profile,
    save_guardrail_profile,
    get_active_guardrail_profile,
)
from workflow_dataset.automations.evaluate import (
    evaluate_active_triggers,
    explain_trigger_match,
    list_blocked_suppressed_triggers,
    match_triggers_to_workflows,
)
from workflow_dataset.automations.templates import instantiate_from_template

__all__ = [
    "TriggerKind",
    "TriggerDefinition",
    "RecurringWorkflowDefinition",
    "TriggerMatchResult",
    "TriggerEvaluationSummary",
    "AutomationTemplateKind",
    "AutomationTemplate",
    "GuardrailProfileKind",
    "GuardrailProfile",
    "SuppressionRule",
    "list_trigger_ids",
    "get_trigger",
    "save_trigger",
    "list_workflow_ids",
    "get_workflow",
    "save_workflow",
    "list_template_ids",
    "get_template",
    "save_template",
    "list_guardrail_profile_ids",
    "get_guardrail_profile",
    "save_guardrail_profile",
    "get_active_guardrail_profile",
    "evaluate_active_triggers",
    "explain_trigger_match",
    "list_blocked_suppressed_triggers",
    "match_triggers_to_workflows",
    "instantiate_from_template",
]
