"""
M29H.1: Role-specific suggested commands — operator, reviewer, etc.
"""

from __future__ import annotations

from typing import Any

# Roles
ROLE_OPERATOR = "operator"
ROLE_REVIEWER = "reviewer"
ROLE_DEFAULT = "default"

# Role -> short label and suggested commands (for display after ask or when ambiguous)
ROLE_SUGGESTED_COMMANDS: dict[str, list[dict[str, str]]] = {
    ROLE_OPERATOR: [
        {"label": "Mission control", "command": "workflow-dataset mission-control"},
        {"label": "What to do next", "command": "workflow-dataset portfolio next"},
        {"label": "Blocked projects", "command": "workflow-dataset portfolio blocked"},
        {"label": "Progress board", "command": "workflow-dataset progress board"},
        {"label": "Approve next action", "command": "workflow-dataset agent-loop approve --id <id>"},
        {"label": "Switch project", "command": "workflow-dataset projects set-current --id <id>"},
    ],
    ROLE_REVIEWER: [
        {"label": "Approval queue", "command": "workflow-dataset agent-loop status"},
        {"label": "Lanes awaiting review", "command": "workflow-dataset lanes list --status completed"},
        {"label": "Review a lane", "command": "workflow-dataset lanes review --id <lane_id>"},
        {"label": "Approve lane handoff", "command": "workflow-dataset lanes approve --id <lane_id>"},
        {"label": "Trust report", "command": "workflow-dataset trust report"},
        {"label": "Mission control", "command": "workflow-dataset mission-control"},
    ],
    ROLE_DEFAULT: [
        {"label": "Status", "command": "workflow-dataset mission-control"},
        {"label": "Ask something", "command": "workflow-dataset ask \"What should I do next?\""},
        {"label": "Blocked", "command": "workflow-dataset portfolio blocked"},
        {"label": "Progress", "command": "workflow-dataset progress board"},
    ],
}


def get_role_suggested_commands(role: str | None) -> list[dict[str, str]]:
    """Return suggested commands for the given role. role=None -> ROLE_DEFAULT."""
    if not role:
        return list(ROLE_SUGGESTED_COMMANDS.get(ROLE_DEFAULT, []))
    return list(ROLE_SUGGESTED_COMMANDS.get(role, ROLE_SUGGESTED_COMMANDS[ROLE_DEFAULT]))


def get_roles() -> list[str]:
    """Return known role ids."""
    return [ROLE_OPERATOR, ROLE_REVIEWER, ROLE_DEFAULT]
