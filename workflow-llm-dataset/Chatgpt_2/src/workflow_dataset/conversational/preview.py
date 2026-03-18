"""
M29E–M29H: Action preview — show what would run, trust/approval implications, no execution.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.conversational.intents import (
    ParsedIntent,
    INTENT_EXECUTION_PREVIEW_REQUEST,
    INTENT_PLAN_PREVIEW_REQUEST,
    INTENT_APPROVAL_REVIEW_QUERY,
    INTENT_PROJECT_SWITCH_REQUEST,
)


def build_action_preview(
    parsed_intent: ParsedIntent,
    state: dict[str, Any] | None = None,
    repo_root: Path | str | None = None,
) -> str:
    """
    For action-like intents, return a preview: what command/action would run, trust/approval note.
    Does not execute anything.
    """
    intent = parsed_intent.intent_type
    cmd = parsed_intent.suggested_command or ""

    if intent == INTENT_EXECUTION_PREVIEW_REQUEST:
        try:
            from workflow_dataset.mission_control.state import get_mission_control_state
            s = state or get_mission_control_state(repo_root)
        except Exception:
            s = state or {}
        sl = s.get("supervised_loop", {})
        next_label = sl.get("next_proposed_action_label", "")
        next_id = sl.get("next_proposed_action_id", "")
        out = "**Preview: If you approve the next queued action**\n"
        out += f"  Proposed action: {next_label or '(none)'}\n"
        out += f"  To approve (no execution from ask): run `workflow-dataset agent-loop approve --id {next_id or '<id>'}`\n"
        out += "  Trust/approval: Approval sends the action to the executor; execution respects trust and checkpoint rules."
        return out

    if intent == INTENT_PLAN_PREVIEW_REQUEST:
        out = "**Preview: View current plan**\n"
        out += f"  Command: `{cmd}`\n"
        out += "  This only shows the plan; no compile or execution."
        return out

    if intent == INTENT_APPROVAL_REVIEW_QUERY:
        out = "**Preview: Approval queue**\n"
        out += f"  Check queue: `workflow-dataset agent-loop status`\n"
        out += "  Approving an item hands it to the executor; approval is required before real execution for gated steps."
        return out

    if intent == INTENT_PROJECT_SWITCH_REQUEST:
        pid = parsed_intent.scope.get("project_id")
        out = "**Preview: Switch project**\n"
        out += f"  Command: `workflow-dataset projects set-current --id {pid or '<project_id>'}`\n"
        out += "  This only changes current project pointer; no automatic plan or run."
        return out

    return f"**Preview**\n  Suggested command: `{cmd}`\n  No execution from ask; run the command yourself to apply."
