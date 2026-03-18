"""
M33D.1: Transition maps between stages and advance/stall explanations.
"""

from __future__ import annotations

from workflow_dataset.workflow_episodes.models import WorkflowEpisode, WorkflowStage, HandoffGapKind

# Typical next stages from each stage (stage, short description)
STAGE_TRANSITIONS: dict[WorkflowStage, list[tuple[WorkflowStage, str]]] = {
    WorkflowStage.UNKNOWN: [
        (WorkflowStage.INTAKE, "Start gathering or discovery"),
        (WorkflowStage.DRAFTING, "Start creating or editing"),
    ],
    WorkflowStage.INTAKE: [
        (WorkflowStage.DRAFTING, "Move to creating/editing"),
        (WorkflowStage.REVIEW, "Move to reviewing gathered material"),
    ],
    WorkflowStage.DRAFTING: [
        (WorkflowStage.REVIEW, "Send for review or self-review"),
        (WorkflowStage.EXECUTION_FOLLOWUP, "Run or test (e.g. terminal)"),
    ],
    WorkflowStage.REVIEW: [
        (WorkflowStage.APPROVAL_DECISION, "Request or give approval"),
        (WorkflowStage.DRAFTING, "Return to editing after feedback"),
    ],
    WorkflowStage.APPROVAL_DECISION: [
        (WorkflowStage.HANDOFF_WRAPUP, "Complete and hand off"),
        (WorkflowStage.EXECUTION_FOLLOWUP, "Execute after approval"),
    ],
    WorkflowStage.EXECUTION_FOLLOWUP: [
        (WorkflowStage.HANDOFF_WRAPUP, "Wrap up and hand off"),
        (WorkflowStage.DRAFTING, "Return to edit after run"),
    ],
    WorkflowStage.HANDOFF_WRAPUP: [
        (WorkflowStage.INTAKE, "Start next workflow"),
    ],
}


def get_transition_map() -> dict[str, list[dict[str, str]]]:
    """Return full transition map as JSON-friendly dict: from_stage -> [{to_stage, description}]."""
    out: dict[str, list[dict[str, str]]] = {}
    for from_stage, pairs in STAGE_TRANSITIONS.items():
        out[from_stage.value] = [{"to_stage": to_stage.value, "description": desc} for to_stage, desc in pairs]
    return out


def get_next_stages(current: WorkflowStage) -> list[dict[str, str]]:
    """Return possible next stages from current stage."""
    pairs = STAGE_TRANSITIONS.get(current, STAGE_TRANSITIONS.get(WorkflowStage.UNKNOWN, []))
    return [{"to_stage": to_stage.value, "description": desc} for to_stage, desc in pairs]


def get_advance_reasons(from_stage: WorkflowStage, to_stage: WorkflowStage) -> list[str]:
    """Reasons why the workflow may have advanced from from_stage to to_stage."""
    reasons: list[str] = []
    allowed = [to_s for to_s, _ in STAGE_TRANSITIONS.get(from_stage, [])]
    if to_stage in allowed:
        reasons.append(f"Transition {from_stage.value} -> {to_stage.value} is a typical next step.")
    elif from_stage != to_stage:
        reasons.append(f"Stage changed from {from_stage.value} to {to_stage.value} (may reflect new activity).")
    return reasons


def get_stall_reasons(episode: WorkflowEpisode) -> list[str]:
    """Reasons why the workflow may be stalled (gaps, missing next step)."""
    reasons: list[str] = []
    for g in episode.handoff_gaps:
        if g.kind == HandoffGapKind.MISSING_APPROVAL:
            reasons.append("Pending approval: items in approval queue need review or decision.")
        elif g.kind == HandoffGapKind.MISSING_ARTIFACT:
            reasons.append("Missing artifact: expected output or file not yet present.")
        elif g.kind == HandoffGapKind.STALE_EPISODE:
            reasons.append("Stale: no recent activity in this episode.")
        elif g.kind == HandoffGapKind.LIKELY_CONTEXT_SWITCH:
            reasons.append("Context switch: activity may have moved to another app or task.")
    if not reasons and episode.stage in (WorkflowStage.DRAFTING, WorkflowStage.REVIEW):
        if not episode.next_step_candidates:
            reasons.append("No clear next step suggested; consider review or handoff.")
    return reasons


def build_transition_map_output(episode: WorkflowEpisode) -> dict[str, str | list[dict[str, str]]]:
    """Build transition-map output for current episode: current_stage, next_stages, full_map optional."""
    from workflow_dataset.workflow_episodes.stage_detection import infer_stage
    stage, _ = infer_stage(episode)
    return {
        "current_stage": stage.value,
        "episode_type": getattr(episode, "episode_type", "unknown") or "unknown",
        "next_stages": get_next_stages(stage),
        "transition_map": get_transition_map(),
    }


def build_advance_stall_explanation(episode: WorkflowEpisode) -> dict[str, list[str]]:
    """Build why the workflow has advanced or stalled (clearer explanations)."""
    from workflow_dataset.workflow_episodes.stage_detection import infer_stage
    stage, stage_evidence = infer_stage(episode)
    why_advanced: list[str] = []
    why_stalled: list[str] = []

    if stage != WorkflowStage.UNKNOWN and stage_evidence:
        why_advanced.append(f"Current stage '{stage.value}' inferred from: {', '.join(stage_evidence[:3])}.")
    if episode.inferred_project and episode.inferred_project.confidence >= 0.5:
        why_advanced.append(f"Project context: {episode.inferred_project.label} (confidence {episode.inferred_project.confidence:.2f}).")

    why_stalled = get_stall_reasons(episode)
    if not why_stalled and len(episode.linked_activities) == 0:
        why_stalled.append("No linked activities; episode may not have started or has no recent signals.")

    return {
        "why_advanced": why_advanced,
        "why_stalled": why_stalled,
    }
