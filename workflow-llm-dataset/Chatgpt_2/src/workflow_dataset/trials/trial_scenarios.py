"""
M17: First set of workflow trial scenarios — ops, spreadsheet, founder, creative.
"""

from __future__ import annotations

from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.trials.trial_models import WorkflowTrial
from workflow_dataset.trials.trial_registry import register_trial


def _t(
    trial_id: str,
    scenario_id: str,
    domain: str,
    workflow_type: str,
    task_goal: str,
    required_inputs: list[str] | None = None,
    expected_outputs: list[str] | None = None,
    requires_retrieval: bool = False,
    requires_adapter: bool = False,
    prompt_template: str = "",
) -> WorkflowTrial:
    t = WorkflowTrial(
        trial_id=trial_id,
        scenario_id=scenario_id,
        domain=domain,
        workflow_type=workflow_type,
        task_goal=task_goal,
        required_inputs=required_inputs or [],
        expected_outputs=expected_outputs or [],
        requires_retrieval=requires_retrieval,
        requires_adapter=requires_adapter,
        prompt_template=prompt_template or f"Task: {task_goal}\n\nContext:\n{{context}}",
        created_utc=utc_now_iso(),
    )
    register_trial(t)
    return t


def register_all_trials() -> None:
    """Register the first serious set of workflow trials."""

    # Operations / office admin
    _t(
        "ops_summarize_reporting",
        "ops_reporting",
        "ops",
        "summarize_reporting",
        "Summarize this user's recurring reporting workflow and suggest a weekly status structure.",
        required_inputs=["project_context", "style_signals"],
        expected_outputs=["summary", "suggested_structure"],
        prompt_template="Based on the user's projects and style signals, summarize their recurring reporting workflow and suggest a weekly status/report package structure.\n\nContext:\n{context}",
    )
    _t(
        "ops_scaffold_status",
        "ops_reporting",
        "ops",
        "scaffold_status",
        "Scaffold a weekly status report package in the user's style.",
        required_inputs=["project_context"],
        expected_outputs=["scaffold"],
        requires_retrieval=True,
    )
    _t(
        "ops_handoff_bundle",
        "ops_handoff",
        "ops",
        "handoff_bundle",
        "Produce an ops handoff bundle from prior patterns.",
        required_inputs=["project_context", "parsed_artifacts"],
        expected_outputs=["bundle"],
        requires_adapter=True,
    )
    _t(
        "ops_next_steps",
        "ops_next",
        "ops",
        "next_steps",
        "Recommend next steps based on previous work structure.",
        required_inputs=["project_context", "routines"],
        expected_outputs=["recommendations"],
        prompt_template="Given the user's projects and observed routines, recommend sensible next steps. Context:\n{context}",
    )

    # Spreadsheet / finance
    _t(
        "sheet_workbook_structure",
        "sheet_structure",
        "spreadsheet",
        "workbook_structure",
        "Propose a workbook/tracker structure in the user's style.",
        required_inputs=["style_signals", "parsed_artifacts"],
        expected_outputs=["structure"],
        requires_retrieval=True,
    )
    _t(
        "sheet_populated_bundle",
        "sheet_bundle",
        "spreadsheet",
        "populated_bundle",
        "Create a populated bundle from prior spreadsheet-like patterns.",
        required_inputs=["parsed_artifacts", "style_signals"],
        expected_outputs=["bundle"],
        requires_adapter=True,
    )
    _t(
        "sheet_recurring_sections",
        "sheet_patterns",
        "spreadsheet",
        "recurring_sections",
        "Explain likely recurring spreadsheet sections/columns for this user.",
        required_inputs=["style_signals"],
        expected_outputs=["explanation"],
    )
    _t(
        "sheet_reconciliation_scaffold",
        "sheet_finance",
        "spreadsheet",
        "reconciliation_scaffold",
        "Generate a reconciliation/reporting scaffold.",
        required_inputs=["project_context", "parsed_artifacts"],
        expected_outputs=["scaffold"],
        requires_retrieval=True,
    )

    # Founder / project
    _t(
        "founder_project_scaffold",
        "founder_scaffold",
        "founder",
        "project_scaffold",
        "Scaffold a new project folder/bundle in the user's style.",
        required_inputs=["project_context", "style_signals"],
        expected_outputs=["scaffold"],
        prompt_template="Scaffold a new project folder/bundle structure that matches this user's style. Context:\n{context}",
    )
    _t(
        "founder_deliverables_phases",
        "founder_planning",
        "founder",
        "deliverables_phases",
        "Summarize likely deliverables and workflow phases for this user.",
        required_inputs=["project_context", "parsed_artifacts"],
        expected_outputs=["summary"],
        requires_retrieval=True,
    )
    _t(
        "founder_cadence",
        "founder_ops",
        "founder",
        "cadence_structure",
        "Propose a startup/ops cadence structure.",
        required_inputs=["project_context"],
        expected_outputs=["structure"],
    )
    _t(
        "founder_handoff_package",
        "founder_handoff",
        "founder",
        "handoff_package",
        "Produce a founder handoff/update package.",
        required_inputs=["project_context", "style_signals"],
        expected_outputs=["package"],
        requires_adapter=True,
    )

    # Creative / design
    _t(
        "creative_brief_storyboard",
        "creative_brief",
        "creative",
        "brief_storyboard",
        "Generate a creative brief and storyboard/shotlist package in the user's style.",
        required_inputs=["style_signals", "parsed_artifacts"],
        expected_outputs=["brief", "shotlist"],
        requires_retrieval=True,
    )
    _t(
        "creative_naming_export",
        "creative_naming",
        "creative",
        "naming_export",
        "Recommend naming/export structure based on prior patterns.",
        required_inputs=["style_signals"],
        expected_outputs=["recommendations"],
    )
    _t(
        "creative_revision_plan",
        "creative_revision",
        "creative",
        "revision_plan",
        "Produce a revision plan bundle.",
        required_inputs=["parsed_artifacts", "style_signals"],
        expected_outputs=["bundle"],
        requires_adapter=True,
    )
