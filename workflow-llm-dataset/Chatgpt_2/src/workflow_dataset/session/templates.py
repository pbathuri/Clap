"""
M24M.1: Session templates — starting board state, recommended jobs/routines/macros, expected artifacts, next-step chain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionTemplate:
    """
    First-draft session template: starting board state, recommended work items,
    expected artifacts, and likely next-step chain.
    """
    template_id: str
    name: str
    description: str = ""
    value_pack_id: str = ""  # default pack when starting from this template
    # Starting board state
    active_tasks: list[str] = field(default_factory=list)
    job_ids: list[str] = field(default_factory=list)
    routine_ids: list[str] = field(default_factory=list)
    macro_ids: list[str] = field(default_factory=list)
    # Expected artifacts (labels or path patterns)
    expected_artifacts: list[str] = field(default_factory=list)
    # Likely next step chain (suggested commands or actions)
    next_step_chain: list[str] = field(default_factory=list)


# Built-in templates aligned to value packs and practical daily use
BUILTIN_SESSION_TEMPLATES: list[SessionTemplate] = [
    SessionTemplate(
        template_id="morning_review",
        name="Morning review",
        description="Start-of-day: inbox, reminders, overnight changes, first priorities.",
        value_pack_id="founder_ops_plus",
        active_tasks=["Check inbox", "Review reminders", "Pick first priority"],
        job_ids=["weekly_status_from_notes", "weekly_status"],
        routine_ids=["morning_reporting", "morning_ops", "weekly_review"],
        macro_ids=["morning_ops"],
        expected_artifacts=["inbox summary", "morning brief", "plan run record"],
        next_step_chain=[
            "workflow-dataset inbox",
            "workflow-dataset macro run --id morning_ops --mode simulate",
            "workflow-dataset session board",
        ],
    ),
    SessionTemplate(
        template_id="analyst_deep_work",
        name="Analyst deep-work session",
        description="Focused analysis: data, literature, reports; minimal context switching.",
        value_pack_id="analyst_research_plus",
        active_tasks=["Load data/context", "Run analysis job", "Capture findings"],
        job_ids=["weekly_status_from_notes", "weekly_status", "status_action_bundle", "meeting_brief_bundle"],
        routine_ids=["research_digest", "weekly_analysis"],
        macro_ids=[],
        expected_artifacts=["analysis output", "run record", "findings note"],
        next_step_chain=[
            "workflow-dataset jobs run --id weekly_status_from_notes --mode simulate",
            "workflow-dataset session artifacts",
            "workflow-dataset session close",
        ],
    ),
    SessionTemplate(
        template_id="founder_ops_session",
        name="Founder ops session",
        description="Operator/founder: light ops, stakeholder updates, reporting.",
        value_pack_id="founder_ops_plus",
        active_tasks=["Morning ops", "Weekly status", "Stakeholder brief"],
        job_ids=["weekly_status_from_notes", "weekly_status"],
        routine_ids=["morning_reporting", "morning_ops", "weekly_review"],
        macro_ids=["morning_ops"],
        expected_artifacts=["weekly status draft", "morning run record", "brief note"],
        next_step_chain=[
            "workflow-dataset macro run --id morning_ops --mode simulate",
            "workflow-dataset jobs run --id weekly_status_from_notes --mode real",
            "workflow-dataset session close",
        ],
    ),
    SessionTemplate(
        template_id="developer_focus",
        name="Developer focus session",
        description="Coding focus: task replay, scaffold, review; simulate-first.",
        value_pack_id="developer_plus",
        active_tasks=["Task replay", "Code review", "Scaffold"],
        job_ids=["replay_cli_demo"],
        routine_ids=[],
        macro_ids=[],
        expected_artifacts=["task replay preview", "simulate run record"],
        next_step_chain=[
            "workflow-dataset jobs run --id replay_cli_demo --mode simulate",
            "workflow-dataset session board",
            "workflow-dataset session close",
        ],
    ),
    SessionTemplate(
        template_id="document_review",
        name="Document review session",
        description="Document-heavy: long-form, summaries, knowledge-base style work.",
        value_pack_id="document_worker_plus",
        active_tasks=["Load doc context", "Run digest/summary", "Save outline"],
        job_ids=["weekly_status_from_notes", "weekly_status", "meeting_brief_bundle"],
        routine_ids=["doc_review", "weekly_digest"],
        macro_ids=[],
        expected_artifacts=["digest output", "run record", "outline or summary"],
        next_step_chain=[
            "workflow-dataset jobs run --id weekly_status_from_notes --mode simulate",
            "workflow-dataset session artifacts",
            "workflow-dataset session close",
        ],
    ),
]


def list_session_templates() -> list[str]:
    """Return template ids."""
    return [t.template_id for t in BUILTIN_SESSION_TEMPLATES]


def get_session_template(template_id: str) -> SessionTemplate | None:
    """Return template by id, or None."""
    for t in BUILTIN_SESSION_TEMPLATES:
        if t.template_id == template_id:
            return t
    return None
