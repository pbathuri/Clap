"""
M34A–M34D: Trigger engine + recurring workflow definitions.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.automations.models import (
    TriggerKind,
    TriggerDefinition,
    RecurringWorkflowDefinition,
    TriggerMatchResult,
    TriggerEvaluationSummary,
    AutomationTemplate,
    AutomationTemplateKind,
    GuardrailProfile,
    GuardrailProfileKind,
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


def test_trigger_definition_model():
    """TriggerDefinition has expected fields and kinds."""
    t = TriggerDefinition(
        trigger_id="t1",
        kind=TriggerKind.TIME_BASED,
        label="Daily 09:00",
        condition={"cron_expression": "0 9 * * *"},
        enabled=True,
    )
    assert t.trigger_id == "t1"
    assert t.kind == TriggerKind.TIME_BASED
    assert t.condition.get("cron_expression") == "0 9 * * *"


def test_recurring_workflow_definition_model():
    """RecurringWorkflowDefinition has triggers, goal, execution_mode."""
    w = RecurringWorkflowDefinition(
        workflow_id="w1",
        label="Weekly report",
        trigger_ids=["t1", "t2"],
        planner_goal="Weekly report",
        execution_mode="simulate",
    )
    assert w.workflow_id == "w1"
    assert len(w.trigger_ids) == 2
    assert w.execution_mode == "simulate"


def test_save_and_load_trigger(tmp_path):
    """Save and load trigger definition."""
    t = TriggerDefinition(
        trigger_id="test_trigger",
        kind=TriggerKind.APPROVAL_AVAILABLE,
        label="When approval present",
        enabled=True,
    )
    save_trigger(t, repo_root=tmp_path)
    ids = list_trigger_ids(repo_root=tmp_path)
    assert "test_trigger" in ids
    loaded = get_trigger("test_trigger", repo_root=tmp_path)
    assert loaded is not None
    assert loaded.label == "When approval present"
    assert loaded.kind == TriggerKind.APPROVAL_AVAILABLE


def test_save_and_load_workflow(tmp_path):
    """Save and load recurring workflow definition."""
    w = RecurringWorkflowDefinition(
        workflow_id="test_workflow",
        label="Test",
        trigger_ids=["test_trigger"],
        planner_goal="Test goal",
    )
    save_workflow(w, repo_root=tmp_path)
    ids = list_workflow_ids(repo_root=tmp_path)
    assert "test_workflow" in ids
    loaded = get_workflow("test_workflow", repo_root=tmp_path)
    assert loaded is not None
    assert loaded.planner_goal == "Test goal"


def test_evaluate_active_triggers_empty(tmp_path):
    """With no definitions, evaluation returns empty summary."""
    matches, summary = evaluate_active_triggers(repo_root=tmp_path)
    assert len(matches) == 0
    assert summary.active_trigger_ids == []
    assert summary.suppressed_trigger_ids == []
    assert summary.blocked_trigger_ids == []


def test_evaluate_active_triggers_recurring_digest(tmp_path):
    """Recurring digest trigger matches (heuristic)."""
    t = TriggerDefinition(
        trigger_id="digest_1",
        kind=TriggerKind.RECURRING_DIGEST,
        label="Daily digest",
        condition={"time_window": "morning"},
        enabled=True,
    )
    save_trigger(t, repo_root=tmp_path)
    matches, summary = evaluate_active_triggers(repo_root=tmp_path)
    assert len(matches) == 1
    assert matches[0].matched is True
    assert "digest" in matches[0].reason.lower() or "Recurring" in matches[0].reason
    assert summary.active_trigger_ids == ["digest_1"]


def test_trigger_suppressed_when_disabled(tmp_path):
    """Disabled trigger is suppressed."""
    t = TriggerDefinition(
        trigger_id="off_1",
        kind=TriggerKind.TIME_BASED,
        label="Off",
        enabled=False,
    )
    save_trigger(t, repo_root=tmp_path)
    matches, summary = evaluate_active_triggers(repo_root=tmp_path)
    assert len(matches) == 1
    assert matches[0].suppressed is True
    assert "disabled" in matches[0].suppressed_reason.lower()
    assert "off_1" in summary.suppressed_trigger_ids


def test_explain_trigger_match(tmp_path):
    """Explain returns reason and matched/blocked/suppressed."""
    t = TriggerDefinition(
        trigger_id="explain_1",
        kind=TriggerKind.EVENT_BASED,
        label="Manual",
        condition={"event_type": "manual"},
        enabled=True,
    )
    save_trigger(t, repo_root=tmp_path)
    expl = explain_trigger_match("explain_1", repo_root=tmp_path)
    assert expl.get("trigger_id") == "explain_1"
    assert "matched" in expl
    assert "reason" in expl


def test_explain_trigger_not_found(tmp_path):
    """Explain for missing trigger returns error."""
    expl = explain_trigger_match("nonexistent", repo_root=tmp_path)
    assert expl.get("error") == "trigger_not_found"


def test_list_blocked_suppressed(tmp_path):
    """list_blocked_suppressed_triggers returns structure with blocked/suppressed lists."""
    t = TriggerDefinition(trigger_id="sup_1", kind=TriggerKind.TIME_BASED, enabled=False)
    save_trigger(t, repo_root=tmp_path)
    out = list_blocked_suppressed_triggers(repo_root=tmp_path)
    assert "blocked" in out
    assert "suppressed" in out
    assert isinstance(out["blocked"], list)
    assert isinstance(out["suppressed"], list)


def test_match_triggers_to_workflows(tmp_path):
    """match_triggers_to_workflows returns (trigger_id, workflow_id) for tied workflows."""
    t = TriggerDefinition(trigger_id="tt", kind=TriggerKind.RECURRING_DIGEST, enabled=True)
    save_trigger(t, repo_root=tmp_path)
    w = RecurringWorkflowDefinition(workflow_id="ww", trigger_ids=["tt"], planner_goal="G")
    save_workflow(w, repo_root=tmp_path)
    pairs = match_triggers_to_workflows(["tt"], repo_root=tmp_path)
    assert ("tt", "ww") in pairs


def test_no_trigger_conflict(tmp_path):
    """Multiple triggers can be active; no conflict in summary."""
    for i in range(2):
        t = TriggerDefinition(
            trigger_id=f"multi_{i}",
            kind=TriggerKind.RECURRING_DIGEST,
            enabled=True,
            condition={"time_window": "morning"},
        )
        save_trigger(t, repo_root=tmp_path)
    matches, summary = evaluate_active_triggers(repo_root=tmp_path)
    assert len(summary.active_trigger_ids) == 2
    assert len(matches) == 2


# ----- M34D.1 Automation templates + guardrails -----


def test_automation_template_model():
    """AutomationTemplate has kind, default_trigger_kind, default_planner_goal."""
    tmpl = AutomationTemplate(
        template_id="morning_digest",
        kind=AutomationTemplateKind.MORNING_DIGEST,
        label="Morning digest",
        default_trigger_kind="recurring_digest",
        default_planner_goal="Produce morning digest.",
    )
    assert tmpl.template_id == "morning_digest"
    assert tmpl.kind == AutomationTemplateKind.MORNING_DIGEST
    assert tmpl.default_planner_goal == "Produce morning digest."


def test_guardrail_profile_model():
    """GuardrailProfile has suppression_rules and allowed_trigger_kinds."""
    rule = SuppressionRule(
        rule_id="r1",
        condition_type="no_approval",
        action="block",
        reason="Approval required.",
    )
    p = GuardrailProfile(
        profile_id="supervised",
        kind=GuardrailProfileKind.SUPERVISED,
        label="Supervised",
        suppression_rules=[rule],
        allowed_trigger_kinds=[],
        is_default=True,
    )
    assert p.profile_id == "supervised"
    assert len(p.suppression_rules) == 1
    assert p.suppression_rules[0].condition_type == "no_approval"


def test_save_and_load_template(tmp_path):
    """Save and load automation template."""
    tmpl = AutomationTemplate(
        template_id="end_of_day",
        kind=AutomationTemplateKind.END_OF_DAY_WRAP,
        label="End of day wrap",
        default_trigger_kind="time_based",
        default_trigger_condition={"time_window": "17:00"},
    )
    save_template(tmpl, repo_root=tmp_path)
    ids = list_template_ids(repo_root=tmp_path)
    assert "end_of_day" in ids
    loaded = get_template("end_of_day", repo_root=tmp_path)
    assert loaded is not None
    assert loaded.label == "End of day wrap"
    assert loaded.kind == AutomationTemplateKind.END_OF_DAY_WRAP


def test_save_and_load_guardrail_profile(tmp_path):
    """Save and load guardrail profile."""
    p = GuardrailProfile(
        profile_id="bounded",
        kind=GuardrailProfileKind.BOUNDED_RECURRING,
        label="Bounded recurring",
        allowed_trigger_kinds=["recurring_digest", "time_based"],
        max_recurring_per_day=2,
        is_default=False,
    )
    save_guardrail_profile(p, repo_root=tmp_path)
    ids = list_guardrail_profile_ids(repo_root=tmp_path)
    assert "bounded" in ids
    loaded = get_guardrail_profile("bounded", repo_root=tmp_path)
    assert loaded is not None
    assert loaded.max_recurring_per_day == 2


def test_get_active_guardrail_profile_default(tmp_path):
    """Active profile is the one with is_default=True."""
    a = GuardrailProfile(profile_id="a", is_default=False)
    b = GuardrailProfile(profile_id="b", is_default=True)
    save_guardrail_profile(a, repo_root=tmp_path)
    save_guardrail_profile(b, repo_root=tmp_path)
    active = get_active_guardrail_profile(repo_root=tmp_path)
    assert active is not None
    assert active.profile_id == "b"


def test_instantiate_from_template(tmp_path):
    """instantiate_from_template returns trigger + workflow from template."""
    tmpl = AutomationTemplate(
        template_id="sample",
        kind=AutomationTemplateKind.MORNING_DIGEST,
        label="Sample digest",
        default_trigger_kind="recurring_digest",
        default_trigger_condition={"time_window": "morning"},
        default_planner_goal="Daily digest.",
    )
    save_template(tmpl, repo_root=tmp_path)
    pair = instantiate_from_template("sample", "my_instance", repo_root=tmp_path)
    assert pair is not None
    trigger, workflow = pair
    assert trigger.trigger_id == "my_instance"
    assert trigger.kind == TriggerKind.RECURRING_DIGEST
    assert workflow.workflow_id == "my_instance"
    assert workflow.planner_goal == "Daily digest."
    assert workflow.trigger_ids == ["my_instance"]


def test_guardrail_suppresses_disallowed_trigger_kind(tmp_path):
    """When guardrail profile allows only certain trigger kinds, others are suppressed."""
    t = TriggerDefinition(
        trigger_id="recur_1",
        kind=TriggerKind.RECURRING_DIGEST,
        label="Digest",
        enabled=True,
        condition={"time_window": "morning"},
    )
    save_trigger(t, repo_root=tmp_path)
    p = GuardrailProfile(
        profile_id="strict",
        allowed_trigger_kinds=["event_based", "approval_available"],
        is_default=True,
    )
    save_guardrail_profile(p, repo_root=tmp_path)
    matches, summary = evaluate_active_triggers(repo_root=tmp_path)
    assert len(matches) == 1
    assert matches[0].suppressed is True
    assert "not in allowed" in matches[0].suppressed_reason.lower() or "guardrail" in matches[0].suppressed_reason.lower()
    assert "recur_1" in summary.suppressed_trigger_ids


def test_guardrail_no_approval_blocks(tmp_path):
    """Guardrail rule no_approval blocks trigger when work_state has no approvals."""
    class NoApprovalState:
        approvals_file_exists = False

    t = TriggerDefinition(
        trigger_id="need_approval",
        kind=TriggerKind.RECURRING_DIGEST,
        enabled=True,
        condition={"time_window": "morning"},
        required_policy_trust="approval_required",
    )
    save_trigger(t, repo_root=tmp_path)
    p = GuardrailProfile(
        profile_id="supervised",
        suppression_rules=[
            SuppressionRule(
                rule_id="r1",
                condition_type="no_approval",
                action="block",
                reason="Approval required.",
            )
        ],
        is_default=True,
    )
    save_guardrail_profile(p, repo_root=tmp_path)
    matches, summary = evaluate_active_triggers(repo_root=tmp_path, work_state=NoApprovalState())
    assert len(matches) == 1
    # Either policy block or guardrail block
    assert matches[0].blocked or matches[0].suppressed
    assert not matches[0].matched


def test_instantiate_from_template_not_found(tmp_path):
    """instantiate_from_template returns None for missing template."""
    pair = instantiate_from_template("nonexistent", "id", repo_root=tmp_path)
    assert pair is None
