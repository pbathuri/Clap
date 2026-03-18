"""
M29E–M29H: Natural language to intent — first-draft interpreter with confidence and refusal.
"""

from __future__ import annotations

import re
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


def _normalize(phrase: str) -> str:
    return re.sub(r"\s+", " ", (phrase or "").strip().lower())


def _extract_project_id(phrase: str) -> str | None:
    """Heuristic: look for known project-like tokens (founder_case_alpha, default, etc.)."""
    n = _normalize(phrase)
    # Match quoted or word-like project ids
    m = re.search(r"(founder_case_alpha|default|proj[_\-]?\w+)", n)
    if m:
        return m.group(1)
    return None


def parse_natural_language(phrase: str, repo_root: Path | str | None = None) -> ParsedIntent:
    """
    Map natural language to explicit intent. First-draft: keyword/pattern based.
    Returns ParsedIntent with confidence; intent_type=unknown and low confidence when unclear.
    """
    raw = (phrase or "").strip()
    n = _normalize(raw)
    scope: dict[str, Any] = {}
    project_id = _extract_project_id(raw)

    # Next / what should I do
    if re.search(r"what (should i |do i |to )?do next|what('s| is) next|next (action|step)|what (should i )?work on", n):
        return ParsedIntent(
            intent_type=INTENT_NEXT_ACTION_QUERY,
            scope=scope,
            confidence=0.85,
            suggested_command="workflow-dataset mission-control",
            raw_phrase=raw,
        )

    # Why blocked / blocked state
    if re.search(r"why (is .+ )?blocked|what('s| is) blocked|blocked (state|projects)|why (is )?(it|this) blocked", n):
        scope["project_id"] = project_id
        return ParsedIntent(
            intent_type=INTENT_BLOCKED_STATE_QUERY,
            scope=scope,
            confidence=0.9 if project_id else 0.75,
            ambiguity_note="No project specified; will use current or list blocked." if not project_id else "",
            suggested_command=f"workflow-dataset portfolio blocked" + (f" ; workflow-dataset portfolio explain --project {project_id}" if project_id else ""),
            raw_phrase=raw,
        )

    # What changed
    if re.search(r"what (has )?changed|what('s| is) (new|different)|since yesterday|changes? (today|recent)", n):
        return ParsedIntent(
            intent_type=INTENT_WHAT_CHANGED,
            scope=scope,
            confidence=0.8,
            suggested_command="workflow-dataset progress board",
            raw_phrase=raw,
        )

    # Show what would happen if I approve (check before generic approval queue)
    if re.search(r"what (would )?happen (if i )?approve|preview (if i )?approve|show (me )?(what would happen )?if i approve", n):
        return ParsedIntent(
            intent_type=INTENT_EXECUTION_PREVIEW_REQUEST,
            scope=scope,
            confidence=0.85,
            suggested_command="workflow-dataset agent-loop status",
            raw_phrase=raw,
        )

    # Approval queue / why in queue
    if re.search(r"approval (queue|pending)|why (is .+ )?in the (approval )?queue|what('s| is) (in )?(the )?queue|pending approval|approve (the )?next", n):
        return ParsedIntent(
            intent_type=INTENT_APPROVAL_REVIEW_QUERY,
            scope=scope,
            confidence=0.85,
            suggested_command="workflow-dataset agent-loop status (or approve)",
            raw_phrase=raw,
        )

    # Plan preview
    if re.search(r"plan preview|preview (the )?plan|show (me )?(the )?plan|what('s| is) (the )?(current )?plan", n):
        return ParsedIntent(
            intent_type=INTENT_PLAN_PREVIEW_REQUEST,
            scope=scope,
            confidence=0.85,
            suggested_command="workflow-dataset planner preview --latest",
            raw_phrase=raw,
        )

    # Project switch / switch project
    if re.search(r"switch (to )?(project )?|(change|set) (current )?project|work on (a )?different project", n):
        scope["project_id"] = project_id
        return ParsedIntent(
            intent_type=INTENT_PROJECT_SWITCH_REQUEST,
            scope=scope,
            confidence=0.7 if project_id else 0.5,
            ambiguity_note="Specify project id to switch, e.g. founder_case_alpha." if not project_id else "",
            suggested_command=f"workflow-dataset projects set-current --id {project_id}" if project_id else "workflow-dataset portfolio list ; projects set-current --id <id>",
            raw_phrase=raw,
        )

    # Explain (why this project / why blocked for X)
    if re.search(r"why (did you )?choose (this )?project|explain (this )?project|why (is )?(founder_case_alpha|default|.+) (blocked|priority)", n):
        scope["project_id"] = project_id
        return ParsedIntent(
            intent_type=INTENT_EXPLANATION_QUERY,
            scope=scope,
            confidence=0.8 if project_id else 0.6,
            suggested_command=f"workflow-dataset portfolio explain --project {project_id}" if project_id else "workflow-dataset portfolio explain --project <id>",
            raw_phrase=raw,
        )

    # Status
    if re.search(r"status|current state|how (are we |is (everything|it) )?doing|overview|summary", n):
        return ParsedIntent(
            intent_type=INTENT_STATUS_QUERY,
            scope=scope,
            confidence=0.8,
            suggested_command="workflow-dataset mission-control",
            raw_phrase=raw,
        )

    # Policy
    if re.search(r"policy|(what )?rules?|approval (rules?|policy)|trust (level|policy)", n):
        return ParsedIntent(
            intent_type=INTENT_POLICY_QUESTION,
            scope=scope,
            confidence=0.75,
            suggested_command="workflow-dataset trust report (or policy commands)",
            raw_phrase=raw,
        )

    # Artifact / summary of workspace
    if re.search(r"artifact|workspace (summary|state)|what (is )?(in )?my (active )?workspace|summarize (what changed )?(in )?(my )?(workspace )?today", n):
        return ParsedIntent(
            intent_type=INTENT_ARTIFACT_LOOKUP,
            scope=scope,
            confidence=0.7,
            suggested_command="workflow-dataset mission-control",
            raw_phrase=raw,
        )

    # Pack doing
    if re.search(r"what (is )?(this |the )?pack doing|pack (.+ )?(doing|purpose)", n):
        scope["pack_ref"] = project_id or "current"
        return ParsedIntent(
            intent_type=INTENT_POLICY_QUESTION,
            scope=scope,
            confidence=0.65,
            ambiguity_note="Pack ref inferred or use current.",
            suggested_command="workflow-dataset packs list (or show)",
            raw_phrase=raw,
        )

    # Refusal: unclear
    return ParsedIntent(
        intent_type=INTENT_UNKNOWN,
        scope=scope,
        confidence=0.0,
        ambiguity_note="Intent unclear. Try: 'What should I do next?', 'Why is X blocked?', 'Status', 'What changed?'",
        suggested_command="workflow-dataset mission-control",
        raw_phrase=raw,
    )
