"""
M36I–M36L: Resume flow — detect interrupted work, reconnect to project/session/episode, surface next steps.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from workflow_dataset.utils.dates import utc_now_iso
except Exception:
    from datetime import datetime, timezone
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

try:
    from workflow_dataset.utils.hashes import stable_id
except Exception:
    def stable_id(*parts: str, prefix: str = "") -> str:
        import hashlib
        return prefix + hashlib.sha256("".join(str(p) for p in parts).encode()).hexdigest()[:14]

from workflow_dataset.continuity_engine.models import ResumeCard, InterruptedWorkChain
from workflow_dataset.continuity_engine.store import load_last_shutdown, load_next_session_recommendation, load_carry_forward


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def detect_interrupted_work(repo_root: Path | str | None = None) -> InterruptedWorkChain | None:
    """Infer interrupted work from workday state, last shutdown, current project/episode."""
    root = _root(repo_root)
    chain_id = stable_id("chain", "resume", utc_now_iso()[:16], prefix="chain_")

    project_id = ""
    session_ref = ""
    episode_ref = ""
    last_activity = ""
    inferred = "Unknown"
    next_step = "Run continuity morning to see recommended first action."
    confidence = "low"

    try:
        from workflow_dataset.workday.store import load_workday_state
        record = load_workday_state(root)
        if record.transition_history:
            last_activity = record.transition_history[-1].at_iso
        if record.entered_at_iso:
            last_activity = last_activity or record.entered_at_iso
        if record.state == "resume_pending":
            inferred = "Last session was shutdown; resuming today."
            next_step = "workflow-dataset continuity morning"
            confidence = "medium"
    except Exception:
        pass

    rec = load_next_session_recommendation(root)
    if rec:
        next_step = rec.first_action_command or next_step
        inferred = rec.likely_start_context or inferred
        if rec.carry_forward_count > 0:
            next_step = "workflow-dataset continuity carry-forward then " + (rec.first_action_command or "continuity morning")

    try:
        from workflow_dataset.workspace.state import build_active_work_context
        ctx = build_active_work_context(repo_root=root)
        if ctx and getattr(ctx, "active_project_id", None):
            project_id = project_id or getattr(ctx, "active_project_id", "")
    except Exception:
        pass

    if not project_id and not session_ref and not episode_ref:
        return InterruptedWorkChain(
            chain_id=chain_id,
            inferred_what_doing=inferred,
            next_step_summary=next_step,
            confidence=confidence,
        )

    return InterruptedWorkChain(
        chain_id=chain_id,
        project_id=project_id,
        session_ref=session_ref,
        episode_ref=episode_ref,
        last_activity_utc=last_activity,
        inferred_what_doing=inferred,
        next_step_summary=next_step,
        confidence=confidence,
    )


def get_strongest_resume_target(repo_root: Path | str | None = None) -> tuple[str, str]:
    """Return (label, command) for the strongest resume target (handoff or morning)."""
    root = _root(repo_root)
    try:
        from workflow_dataset.automation_inbox import get_recommended_handoff
        handoff = get_recommended_handoff(repo_root=root)
        if handoff and handoff.command:
            return handoff.label, handoff.command
    except Exception:
        pass
    return "Start morning flow", "workflow-dataset continuity morning"


def build_resume_flow(repo_root: Path | str | None = None) -> ResumeCard:
    """Build resume card: interrupted work, reconnect refs, what doing, what remains, first action."""
    root = _root(repo_root)
    now = utc_now_iso()
    card_id = stable_id("resume", now[:16], prefix="card_")

    interrupted = detect_interrupted_work(root)
    label, command = get_strongest_resume_target(root)
    what_doing = interrupted.inferred_what_doing if interrupted else "No prior context. Start with morning flow."
    what_remains: list[str] = []
    if interrupted and interrupted.next_step_summary:
        what_remains.append(interrupted.next_step_summary)
    carry = load_carry_forward(root)
    if carry:
        what_remains.append(f"{len(carry)} carry-forward item(s): workflow-dataset continuity carry-forward")

    suggested = command
    if not what_remains:
        suggested = "workflow-dataset continuity morning"

    memory_context: dict = {}
    try:
        from workflow_dataset.memory_intelligence.continuity_enrichment import get_resume_memory_context
        project_id = interrupted.project_id if interrupted else ""
        session_ref = interrupted.session_ref if interrupted else ""
        memory_context = get_resume_memory_context(project_id=project_id, session_ref=session_ref, repo_root=root)
    except Exception:
        pass

    return ResumeCard(
        card_id=card_id,
        generated_at_utc=now,
        interrupted_work=interrupted,
        resume_target_label=label,
        resume_target_command=command,
        what_system_thinks_doing=what_doing,
        what_remains=what_remains if what_remains else ["Run morning flow: workflow-dataset continuity morning"],
        suggested_first_action=suggested,
        memory_context=memory_context,
    )
