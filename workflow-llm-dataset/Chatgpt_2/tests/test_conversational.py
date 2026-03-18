"""
M29E–M29H: Conversational command center — intent parsing, explanation, preview, ambiguous/blocked handling.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_dataset.conversational.intents import (
    ParsedIntent,
    INTENT_NEXT_ACTION_QUERY,
    INTENT_BLOCKED_STATE_QUERY,
    INTENT_WHAT_CHANGED,
    INTENT_APPROVAL_REVIEW_QUERY,
    INTENT_EXECUTION_PREVIEW_REQUEST,
    INTENT_PLAN_PREVIEW_REQUEST,
    INTENT_STATUS_QUERY,
    INTENT_UNKNOWN,
)
from workflow_dataset.conversational.interpreter import parse_natural_language
from workflow_dataset.conversational.explain import (
    answer_what_next,
    answer_why_blocked,
    answer_what_changed,
    answer_approval_queue,
    answer_status,
)
from workflow_dataset.conversational.preview import build_action_preview
from workflow_dataset.conversational.ask import ask


def test_parse_next_action():
    p = parse_natural_language("What should I do next?")
    assert p.intent_type == INTENT_NEXT_ACTION_QUERY
    assert p.confidence >= 0.5
    assert "mission-control" in p.suggested_command or "mission" in p.suggested_command


def test_parse_why_blocked():
    p = parse_natural_language("Why is founder_case_alpha blocked?")
    assert p.intent_type == INTENT_BLOCKED_STATE_QUERY
    assert p.scope.get("project_id") == "founder_case_alpha"


def test_parse_what_changed():
    p = parse_natural_language("What changed since yesterday?")
    assert p.intent_type == INTENT_WHAT_CHANGED
    assert p.confidence >= 0.5


def test_parse_approval_queue():
    p = parse_natural_language("Why is this in the approval queue?")
    assert p.intent_type == INTENT_APPROVAL_REVIEW_QUERY


def test_parse_preview_approve():
    p = parse_natural_language("Show me what would happen if I approve the next queued action.")
    assert p.intent_type == INTENT_EXECUTION_PREVIEW_REQUEST


def test_parse_plan_preview():
    p = parse_natural_language("Preview the plan")
    assert p.intent_type == INTENT_PLAN_PREVIEW_REQUEST


def test_parse_status():
    p = parse_natural_language("status")
    assert p.intent_type == INTENT_STATUS_QUERY


def test_parse_unknown_refusal():
    p = parse_natural_language("xyz random gibberish 123")
    assert p.intent_type == INTENT_UNKNOWN
    assert p.confidence == 0.0
    assert p.ambiguity_note


def test_answer_what_next(tmp_path):
    state = {"product_state": {}, "evaluation_state": {}, "development_state": {}, "incubator_state": {}}
    out = answer_what_next(state=state, repo_root=tmp_path)
    assert "action" in out.lower() or "hold" in out.lower() or "recommend" in out.lower()


def test_answer_why_blocked_no_project(tmp_path):
    out = answer_why_blocked(None, repo_root=tmp_path)
    assert "blocked" in out.lower() or "project" in out.lower()


def test_answer_what_changed(tmp_path):
    state = {"progress_replan": {"replan_needed_projects": ["p1"], "stalled_projects": []}}
    out = answer_what_changed(state=state, repo_root=tmp_path)
    assert "change" in out.lower() or "replan" in out.lower() or "p1" in out


def test_answer_approval_queue(tmp_path):
    state = {"supervised_loop": {"pending_queue_count": 0}}
    out = answer_approval_queue(state=state, repo_root=tmp_path)
    assert "approval" in out.lower() or "pending" in out.lower() or "queue" in out.lower()


def test_build_action_preview():
    p = ParsedIntent(intent_type=INTENT_EXECUTION_PREVIEW_REQUEST, suggested_command="agent-loop status")
    out = build_action_preview(p)
    assert "Preview" in out
    assert "approve" in out.lower() or "queue" in out.lower()


def test_ask_returns_answer_and_intent(tmp_path):
    result = ask("What should I do next?", repo_root=tmp_path)
    assert "answer" in result
    assert "intent" in result
    assert result["intent"]["intent_type"] == INTENT_NEXT_ACTION_QUERY
    assert "confidence" in result


def test_ask_unknown_low_confidence(tmp_path):
    result = ask("kthxbye random stuff", repo_root=tmp_path)
    assert result["intent"]["intent_type"] == INTENT_UNKNOWN
    assert result["confidence"] == 0.0
    assert "not sure" in result["answer"].lower() or "unclear" in result["answer"].lower()


def test_ask_grounded_no_execution(tmp_path):
    result = ask("Why is founder_case_alpha blocked?", repo_root=tmp_path)
    assert "answer" in result
    assert result["intent"]["scope"].get("project_id") == "founder_case_alpha"
    assert "workflow-dataset" in result["answer"] or "portfolio" in result["answer"].lower()


# ----- M29H.1 Suggested queries + guided dialogues + roles -----
def test_suggested_queries_for_next_action():
    from workflow_dataset.conversational.suggested_queries import get_suggested_queries
    q = get_suggested_queries(INTENT_NEXT_ACTION_QUERY, {}, None)
    assert len(q) >= 3
    assert any("blocked" in x.lower() or "approval" in x.lower() for x in q)


def test_follow_up_prompts_when_ambiguous():
    from workflow_dataset.conversational.suggested_queries import get_follow_up_prompts_when_ambiguous
    base = get_follow_up_prompts_when_ambiguous("gibberish", role=None)
    assert len(base) >= 3
    reviewer = get_follow_up_prompts_when_ambiguous("gibberish", role="reviewer")
    assert any("approval" in x.lower() or "queue" in x.lower() for x in reviewer)
    operator = get_follow_up_prompts_when_ambiguous("gibberish", role="operator")
    assert any("next" in x.lower() or "blocked" in x.lower() for x in operator)


def test_list_guided_dialogues():
    from workflow_dataset.conversational.dialogues import list_guided_dialogues
    flows = list_guided_dialogues()
    assert len(flows) >= 4
    ids = [f["flow_id"] for f in flows]
    assert "unblock_project" in ids
    assert "approve_and_run" in ids


def test_get_dialogue_definition():
    from workflow_dataset.conversational.dialogues import get_dialogue_definition, FLOW_UNBLOCK_PROJECT
    d = get_dialogue_definition(FLOW_UNBLOCK_PROJECT)
    assert d is not None
    assert d.title
    assert len(d.steps) >= 2
    assert d.steps[0].suggested_command


def test_get_dialogue_for_intent():
    from workflow_dataset.conversational.dialogues import get_dialogue_for_intent
    d = get_dialogue_for_intent(INTENT_BLOCKED_STATE_QUERY, {})
    assert d is not None
    assert d.flow_id == "unblock_project"
    d2 = get_dialogue_for_intent(INTENT_APPROVAL_REVIEW_QUERY, {})
    assert d2 is not None
    assert "approve" in d2.flow_id or "run" in d2.flow_id


def test_role_suggested_commands():
    from workflow_dataset.conversational.roles import get_role_suggested_commands, get_roles
    roles = get_roles()
    assert "operator" in roles
    assert "reviewer" in roles
    op = get_role_suggested_commands("operator")
    assert len(op) >= 3
    assert any("mission" in c.get("command", "") for c in op)
    rev = get_role_suggested_commands("reviewer")
    assert any("lane" in c.get("command", "").lower() or "approval" in c.get("label", "").lower() for c in rev)


def test_ask_returns_suggested_queries(tmp_path):
    result = ask("What should I do next?", repo_root=tmp_path)
    assert "suggested_queries" in result
    assert len(result["suggested_queries"]) >= 2


def test_ask_returns_guided_dialogue_for_blocked(tmp_path):
    result = ask("Why is founder_case_alpha blocked?", repo_root=tmp_path)
    assert "guided_dialogue" in result
    assert result["guided_dialogue"]["flow_id"] == "unblock_project"
    assert result["guided_dialogue"]["title"]


def test_ask_returns_role_commands_when_role_set(tmp_path):
    result = ask("Status", repo_root=tmp_path, role="operator")
    assert "role_commands" in result
    assert len(result["role_commands"]) >= 2
