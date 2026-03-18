"""
M47I–M47L: Guidance tightening — next best action, review-needed, blocked-state, resume, operator routine, support/recovery.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.quality_guidance.models import (
    GuidanceItem,
    QualitySignal,
    ClarityScore,
    ConfidenceWithEvidence,
    ReadyToActSignal,
    NeedsReviewSignal,
    StrongNextStepSignal,
    AmbiguityWarning,
    WeakGuidanceWarning,
    GuidanceKind,
)
from workflow_dataset.quality_guidance.signals import build_quality_signals


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def _guid_id(prefix: str, kind: str) -> str:
    from workflow_dataset.utils.hashes import stable_id
    from workflow_dataset.utils.dates import utc_now_iso
    return stable_id("guide", kind, utc_now_iso(), prefix=prefix)


def next_best_action_guidance(repo_root: Path | str | None = None) -> GuidanceItem | None:
    """Next best action with quality signal; sharper rationale and evidence-linked confidence."""
    root = _repo_root(repo_root)
    signals = build_quality_signals(root)
    sig = signals.get("next_action_signal")
    if not sig:
        return None
    strong = (sig.get("strong_next_step") or {})
    summary = strong.get("step_label", "hold")
    rationale = strong.get("rationale", "No urgent signal; review state and choose next step.")
    action_ref = strong.get("command_or_ref", "")
    clarity = sig.get("clarity", {})
    confidence = sig.get("confidence", {})
    quality = QualitySignal(
        clarity=ClarityScore(
            clarity.get("score", 0.5),
            clarity.get("reason", ""),
            clarity.get("evidence_refs", []),
        ),
        confidence=ConfidenceWithEvidence(
            confidence.get("level", "medium"),
            confidence.get("evidence_refs", []),
            confidence.get("disclaimer", ""),
        ),
        weak_guidance_warnings=[WeakGuidanceWarning(**w) for w in sig.get("weak_guidance_warnings", [])],
        strong_next_step=StrongNextStepSignal(
            step_label=strong.get("step_label", summary),
            rationale=rationale,
            evidence_refs=strong.get("evidence_refs", []),
            command_or_ref=action_ref,
        ) if strong else None,
        ready_to_act=ReadyToActSignal(**sig["ready_to_act"]) if sig.get("ready_to_act") else None,
    )
    return GuidanceItem(
        guide_id=_guid_id("next", GuidanceKind.NEXT_ACTION.value),
        kind=GuidanceKind.NEXT_ACTION.value,
        summary=f"Next: {summary}",
        rationale=rationale,
        quality_signal=quality,
        action_ref=action_ref,
        evidence_refs=quality.clarity.evidence_refs,
    )


def review_needed_guidance(repo_root: Path | str | None = None) -> GuidanceItem | None:
    """Review-needed guidance (pending proposals, unreviewed workspaces) with quality signal."""
    root = _repo_root(repo_root)
    signals = build_quality_signals(root)
    sig = signals.get("review_needed_signal")
    if not sig:
        return None
    nr = sig.get("needs_review", {})
    summary = nr.get("label", "Items need review")
    rationale = nr.get("rationale", "Apply or reject proposals; or review and package workspaces.")
    quality = QualitySignal(
        clarity=ClarityScore(
            sig.get("clarity", {}).get("score", 0.8),
            sig.get("clarity", {}).get("reason", ""),
            sig.get("clarity", {}).get("evidence_refs", []),
        ),
        confidence=ConfidenceWithEvidence(
            sig.get("confidence", {}).get("level", "high"),
            sig.get("confidence", {}).get("evidence_refs", []),
            "",
        ),
        needs_review=NeedsReviewSignal(
            label=nr.get("label", summary),
            ref=nr.get("ref", ""),
            priority=nr.get("priority", "medium"),
            rationale=rationale,
        ),
    )
    return GuidanceItem(
        guide_id=_guid_id("review", GuidanceKind.REVIEW_NEEDED.value),
        kind=GuidanceKind.REVIEW_NEEDED.value,
        summary=summary,
        rationale=rationale,
        quality_signal=quality,
        action_ref="workflow-dataset devlab show-proposal; workflow-dataset review-studio inbox",
        evidence_refs=quality.clarity.evidence_refs,
    )


def blocked_state_guidance(
    project_id: str = "",
    repo_root: Path | str | None = None,
) -> GuidanceItem | None:
    """Blocked-state recovery guidance: executor blocked or progress stalled, with clearer recovery phrasing."""
    root = _repo_root(repo_root)
    signals = build_quality_signals(root)
    sig = signals.get("blocked_recovery_signal")
    if not sig:
        return None
    ready = sig.get("ready_to_act") or sig.get("strong_next_step")
    if not ready:
        return None
    if isinstance(ready, dict):
        summary = ready.get("label", ready.get("step_label", "Recover blocked state"))
        rationale = ready.get("rationale", ready.get("command_or_ref", "Run recovery for blocked run or stalled project."))
        action_ref = ready.get("action_ref", ready.get("command_or_ref", ""))
    else:
        summary = getattr(ready, "label", getattr(ready, "step_label", "Recover blocked state"))
        rationale = getattr(ready, "rationale", "")
        action_ref = getattr(ready, "action_ref", getattr(ready, "command_or_ref", ""))
    quality = QualitySignal(
        clarity=ClarityScore(
            sig.get("clarity", {}).get("score", 0.75),
            sig.get("clarity", {}).get("reason", ""),
            sig.get("clarity", {}).get("evidence_refs", []),
        ),
        confidence=ConfidenceWithEvidence(
            sig.get("confidence", {}).get("level", "medium"),
            sig.get("confidence", {}).get("evidence_refs", []),
            "",
        ),
        ready_to_act=ReadyToActSignal(**sig["ready_to_act"]) if sig.get("ready_to_act") else None,
        strong_next_step=StrongNextStepSignal(**sig["strong_next_step"]) if sig.get("strong_next_step") else None,
    )
    return GuidanceItem(
        guide_id=_guid_id("blocked", GuidanceKind.BLOCKED_STATE.value),
        kind=GuidanceKind.BLOCKED_STATE.value,
        summary=summary,
        rationale=rationale,
        quality_signal=quality,
        action_ref=action_ref,
        evidence_refs=quality.clarity.evidence_refs,
    )


def resume_guidance(repo_root: Path | str | None = None) -> GuidanceItem | None:
    """Resume guidance when a run is awaiting approval; ready-to-act with concise rationale."""
    root = _repo_root(repo_root)
    signals = build_quality_signals(root)
    sig = signals.get("resume_signal")
    if not sig:
        return None
    ready = sig.get("ready_to_act", {})
    summary = ready.get("label", "Resume run")
    rationale = ready.get("rationale", "Run is paused at checkpoint; approve next step to continue.")
    quality = QualitySignal(
        clarity=ClarityScore(
            sig.get("clarity", {}).get("score", 0.9),
            sig.get("clarity", {}).get("reason", ""),
            sig.get("clarity", {}).get("evidence_refs", []),
        ),
        confidence=ConfidenceWithEvidence(
            sig.get("confidence", {}).get("level", "high"),
            sig.get("confidence", {}).get("evidence_refs", []),
            "",
        ),
        ready_to_act=ReadyToActSignal(**ready),
    )
    return GuidanceItem(
        guide_id=_guid_id("resume", GuidanceKind.RESUME.value),
        kind=GuidanceKind.RESUME.value,
        summary=summary,
        rationale=rationale,
        quality_signal=quality,
        action_ref=ready.get("action_ref", "supervised-loop next; executor resume"),
        evidence_refs=quality.clarity.evidence_refs,
    )


def operator_routine_guidance(repo_root: Path | str | None = None) -> GuidanceItem | None:
    """Operator routine: production review cycle, sustained-use, stability review; one concise item."""
    root = _repo_root(repo_root)
    try:
        from workflow_dataset.production_launch.ongoing_summary import build_ongoing_production_summary
        ongoing = build_ongoing_production_summary(root)
    except Exception:
        return None
    one_liner = ongoing.get("one_liner", "")
    guidance = (ongoing.get("post_deployment_guidance") or {}).get("guidance", "continue")
    summary = f"Routine: {guidance}. {one_liner[:80]}"
    rationale = "Run production-runbook review-cycle and sustained-use checkpoint per runbook; schedule next stability review."
    quality = QualitySignal(
        clarity=ClarityScore(0.75, "Ongoing summary and guidance available.", ["ongoing_summary"]),
        confidence=ConfidenceWithEvidence("medium", ["ongoing_summary"], ""),
        strong_next_step=StrongNextStepSignal(
            step_label="Run production review cycle",
            rationale=rationale,
            evidence_refs=["ongoing_summary"],
            command_or_ref="workflow-dataset production-runbook review-cycle show",
        ),
    )
    return GuidanceItem(
        guide_id=_guid_id("routine", GuidanceKind.OPERATOR_ROUTINE.value),
        kind=GuidanceKind.OPERATOR_ROUTINE.value,
        summary=summary,
        rationale=rationale,
        quality_signal=quality,
        action_ref="workflow-dataset stability-reviews generate; workflow-dataset production-runbook review-cycle show",
        evidence_refs=["ongoing_summary"],
    )


def support_recovery_guidance(
    vertical_id: str = "",
    repo_root: Path | str | None = None,
) -> GuidanceItem | None:
    """Support/recovery guidance for the chosen vertical; use vertical playbook when stalled."""
    root = _repo_root(repo_root)
    vid = vertical_id
    if not vid:
        try:
            from workflow_dataset.vertical_selection import get_active_vertical_id
            vid = get_active_vertical_id(root) or ""
        except Exception:
            vid = ""
    try:
        from workflow_dataset.vertical_packs.progress import get_blocked_vertical_onboarding_step
        blocked = get_blocked_vertical_onboarding_step(root)
        if blocked and blocked.get("blocked"):
            step_index = blocked.get("blocked_step_index", 0)
            pack_id = blocked.get("curated_pack_id", vid) or vid
            from workflow_dataset.vertical_packs.playbooks import get_operator_guidance_when_stalled
            stall_guidance = get_operator_guidance_when_stalled(pack_id, step_index, root)
            guidance_text = stall_guidance.get("guidance", "Run first-value path and retry the suggested step.")
            commands = stall_guidance.get("commands", ["workflow-dataset vertical-packs progress"])
            failure = stall_guidance.get("failure_entry", {})
            rationale = failure.get("remediation_hint", guidance_text) or guidance_text
            quality = QualitySignal(
                clarity=ClarityScore(0.85, "Vertical playbook has stalled-step guidance.", ["vertical_packs_playbook"]),
                confidence=ConfidenceWithEvidence("high", ["vertical_packs_playbook"], ""),
                strong_next_step=StrongNextStepSignal(
                    step_label="Recover vertical onboarding step",
                    rationale=rationale,
                    evidence_refs=["vertical_packs_playbook"],
                    command_or_ref=commands[0] if commands else "workflow-dataset vertical-packs first-value",
                ),
            )
            return GuidanceItem(
                guide_id=_guid_id("support", GuidanceKind.SUPPORT_RECOVERY.value),
                kind=GuidanceKind.SUPPORT_RECOVERY.value,
                summary="Vertical onboarding blocked; use playbook recovery.",
                rationale=rationale,
                quality_signal=quality,
                action_ref=commands[0] if commands else "",
                evidence_refs=["vertical_packs_playbook"],
                vertical_id=pack_id,
            )
    except Exception:
        pass
    return None
