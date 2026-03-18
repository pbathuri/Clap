"""
M36D.1: Workday presets by role — founder/operator, analyst, developer, document-heavy, supervision-heavy.
Defines default day states, default transitions, queue/review emphasis, operator-mode usage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from workflow_dataset.workday.models import WorkdayState


# Emphasis levels for queue/review and operator-mode
EMPHASIS_HIGH = "high"
EMPHASIS_MEDIUM = "medium"
EMPHASIS_LOW = "low"
OPERATOR_MODE_PREFERRED = "preferred"
OPERATOR_MODE_OPTIONAL = "optional"
OPERATOR_MODE_RARE = "rare"
OPERATOR_MODE_NONE = "none"


@dataclass
class WorkdayPreset:
    """Role-based workday preset: default states, transitions, queue/review emphasis, operator-mode usage."""
    preset_id: str = ""
    label: str = ""
    description: str = ""
    # Default day flow: ordered states this role typically visits (after startup)
    default_day_states: list[str] = field(default_factory=list)
    # After startup, preferred first transition (e.g. focus_work vs review_and_approvals)
    default_transition_after_startup: str = ""
    # Queue/review emphasis: high = suggest review early and often; low = focus first
    queue_review_emphasis: str = EMPHASIS_MEDIUM
    # Operator-mode usage: preferred = suggest operator_mode; rare/none = focus/review only
    operator_mode_usage: str = OPERATOR_MODE_OPTIONAL
    # Quick actions for this role (label, command)
    quick_actions: list[dict[str, str]] = field(default_factory=list)
    # Short hint for operating surface (e.g. "Portfolio and approvals first")
    role_operating_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "preset_id": self.preset_id,
            "label": self.label,
            "description": self.description,
            "default_day_states": list(self.default_day_states),
            "default_transition_after_startup": self.default_transition_after_startup,
            "queue_review_emphasis": self.queue_review_emphasis,
            "operator_mode_usage": self.operator_mode_usage,
            "quick_actions": list(self.quick_actions),
            "role_operating_hint": self.role_operating_hint,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "WorkdayPreset":
        return cls(
            preset_id=str(d.get("preset_id", "")),
            label=str(d.get("label", "")),
            description=str(d.get("description", "")),
            default_day_states=list(d.get("default_day_states") or []),
            default_transition_after_startup=str(d.get("default_transition_after_startup", "")),
            queue_review_emphasis=str(d.get("queue_review_emphasis", EMPHASIS_MEDIUM)),
            operator_mode_usage=str(d.get("operator_mode_usage", OPERATOR_MODE_OPTIONAL)),
            quick_actions=[dict(x) for x in (d.get("quick_actions") or [])],
            role_operating_hint=str(d.get("role_operating_hint", "")),
        )


PRESET_FOUNDER_OPERATOR = "founder_operator"
PRESET_ANALYST = "analyst"
PRESET_DEVELOPER = "developer"
PRESET_DOCUMENT_HEAVY = "document_heavy"
PRESET_SUPERVISION_HEAVY = "supervision_heavy"

BUILTIN_WORKDAY_PRESETS: list[WorkdayPreset] = [
    WorkdayPreset(
        preset_id=PRESET_FOUNDER_OPERATOR,
        label="Founder / Operator",
        description="Portfolio-first: start day, check approvals and queue, use operator mode for delegated work, wrap with review.",
        default_day_states=[
            WorkdayState.STARTUP.value,
            WorkdayState.REVIEW_AND_APPROVALS.value,
            WorkdayState.FOCUS_WORK.value,
            WorkdayState.OPERATOR_MODE.value,
            WorkdayState.WRAP_UP.value,
            WorkdayState.SHUTDOWN.value,
        ],
        default_transition_after_startup=WorkdayState.REVIEW_AND_APPROVALS.value,
        queue_review_emphasis=EMPHASIS_HIGH,
        operator_mode_usage=OPERATOR_MODE_PREFERRED,
        quick_actions=[
            {"label": "Mission control", "command": "workflow-dataset mission-control"},
            {"label": "Portfolio next", "command": "workflow-dataset portfolio next"},
            {"label": "Approval queue", "command": "workflow-dataset agent-loop queue"},
            {"label": "Operator mode status", "command": "workflow-dataset operator-mode status"},
        ],
        role_operating_hint="Portfolio and approvals first; operator mode for delegated runs.",
    ),
    WorkdayPreset(
        preset_id=PRESET_ANALYST,
        label="Analyst",
        description="Session and focus first: start, focus work, review when needed, minimal operator mode.",
        default_day_states=[
            WorkdayState.STARTUP.value,
            WorkdayState.FOCUS_WORK.value,
            WorkdayState.REVIEW_AND_APPROVALS.value,
            WorkdayState.WRAP_UP.value,
            WorkdayState.SHUTDOWN.value,
        ],
        default_transition_after_startup=WorkdayState.FOCUS_WORK.value,
        queue_review_emphasis=EMPHASIS_MEDIUM,
        operator_mode_usage=OPERATOR_MODE_RARE,
        quick_actions=[
            {"label": "Session board", "command": "workflow-dataset session board"},
            {"label": "Outcomes report", "command": "workflow-dataset outcomes report"},
            {"label": "Projects list", "command": "workflow-dataset projects list"},
        ],
        role_operating_hint="Focus work first; review when queue has items.",
    ),
    WorkdayPreset(
        preset_id=PRESET_DEVELOPER,
        label="Developer",
        description="Lanes and focus: start, focus or operator mode for runs, review before wrap.",
        default_day_states=[
            WorkdayState.STARTUP.value,
            WorkdayState.FOCUS_WORK.value,
            WorkdayState.OPERATOR_MODE.value,
            WorkdayState.REVIEW_AND_APPROVALS.value,
            WorkdayState.WRAP_UP.value,
            WorkdayState.SHUTDOWN.value,
        ],
        default_transition_after_startup=WorkdayState.FOCUS_WORK.value,
        queue_review_emphasis=EMPHASIS_MEDIUM,
        operator_mode_usage=OPERATOR_MODE_PREFERRED,
        quick_actions=[
            {"label": "Lanes list", "command": "workflow-dataset lanes list"},
            {"label": "Executor status", "command": "workflow-dataset executor status"},
            {"label": "Agent next", "command": "workflow-dataset agent-loop next"},
        ],
        role_operating_hint="Focus or operator mode; review before wrap.",
    ),
    WorkdayPreset(
        preset_id=PRESET_DOCUMENT_HEAVY,
        label="Document-heavy",
        description="Artifacts and review: start, focus on documents/artifacts, review and approvals, then wrap.",
        default_day_states=[
            WorkdayState.STARTUP.value,
            WorkdayState.FOCUS_WORK.value,
            WorkdayState.REVIEW_AND_APPROVALS.value,
            WorkdayState.WRAP_UP.value,
            WorkdayState.SHUTDOWN.value,
        ],
        default_transition_after_startup=WorkdayState.FOCUS_WORK.value,
        queue_review_emphasis=EMPHASIS_HIGH,
        operator_mode_usage=OPERATOR_MODE_RARE,
        quick_actions=[
            {"label": "Session artifacts", "command": "workflow-dataset session artifacts"},
            {"label": "Review studio", "command": "workflow-dataset review status"},
            {"label": "Inbox list", "command": "workflow-dataset inbox list"},
        ],
        role_operating_hint="Documents and artifacts first; review queue regularly.",
    ),
    WorkdayPreset(
        preset_id=PRESET_SUPERVISION_HEAVY,
        label="Supervision-heavy operator",
        description="Review and approvals first: start, clear queue and reviews, then focus or operator mode.",
        default_day_states=[
            WorkdayState.STARTUP.value,
            WorkdayState.REVIEW_AND_APPROVALS.value,
            WorkdayState.FOCUS_WORK.value,
            WorkdayState.OPERATOR_MODE.value,
            WorkdayState.WRAP_UP.value,
            WorkdayState.SHUTDOWN.value,
        ],
        default_transition_after_startup=WorkdayState.REVIEW_AND_APPROVALS.value,
        queue_review_emphasis=EMPHASIS_HIGH,
        operator_mode_usage=OPERATOR_MODE_PREFERRED,
        quick_actions=[
            {"label": "Agent loop queue", "command": "workflow-dataset agent-loop queue"},
            {"label": "Inbox studio", "command": "workflow-dataset inbox-studio list"},
            {"label": "Automation inbox", "command": "workflow-dataset automation-inbox list"},
            {"label": "Trust validate-config", "command": "workflow-dataset trust validate-config"},
        ],
        role_operating_hint="Clear approvals and review first; then focus or operator mode.",
    ),
]


def get_workday_preset(preset_id: str) -> WorkdayPreset | None:
    """Return built-in workday preset by id."""
    for p in BUILTIN_WORKDAY_PRESETS:
        if p.preset_id == preset_id:
            return p
    return None


def list_workday_presets() -> list[WorkdayPreset]:
    """Return all built-in workday presets."""
    return list(BUILTIN_WORKDAY_PRESETS)
