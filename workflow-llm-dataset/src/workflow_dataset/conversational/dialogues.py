"""
M29H.1: Guided operator dialogues for common flows — step-by-step prompts and suggested commands.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Flow ids
FLOW_UNBLOCK_PROJECT = "unblock_project"
FLOW_APPROVE_AND_RUN = "approve_and_run"
FLOW_SWITCH_AND_PLAN = "switch_and_plan"
FLOW_REVIEW_LANES = "review_lanes"


@dataclass
class DialogueStep:
    """One step in a guided dialogue."""
    step_index: int
    prompt: str
    suggested_command: str = ""
    hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "prompt": self.prompt,
            "suggested_command": self.suggested_command,
            "hint": self.hint,
        }


@dataclass
class GuidedDialogue:
    """A guided flow: id, title, steps."""
    flow_id: str
    title: str
    steps: list[DialogueStep] = field(default_factory=list)
    current_step_index: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "title": self.title,
            "steps": [s.to_dict() for s in self.steps],
            "current_step_index": self.current_step_index,
        }


def get_dialogue_definition(flow_id: str) -> GuidedDialogue | None:
    """Return the definition of a guided dialogue (no state)."""
    if flow_id == FLOW_UNBLOCK_PROJECT:
        return GuidedDialogue(
            flow_id=FLOW_UNBLOCK_PROJECT,
            title="Unblock a project",
            steps=[
                DialogueStep(0, "Identify which project is blocked.", "workflow-dataset portfolio blocked", "Or ask: Why is X blocked?"),
                DialogueStep(1, "Understand why it's blocked.", "workflow-dataset portfolio explain --project <id>", "Or ask: Why is founder_case_alpha blocked?"),
                DialogueStep(2, "Get recovery suggestions.", "workflow-dataset progress recovery --project <id>", "Playbooks and next steps"),
                DialogueStep(3, "Replan if recommended.", "workflow-dataset replan recommend --project <id>", "Then replan diff / accept as needed"),
            ],
        )
    if flow_id == FLOW_APPROVE_AND_RUN:
        return GuidedDialogue(
            flow_id=FLOW_APPROVE_AND_RUN,
            title="Approve and run next action",
            steps=[
                DialogueStep(0, "See what's pending approval.", "workflow-dataset agent-loop status", "Or ask: What's in the approval queue?"),
                DialogueStep(1, "Preview what would happen if you approve.", "workflow-dataset ask \"Show me what would happen if I approve the next action\"", "No execution from ask"),
                DialogueStep(2, "Approve the next item (then executor runs).", "workflow-dataset agent-loop approve --id <queue_id>", "Execution respects trust and checkpoints"),
            ],
        )
    if flow_id == FLOW_SWITCH_AND_PLAN:
        return GuidedDialogue(
            flow_id=FLOW_SWITCH_AND_PLAN,
            title="Switch project and plan",
            steps=[
                DialogueStep(0, "Choose project to switch to.", "workflow-dataset portfolio list", "Or ask: Should I switch project?"),
                DialogueStep(1, "Set current project.", "workflow-dataset projects set-current --id <project_id>", ""),
                DialogueStep(2, "Compile or preview plan for current goal.", "workflow-dataset planner compile --goal \"<goal text>\"", "Or planner preview --latest"),
            ],
        )
    if flow_id == FLOW_REVIEW_LANES:
        return GuidedDialogue(
            flow_id=FLOW_REVIEW_LANES,
            title="Review worker lane results",
            steps=[
                DialogueStep(0, "List lanes (e.g. completed awaiting review).", "workflow-dataset lanes list --status completed", ""),
                DialogueStep(1, "Review one lane's results.", "workflow-dataset lanes review --id <lane_id>", "Or ask: What's awaiting review?"),
                DialogueStep(2, "Approve or reject handoff.", "workflow-dataset lanes approve --id <lane_id>", "Or lanes reject --id <lane_id> --reason \"...\""),
                DialogueStep(3, "Accept into project (if approved).", "workflow-dataset lanes accept --id <lane_id>", ""),
            ],
        )
    return None


def list_guided_dialogues() -> list[dict[str, Any]]:
    """List available guided dialogue flows."""
    return [
        {"flow_id": FLOW_UNBLOCK_PROJECT, "title": "Unblock a project"},
        {"flow_id": FLOW_APPROVE_AND_RUN, "title": "Approve and run next action"},
        {"flow_id": FLOW_SWITCH_AND_PLAN, "title": "Switch project and plan"},
        {"flow_id": FLOW_REVIEW_LANES, "title": "Review worker lane results"},
    ]


def get_dialogue_for_intent(intent_type: str, scope: dict[str, Any]) -> GuidedDialogue | None:
    """Suggest a guided dialogue based on current intent (optional hook from ask)."""
    if intent_type == "blocked_state_query":
        return get_dialogue_definition(FLOW_UNBLOCK_PROJECT)
    if intent_type in ("approval_review_query", "execution_preview_request"):
        return get_dialogue_definition(FLOW_APPROVE_AND_RUN)
    if intent_type == "project_switch_request":
        return get_dialogue_definition(FLOW_SWITCH_AND_PLAN)
    return None
