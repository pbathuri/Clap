"""
M51L.1: Compact 5-minute investor demo script (~300s) with stage-aligned beats.
"""

from __future__ import annotations

from workflow_dataset.investor_demo.models import DemoScriptBeat, FiveMinuteDemoScript, DemoNarrativeStage


def build_five_minute_demo_script() -> FiveMinuteDemoScript:
    """
    Eight beats ~35–40s each ≈ 300s. Each beat: SHOW (terminal/UI), CLICK/RUN (CLI), SAY, IF_DEGRADED_SAY.
    """
    d = 38
    beats: list[DemoScriptBeat] = []
    t = 0

    def add(stage: DemoNarrativeStage, show: str, run: str, say: str, deg: str, note: str = "") -> None:
        nonlocal t, beats
        beats.append(DemoScriptBeat(
            beat_index=len(beats) + 1,
            stage_id=stage.value,
            start_after_seconds=t,
            duration_seconds=d,
            show=show,
            click_or_run=run,
            say=say,
            if_degraded_say=deg,
            narrative_note=note,
        ))
        t += d

    opening_deg = (
        "We're not in perfect readiness—that's fine. Say: 'I'll show you the same product arc in five minutes, "
        "just with honest limits on this machine.'"
    )
    add(
        DemoNarrativeStage.STARTUP_READINESS,
        "Terminal full screen; font readable.",
        "workflow-dataset investor-demo presenter-mode --on  &&  workflow-dataset investor-demo cue",
        "This is local-first. Nothing here depends on cloud for the story we're about to tell.",
        opening_deg,
    )
    add(
        DemoNarrativeStage.ROLE_ONBOARDING,
        "Same terminal.",
        "workflow-dataset investor-demo session start  (if no session yet)",
        "We deliberately pick one role pack and vertical so investors don't get lost in breadth.",
        "If vertical isn't locked, say: 'Imagine this locked to your vertical—same flow.'",
    )
    add(
        DemoNarrativeStage.MEMORY_BOOTSTRAP,
        "Terminal.",
        "workflow-dataset investor-demo mission-control  (first 3 lines only)",
        "Memory and continuity live locally—carry-forward and resume are real state, not theater.",
        "If continuity lines are empty, say: 'Cold start today—the structure is what we're showing.'",
    )
    add(
        DemoNarrativeStage.INFERRED_USER_CONTEXT,
        "Terminal.",
        "workflow-dataset investor-demo cue",
        "Context is inferred from aggregates on disk, not a fabricated user profile.",
        "Sparse context is OK—say you're showing signal, not pretending rich history.",
    )
    add(
        DemoNarrativeStage.FIRST_VALUE_RECOMMENDATION,
        "Terminal.",
        "workflow-dataset investor-demo script --beat 5  (or session first-value)",
        "First value is a real path recommendation from this repo's state.",
        "If blocked, say: 'In production we'd unblock this step—here's the intended path.'",
    )
    add(
        DemoNarrativeStage.ARTIFACT_GENERATION,
        "Terminal.",
        "workflow-dataset investor-demo first-value  (prints markdown artifact)",
        "This artifact is deterministic from local state—auditable, not a random LLM pitch.",
        "Same script—artifact may say placeholder if repo is thin; narrate that honesty.",
    )
    add(
        DemoNarrativeStage.SUPERVISED_OPERATOR_ACTION,
        "Terminal.",
        "workflow-dataset investor-demo supervised-action",
        "Assistance stays supervised: simulate or prefill—real execution waits for operator approval.",
        "Emphasize approval more if env is degraded—safety doesn't relax when the machine is thin.",
    )
    add(
        DemoNarrativeStage.CLOSING_MISSION_CONTROL_SUMMARY,
        "Terminal.",
        "workflow-dataset investor-demo mission-control",
        "Eight lines: readiness through supervision—that's the coherent product story.",
        "If degraded block shows, read it once: 'That's the honest posture—questions?'",
    )

    return FiveMinuteDemoScript(
        total_target_seconds=t,
        beats=beats,
        degraded_opening_line=(
            "If anything is yellow or degraded: name it once, then continue—credibility beats pretending green."
        ),
        script_id="investor_demo_5min_v1",
    )


def beat_for_stage(stage_id: str) -> DemoScriptBeat | None:
    script = build_five_minute_demo_script()
    for b in script.beats:
        if b.stage_id == stage_id:
            return b
    return None


def format_script_compact_text(script: FiveMinuteDemoScript | None = None) -> str:
    s = script or build_five_minute_demo_script()
    lines = [
        f"=== 5-minute investor demo script (~{s.total_target_seconds}s) ===",
        f"[{s.degraded_opening_line}]",
        "",
    ]
    for b in s.beats:
        mm = b.start_after_seconds // 60
        ss = b.start_after_seconds % 60
        lines.append(f"— Beat {b.beat_index} @ ~{mm}:{ss:02d}  ({b.duration_seconds}s)  [{b.stage_id}] —")
        lines.append(f"  SHOW:  {b.show}")
        lines.append(f"  RUN:   {b.click_or_run}")
        lines.append(f"  SAY:   {b.say}")
        if b.if_degraded_say:
            lines.append(f"  IF DEGRADED: {b.if_degraded_say}")
        lines.append("")
    return "\n".join(lines)
