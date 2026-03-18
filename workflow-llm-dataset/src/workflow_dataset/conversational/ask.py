"""
M29E–M29H: Conversational ask — parse phrase, ground answer, optional action preview.
M29H.1: Suggested queries, guided dialogue, role-specific commands.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.conversational.intents import (
    ParsedIntent,
    INTENT_STATUS_QUERY,
    INTENT_EXPLANATION_QUERY,
    INTENT_NEXT_ACTION_QUERY,
    INTENT_BLOCKED_STATE_QUERY,
    INTENT_APPROVAL_REVIEW_QUERY,
    INTENT_PROJECT_SWITCH_REQUEST,
    INTENT_PLAN_PREVIEW_REQUEST,
    INTENT_EXECUTION_PREVIEW_REQUEST,
    INTENT_POLICY_QUESTION,
    INTENT_ARTIFACT_LOOKUP,
    INTENT_WHAT_CHANGED,
    INTENT_UNKNOWN,
)
from workflow_dataset.conversational.interpreter import parse_natural_language
from workflow_dataset.conversational.explain import (
    answer_what_next,
    answer_why_blocked,
    answer_why_this_project,
    answer_what_changed,
    answer_approval_queue,
    answer_pack_doing,
    answer_status,
    answer_artifact_lookup,
)
from workflow_dataset.conversational.preview import build_action_preview
from workflow_dataset.conversational.suggested_queries import get_suggested_queries, get_follow_up_prompts_when_ambiguous
from workflow_dataset.conversational.dialogues import get_dialogue_for_intent
from workflow_dataset.conversational.roles import get_role_suggested_commands

# Minimum confidence to return an intent-driven answer; below this we return refusal + suggestions
MIN_CONFIDENCE = 0.5


def ask(
    phrase: str,
    repo_root: Path | str | None = None,
    include_preview: bool = True,
    role: str | None = None,
) -> dict[str, Any]:
    """
    Process natural-language question/request. Returns:
    - answer: text response (grounded in state or refusal)
    - intent: parsed intent dict
    - preview: optional action preview text (if include_preview and action-like)
    - confidence: 0..1
    - suggested_queries: M29H.1 suggested next questions (or follow-up prompts when ambiguous)
    - guided_dialogue: M29H.1 optional guided flow when intent maps to a flow
    - role_commands: M29H.1 role-specific suggested commands when role is set
    """
    root = Path(repo_root).resolve() if repo_root else None
    parsed = parse_natural_language(phrase, root)
    state = None
    try:
        from workflow_dataset.mission_control.state import get_mission_control_state
        state = get_mission_control_state(root)
    except Exception:
        pass

    # Resolve current project if scope missing
    if not parsed.scope.get("project_id") and state:
        pid = (state.get("project_case") or {}).get("active_project_id")
        if pid:
            parsed.scope["project_id"] = pid

    answer = ""
    if parsed.intent_type == INTENT_UNKNOWN or parsed.confidence < MIN_CONFIDENCE:
        follow_ups = get_follow_up_prompts_when_ambiguous(parsed.raw_phrase, role)
        answer = "I'm not sure what you're asking. Try one of these: " + "; ".join(f'"{q}"' for q in follow_ups[:3])
        if parsed.suggested_command:
            answer += f" Or run: `{parsed.suggested_command}`"
    elif parsed.intent_type == INTENT_NEXT_ACTION_QUERY:
        answer = answer_what_next(state, root)
    elif parsed.intent_type == INTENT_BLOCKED_STATE_QUERY:
        answer = answer_why_blocked(parsed.scope.get("project_id"), state, root)
    elif parsed.intent_type == INTENT_EXPLANATION_QUERY:
        answer = answer_why_this_project(parsed.scope.get("project_id"), state, root)
    elif parsed.intent_type == INTENT_WHAT_CHANGED:
        answer = answer_what_changed(state, root)
    elif parsed.intent_type == INTENT_APPROVAL_REVIEW_QUERY:
        answer = answer_approval_queue(state, root)
    elif parsed.intent_type == INTENT_PLAN_PREVIEW_REQUEST:
        answer = "Current plan: run `workflow-dataset planner preview --latest` to see steps, checkpoints, and blocked conditions. No execution from here."
    elif parsed.intent_type == INTENT_EXECUTION_PREVIEW_REQUEST:
        answer = answer_approval_queue(state, root)
        answer += "\n\n" + build_action_preview(parsed, state, root)
    elif parsed.intent_type == INTENT_PROJECT_SWITCH_REQUEST:
        pid = parsed.scope.get("project_id")
        answer = f"To switch project: run `workflow-dataset projects set-current --id {pid or '<project_id>'}`. No switch is performed from ask."
        if not pid:
            answer = "Specify which project to switch to (e.g. founder_case_alpha). Then run: workflow-dataset projects set-current --id <id>"
    elif parsed.intent_type == INTENT_STATUS_QUERY:
        answer = answer_status(state, root)
    elif parsed.intent_type == INTENT_POLICY_QUESTION:
        answer = answer_pack_doing(parsed.scope.get("pack_ref"), state, root) if parsed.scope.get("pack_ref") else "Trust and approval policy: run 'workflow-dataset trust report' for current policy. Approvals are required before real execution for gated steps."
    elif parsed.intent_type == INTENT_ARTIFACT_LOOKUP:
        answer = answer_artifact_lookup(state, root)
    else:
        answer = answer_status(state, root)

    preview = ""
    if include_preview and parsed.intent_type in (
        INTENT_EXECUTION_PREVIEW_REQUEST,
        INTENT_PLAN_PREVIEW_REQUEST,
        INTENT_APPROVAL_REVIEW_QUERY,
        INTENT_PROJECT_SWITCH_REQUEST,
    ):
        preview = build_action_preview(parsed, state, root)

    # M29H.1: Suggested next questions (or follow-up prompts when ambiguous)
    if parsed.intent_type == INTENT_UNKNOWN or parsed.confidence < MIN_CONFIDENCE:
        suggested_queries = get_follow_up_prompts_when_ambiguous(parsed.raw_phrase, role)
    else:
        suggested_queries = get_suggested_queries(parsed.intent_type, parsed.scope, state)

    # M29H.1: Guided dialogue when intent maps to a flow
    guided_dialogue = None
    dialogue = get_dialogue_for_intent(parsed.intent_type, parsed.scope)
    if dialogue:
        guided_dialogue = dialogue.to_dict()

    # M29H.1: Role-specific suggested commands
    role_commands = get_role_suggested_commands(role) if role else []

    out = {
        "answer": answer,
        "intent": parsed.to_dict(),
        "preview": preview,
        "confidence": parsed.confidence,
        "suggested_queries": suggested_queries,
    }
    if guided_dialogue:
        out["guided_dialogue"] = guided_dialogue
    if role_commands:
        out["role_commands"] = role_commands
    return out
