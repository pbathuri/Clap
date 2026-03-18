"""
M29D.1: Workspace presets and role-specific layouts.
Founder/operator, analyst, developer, document-heavy.
"""

from __future__ import annotations

from workflow_dataset.workspace.models import (
    WorkspacePreset,
    HOME_SECTION_WHERE,
    HOME_SECTION_TOP_PRIORITY,
    HOME_SECTION_APPROVALS,
    HOME_SECTION_BLOCKED,
    HOME_SECTION_RECENT,
    HOME_SECTION_TRUST_HEALTH,
    HOME_SECTION_AREAS,
    HOME_SECTION_QUICK,
    HOME_SECTIONS_DEFAULT,
)

# Preset IDs (CLI: --preset founder-operator | analyst | developer | document-heavy)
PRESET_FOUNDER_OPERATOR = "founder_operator"
PRESET_ANALYST = "analyst"
PRESET_DEVELOPER = "developer"
PRESET_DOCUMENT_HEAVY = "document_heavy"

WORKSPACE_PRESETS: dict[str, WorkspacePreset] = {
    PRESET_FOUNDER_OPERATOR: WorkspacePreset(
        preset_id=PRESET_FOUNDER_OPERATOR,
        label="Founder / Operator",
        description="Portfolio-first: approvals, next project, mission control.",
        home_section_order=(
            HOME_SECTION_WHERE,
            HOME_SECTION_APPROVALS,
            HOME_SECTION_TOP_PRIORITY,
            HOME_SECTION_BLOCKED,
            HOME_SECTION_RECENT,
            HOME_SECTION_TRUST_HEALTH,
            HOME_SECTION_AREAS,
            HOME_SECTION_QUICK,
        ),
        default_quick_actions=(
            {"label": "Mission control", "command": "workflow-dataset mission-control"},
            {"label": "Portfolio next", "command": "workflow-dataset portfolio next"},
            {"label": "Approval queue", "command": "workflow-dataset agent-loop queue"},
            {"label": "Workspace context", "command": "workflow-dataset workspace context"},
        ),
        priority_widgets=(HOME_SECTION_APPROVALS, HOME_SECTION_TOP_PRIORITY),
        recommended_first_view="portfolio",
    ),
    PRESET_ANALYST: WorkspacePreset(
        preset_id=PRESET_ANALYST,
        label="Analyst",
        description="Session and outcomes first: artifacts, recent activity, outcomes report.",
        home_section_order=(
            HOME_SECTION_WHERE,
            HOME_SECTION_RECENT,
            HOME_SECTION_TOP_PRIORITY,
            HOME_SECTION_BLOCKED,
            HOME_SECTION_APPROVALS,
            HOME_SECTION_TRUST_HEALTH,
            HOME_SECTION_AREAS,
            HOME_SECTION_QUICK,
        ),
        default_quick_actions=(
            {"label": "Session board", "command": "workflow-dataset session board"},
            {"label": "Session artifacts", "command": "workflow-dataset session artifacts"},
            {"label": "Outcomes report", "command": "workflow-dataset outcomes report"},
            {"label": "Projects list", "command": "workflow-dataset projects list"},
        ),
        priority_widgets=(HOME_SECTION_RECENT, HOME_SECTION_WHERE),
        recommended_first_view="session",
    ),
    PRESET_DEVELOPER: WorkspacePreset(
        preset_id=PRESET_DEVELOPER,
        label="Developer",
        description="Lanes and packs: current session, lanes, runtime, agent next.",
        home_section_order=(
            HOME_SECTION_WHERE,
            HOME_SECTION_TOP_PRIORITY,
            HOME_SECTION_BLOCKED,
            HOME_SECTION_APPROVALS,
            HOME_SECTION_RECENT,
            HOME_SECTION_TRUST_HEALTH,
            HOME_SECTION_AREAS,
            HOME_SECTION_QUICK,
        ),
        default_quick_actions=(
            {"label": "Session board", "command": "workflow-dataset session board"},
            {"label": "Lanes list", "command": "workflow-dataset lanes list"},
            {"label": "Packs list", "command": "workflow-dataset packs list"},
            {"label": "Agent next", "command": "workflow-dataset agent-loop next"},
        ),
        priority_widgets=(HOME_SECTION_WHERE, HOME_SECTION_TOP_PRIORITY),
        recommended_first_view="session",
    ),
    PRESET_DOCUMENT_HEAVY: WorkspacePreset(
        preset_id=PRESET_DOCUMENT_HEAVY,
        label="Document-heavy",
        description="Artifacts and outcomes first: session artifacts, outcomes, blocked.",
        home_section_order=(
            HOME_SECTION_WHERE,
            HOME_SECTION_RECENT,
            HOME_SECTION_BLOCKED,
            HOME_SECTION_TOP_PRIORITY,
            HOME_SECTION_APPROVALS,
            HOME_SECTION_TRUST_HEALTH,
            HOME_SECTION_AREAS,
            HOME_SECTION_QUICK,
        ),
        default_quick_actions=(
            {"label": "Session artifacts", "command": "workflow-dataset session artifacts"},
            {"label": "Outcomes report", "command": "workflow-dataset outcomes report"},
            {"label": "Session board", "command": "workflow-dataset session board"},
            {"label": "Projects list", "command": "workflow-dataset projects list"},
        ),
        priority_widgets=(HOME_SECTION_RECENT, HOME_SECTION_BLOCKED),
        recommended_first_view="artifacts",
    ),
}


def get_preset(preset_id: str) -> WorkspacePreset | None:
    """Return preset by id; accepts preset_id with underscores or hyphens."""
    key = (preset_id or "").strip().lower().replace("-", "_")
    return WORKSPACE_PRESETS.get(key)


def list_preset_ids() -> list[str]:
    """Return ordered list of preset ids."""
    return [
        PRESET_FOUNDER_OPERATOR,
        PRESET_ANALYST,
        PRESET_DEVELOPER,
        PRESET_DOCUMENT_HEAVY,
    ]


def get_default_section_order() -> tuple[str, ...]:
    """Default home section order (no preset)."""
    return HOME_SECTIONS_DEFAULT
