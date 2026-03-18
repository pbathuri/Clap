"""
M51I–M51L: Narrative stages and presenter guidance.
"""

from __future__ import annotations

from workflow_dataset.investor_demo.models import (
    DemoNarrativeStage,
    PresenterGuidanceNote,
    STAGE_ORDER,
)


def guidance_for_stage(stage: DemoNarrativeStage | str) -> PresenterGuidanceNote:
    s = stage if isinstance(stage, DemoNarrativeStage) else DemoNarrativeStage(stage)
    notes: dict[DemoNarrativeStage, PresenterGuidanceNote] = {
        DemoNarrativeStage.STARTUP_READINESS: PresenterGuidanceNote(
            stage_id=s.value,
            headline="Show the machine is ready",
            talking_points=[
                "Local-first: no cloud required for this walkthrough.",
                "Environment checks reflect real readiness—not a mock dashboard.",
            ],
            caution="If degraded warnings appear, say so explicitly before continuing.",
        ),
        DemoNarrativeStage.ROLE_ONBOARDING: PresenterGuidanceNote(
            stage_id=s.value,
            headline="Anchor on a single role and vertical",
            talking_points=[
                "We deliberately narrow to one demo pack so the story stays coherent.",
                "Production cut / vertical choice is the contract for what we demo.",
            ],
            caution="Do not imply every vertical is equally mature.",
        ),
        DemoNarrativeStage.MEMORY_BOOTSTRAP: PresenterGuidanceNote(
            stage_id=s.value,
            headline="Local memory and continuity",
            talking_points=[
                "Carry-forward and resume signals show the system remembers working context.",
                "Nothing here executes—it's evidence of durable local state.",
            ],
            caution="Memory depth depends on prior local usage.",
        ),
        DemoNarrativeStage.INFERRED_USER_CONTEXT: PresenterGuidanceNote(
            stage_id=s.value,
            headline="What the system infers from state",
            talking_points=[
                "Context comes from mission-control aggregates, not invented personas.",
            ],
            caution="Sparse state means thinner context—that's honest.",
        ),
        DemoNarrativeStage.FIRST_VALUE_RECOMMENDATION: PresenterGuidanceNote(
            stage_id=s.value,
            headline="First-value path",
            talking_points=[
                "Vertical excellence path shows where the user gets tangible value.",
                "Next step is a real CLI command—safe to run in simulate where offered.",
            ],
            caution="Blocked paths must be acknowledged.",
        ),
        DemoNarrativeStage.ARTIFACT_GENERATION: PresenterGuidanceNote(
            stage_id=s.value,
            headline="A useful artifact from current state",
            talking_points=[
                "The artifact is generated from live slices—deterministic summary, not a deck.",
                "Explains why: grounded in vertical and continuity signals.",
            ],
            caution="This is a demo artifact, not legal or financial advice.",
        ),
        DemoNarrativeStage.SUPERVISED_OPERATOR_ACTION: PresenterGuidanceNote(
            stage_id=s.value,
            headline="Supervised assistance",
            talking_points=[
                "Action card shows what would happen; simulate-only by default.",
                "Real execution stays behind operator approval.",
            ],
            caution="Never skip the approval story for investors.",
        ),
        DemoNarrativeStage.CLOSING_MISSION_CONTROL_SUMMARY: PresenterGuidanceNote(
            stage_id=s.value,
            headline="Close with the demo mission-control panel",
            talking_points=[
                "Eight lines tie the story together: readiness, role, memory, value, safe action.",
                "Investable = coherent local product with supervision, not feature sprawl.",
            ],
            caution="Invite questions on risk and roadmap, not on hidden features.",
        ),
    }
    return notes.get(s, PresenterGuidanceNote(stage_id=str(s), headline="Stage", talking_points=[]))


def next_stage(current: str) -> str | None:
    """Return next stage id or None if at end."""
    try:
        cur = DemoNarrativeStage(current)
    except ValueError:
        return STAGE_ORDER[0].value if STAGE_ORDER else None
    idx = STAGE_ORDER.index(cur) if cur in STAGE_ORDER else -1
    if idx < 0 or idx + 1 >= len(STAGE_ORDER):
        return None
    return STAGE_ORDER[idx + 1].value


def stage_index(stage_id: str) -> int:
    try:
        return STAGE_ORDER.index(DemoNarrativeStage(stage_id))
    except (ValueError, KeyError):
        return 0
