"""
M24M.1: Daily cadence flows — ordered sequence of session templates for a typical day.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from workflow_dataset.session.templates import get_session_template


@dataclass
class CadenceStep:
    """Single step in a cadence: template_id and optional label."""
    template_id: str
    label: str = ""


@dataclass
class CadenceFlow:
    """Daily cadence: ordered list of session templates (e.g. morning → focus → review)."""
    cadence_id: str
    name: str
    description: str = ""
    steps: list[CadenceStep] = field(default_factory=list)


# Built-in cadence flows
BUILTIN_CADENCE_FLOWS: list[CadenceFlow] = [
    CadenceFlow(
        cadence_id="daily_founder",
        name="Daily founder / operator",
        description="Morning review → founder ops session. Pack: founder_ops_plus.",
        steps=[
            CadenceStep("morning_review", "Morning review"),
            CadenceStep("founder_ops_session", "Founder ops session"),
        ],
    ),
    CadenceFlow(
        cadence_id="daily_analyst",
        name="Daily analyst",
        description="Morning review → analyst deep-work. Pack: analyst_research_plus.",
        steps=[
            CadenceStep("morning_review", "Morning review"),
            CadenceStep("analyst_deep_work", "Analyst deep-work"),
        ],
    ),
    CadenceFlow(
        cadence_id="daily_developer",
        name="Daily developer",
        description="Morning review → developer focus. Pack: developer_plus.",
        steps=[
            CadenceStep("morning_review", "Morning review"),
            CadenceStep("developer_focus", "Developer focus"),
        ],
    ),
    CadenceFlow(
        cadence_id="daily_document",
        name="Daily document worker",
        description="Morning review → document review session. Pack: document_worker_plus.",
        steps=[
            CadenceStep("morning_review", "Morning review"),
            CadenceStep("document_review", "Document review"),
        ],
    ),
    CadenceFlow(
        cadence_id="morning_only",
        name="Morning only",
        description="Single morning review step. Pack: founder_ops_plus.",
        steps=[
            CadenceStep("morning_review", "Morning review"),
        ],
    ),
]


def list_cadence_flows() -> list[str]:
    """Return cadence ids."""
    return [c.cadence_id for c in BUILTIN_CADENCE_FLOWS]


def get_cadence_flow(cadence_id: str) -> CadenceFlow | None:
    """Return cadence by id, or None."""
    for c in BUILTIN_CADENCE_FLOWS:
        if c.cadence_id == cadence_id:
            return c
    return None


def resolve_cadence_pack(cadence_id: str) -> str:
    """Return the primary value_pack_id for this cadence (from first step's template)."""
    cadence = get_cadence_flow(cadence_id)
    if not cadence or not cadence.steps:
        return ""
    t = get_session_template(cadence.steps[0].template_id)
    return t.value_pack_id if t else ""
