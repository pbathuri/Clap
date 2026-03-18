"""
M47I–M47L: Build quality signals from mission_control next_action, project_case, executor, vertical playbook, progress (read-only).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.quality_guidance.models import (
    QualitySignal,
    ClarityScore,
    ConfidenceWithEvidence,
    AmbiguityWarning,
    ReadyToActSignal,
    NeedsReviewSignal,
    StrongNextStepSignal,
    WeakGuidanceWarning,
)


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_quality_signals(
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Aggregate quality signals from existing layers (read-only). Returns a dict with:
    next_action_signal, review_needed_signal, blocked_recovery_signal, resume_signal,
    ambiguity_warnings, weak_guidance_warnings, strongest_ready_to_act, most_ambiguous.
    """
    root = _repo_root(repo_root)
    state: dict[str, Any] = {}
    try:
        from workflow_dataset.workspace.state import _mission_control_state_with_timeout

        mc = _mission_control_state_with_timeout(root)
        state = mc if mc is not None else {}
    except Exception:
        pass

    next_action_signal: QualitySignal | None = None
    review_needed_signal: QualitySignal | None = None
    blocked_recovery_signal: QualitySignal | None = None
    resume_signal: QualitySignal | None = None
    ambiguity_warnings: list[AmbiguityWarning] = []
    weak_guidance_warnings: list[WeakGuidanceWarning] = []
    strongest_ready_to_act: ReadyToActSignal | None = None
    most_ambiguous: AmbiguityWarning | None = None

    # Next action from mission_control
    try:
        from workflow_dataset.mission_control.next_action import recommend_next_action
        rec = recommend_next_action(state)
        action = rec.get("action", "hold")
        rationale = rec.get("rationale", "")
        detail = rec.get("detail", "")
        if action == "hold" and "No urgent signal" in (rationale or ""):
            clarity = ClarityScore(0.4, "No urgent signal; recommendation is generic.", ["mission_control_next_action"])
            confidence = ConfidenceWithEvidence("low", ["mission_control"], "No strong evidence; review state and choose.")
            weak_guidance_warnings.append(WeakGuidanceWarning(
                "Next action is hold with no urgent signal.",
                "Run mission-control and act on a specific subsystem (e.g. build, benchmark, promote).",
                "next_action",
            ))
        else:
            clarity = ClarityScore(0.8, "Specific action recommended.", ["mission_control_next_action"])
            confidence = ConfidenceWithEvidence("medium", ["mission_control"], "")
        ready = None
        strong = StrongNextStepSignal(
            step_label=action,
            rationale=rationale or "",
            evidence_refs=["mission_control_next_action"],
            command_or_ref=detail or "",
        )
        if action != "hold":
            ready = ReadyToActSignal(
                label=f"Do: {action}",
                action_ref=detail or action,
                rationale=rationale,
                evidence_refs=["mission_control_next_action"],
            )
            if not strongest_ready_to_act:
                strongest_ready_to_act = ready
        next_action_signal = QualitySignal(
            clarity=clarity,
            confidence=confidence,
            weak_guidance_warnings=weak_guidance_warnings[-1:] if action == "hold" else [],
            ready_to_act=ready,
            strong_next_step=strong,
        )
    except Exception as e:
        ambiguity_warnings.append(AmbiguityWarning(
            f"Could not compute next action: {e}.",
            "Run workflow-dataset mission-control for full state.",
            "next_action",
        ))
        if not most_ambiguous:
            most_ambiguous = ambiguity_warnings[-1]

    # Review needed: pending proposals, unreviewed workspaces
    try:
        dev = state.get("development_state", {})
        pending = dev.get("pending_proposals", 0)
        product = state.get("product_state", {})
        unreviewed = (product.get("review_package") or {}).get("unreviewed_count", 0)
        if pending > 0 or unreviewed > 0:
            label = "Pending proposals need review" if pending > 0 else "Workspaces need review"
            ref = f"Pending: {pending}" if pending else f"Unreviewed: {unreviewed}"
            review_needed_signal = QualitySignal(
                clarity=ClarityScore(0.85, "Specific review backlog.", ["development_state", "product_state"]),
                confidence=ConfidenceWithEvidence("high", ["development_state", "product_state"], ""),
                needs_review=NeedsReviewSignal(
                    label=label,
                    ref=ref,
                    priority="high" if pending else "medium",
                    rationale="Apply or reject proposals; or review and package workspaces.",
                ),
            )
    except Exception:
        pass

    # Blocked recovery: executor blocked run or progress stalled
    try:
        from workflow_dataset.executor.hub import get_recovery_options, list_runs
        runs = list_runs(limit=5, repo_root=root)
        for r in runs:
            if r.get("status") == "blocked":
                opts = get_recovery_options(r.get("run_id", ""), root)
                if opts and "error" not in opts:
                    blocked_recovery_signal = QualitySignal(
                        clarity=ClarityScore(0.9, "Blocked run has clear recovery options.", ["executor"]),
                        confidence=ConfidenceWithEvidence("high", ["executor"], ""),
                        ready_to_act=ReadyToActSignal(
                            label="Resolve blocked run: retry, skip, or substitute",
                            action_ref=opts.get("message", "executor resume-from-blocked"),
                            rationale=opts.get("blocked_reason", "Run blocked."),
                            evidence_refs=["executor_recovery_options"],
                        ),
                    )
                    if not strongest_ready_to_act:
                        strongest_ready_to_act = blocked_recovery_signal.ready_to_act
                break
    except Exception:
        pass
    if not blocked_recovery_signal:
        try:
            from workflow_dataset.progress.recovery import build_stalled_recovery
            board = state.get("progress_replan", {}) or {}
            stalled = board.get("stalled_projects", []) or []
            replan = board.get("replan_needed_projects", []) or []
            if stalled or replan:
                rec = build_stalled_recovery("default", root)
                playbook = rec.get("matched_playbook") or {}
                blocked_recovery_signal = QualitySignal(
                    clarity=ClarityScore(0.7, "Stalled/replan projects; playbook matched.", ["progress_recovery"]),
                    confidence=ConfidenceWithEvidence("medium", ["progress_recovery"], ""),
                    strong_next_step=StrongNextStepSignal(
                        step_label="Run stalled recovery",
                        rationale=playbook.get("rationale", "Match board to playbook and run recovery."),
                        evidence_refs=["progress_recovery"],
                        command_or_ref="workflow-dataset portfolio blocked; workflow-dataset progress recovery --project <id>",
                    ),
                )
        except Exception:
            pass

    # Resume: executor awaiting_approval
    try:
        from workflow_dataset.supervised_loop.next_action import propose_next_actions
        proposed, blocked = propose_next_actions("", root)
        if proposed:
            first = proposed[0]
            if getattr(first, "action_type", "") == "executor_resume":
                resume_signal = QualitySignal(
                    clarity=ClarityScore(0.9, "One run awaiting approval; resume is clear.", ["supervised_loop"]),
                    confidence=ConfidenceWithEvidence("high", ["supervised_loop"], ""),
                    ready_to_act=ReadyToActSignal(
                        label=getattr(first, "label", "Resume executor run"),
                        action_ref=getattr(first, "action_id", ""),
                        rationale=getattr(first, "why", ""),
                        evidence_refs=["supervised_loop_next_action"],
                    ),
                )
                if not strongest_ready_to_act:
                    strongest_ready_to_act = resume_signal.ready_to_act
    except Exception:
        pass

    if ambiguity_warnings and not most_ambiguous:
        most_ambiguous = ambiguity_warnings[0]

    return {
        "next_action_signal": next_action_signal.to_dict() if next_action_signal else None,
        "review_needed_signal": review_needed_signal.to_dict() if review_needed_signal else None,
        "blocked_recovery_signal": blocked_recovery_signal.to_dict() if blocked_recovery_signal else None,
        "resume_signal": resume_signal.to_dict() if resume_signal else None,
        "ambiguity_warnings": [w.to_dict() for w in ambiguity_warnings],
        "weak_guidance_warnings": [w.to_dict() for w in weak_guidance_warnings],
        "strongest_ready_to_act": strongest_ready_to_act.to_dict() if strongest_ready_to_act else None,
        "most_ambiguous": most_ambiguous.to_dict() if most_ambiguous else None,
    }
