"""
M47I–M47L: Feels-excellent guidance surfaces — ready now, not safe yet, ambiguity report, weak-guidance report.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.quality_guidance.signals import build_quality_signals
from workflow_dataset.quality_guidance.guidance import (
    next_best_action_guidance,
    review_needed_guidance,
    blocked_state_guidance,
    resume_guidance,
    operator_routine_guidance,
    support_recovery_guidance,
)


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def ready_now_states(repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """States where the operator can act now: ready_to_act with clear action_ref and rationale."""
    root = _repo_root(repo_root)
    signals = build_quality_signals(root)
    out: list[dict[str, Any]] = []
    if signals.get("strongest_ready_to_act"):
        r = signals["strongest_ready_to_act"]
        out.append({
            "label": r.get("label", ""),
            "action_ref": r.get("action_ref", ""),
            "rationale": r.get("rationale", ""),
            "source": "quality_signals",
        })
    for fn in [resume_guidance, next_best_action_guidance, blocked_state_guidance, review_needed_guidance]:
        try:
            g = fn(root)
            if g and g.quality_signal.ready_to_act:
                r = g.quality_signal.ready_to_act
                out.append({
                    "label": r.label,
                    "action_ref": r.action_ref,
                    "rationale": r.rationale,
                    "source": g.kind,
                })
        except Exception:
            pass
    # Dedupe by label
    seen = set()
    deduped = []
    for x in out:
        k = x.get("label", "")
        if k and k not in seen:
            seen.add(k)
            deduped.append(x)
    return deduped


def not_safe_yet_states(repo_root: Path | str | None = None) -> list[dict[str, Any]]:
    """States where it is not safe to proceed without review or more evidence: needs_review, low clarity, weak evidence."""
    root = _repo_root(repo_root)
    signals = build_quality_signals(root)
    out: list[dict[str, Any]] = []
    for key in ("review_needed_signal", "next_action_signal"):
        sig = signals.get(key)
        if not sig:
            continue
        if sig.get("needs_review"):
            nr = sig["needs_review"]
            out.append({
                "reason": "needs_review",
                "label": nr.get("label", ""),
                "ref": nr.get("ref", ""),
                "rationale": nr.get("rationale", ""),
            })
        clarity = sig.get("clarity", {})
        if clarity.get("score", 1) < 0.5:
            out.append({
                "reason": "low_clarity",
                "label": "Guidance is ambiguous or generic",
                "rationale": clarity.get("reason", "Gather more evidence or specify context."),
            })
        for w in sig.get("weak_guidance_warnings", []):
            out.append({
                "reason": "weak_guidance",
                "label": w.get("message", ""),
                "rationale": w.get("improvement_hint", ""),
            })
    return out


def ambiguity_report(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Report of current ambiguity warnings and suggested clarifications."""
    root = _repo_root(repo_root)
    signals = build_quality_signals(root)
    warnings = signals.get("ambiguity_warnings", [])
    most = signals.get("most_ambiguous")
    return {
        "ambiguity_count": len(warnings),
        "most_ambiguous": most,
        "warnings": warnings,
        "summary": f"{len(warnings)} ambiguity warning(s). " + (
            f"Top: {most.get('message', '')[:100]}" if most else "None."
        ),
    }


def weak_guidance_report(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Report of weak or generic guidance and improvement hints."""
    root = _repo_root(repo_root)
    signals = build_quality_signals(root)
    all_weak: list[dict[str, Any]] = []
    for key in ("next_action_signal", "review_needed_signal"):
        sig = signals.get(key)
        if sig:
            all_weak.extend(sig.get("weak_guidance_warnings", []))
    next_g = next_best_action_guidance(root)
    weakest_surface = None
    if next_g and next_g.quality_signal.confidence.level == "low":
        weakest_surface = {
            "guide_id": next_g.guide_id,
            "kind": next_g.kind,
            "summary": next_g.summary,
            "confidence": next_g.quality_signal.confidence.level,
            "improvement": next_g.quality_signal.confidence.disclaimer or "Gather more evidence; run mission-control and act on a specific subsystem.",
        }
    return {
        "weak_guidance_count": len(all_weak),
        "weak_guidance_warnings": all_weak,
        "weakest_guidance_surface": weakest_surface,
        "summary": f"{len(all_weak)} weak guidance warning(s). " + (
            f"Weakest surface: {weakest_surface.get('kind', '')}" if weakest_surface else ""
        ),
    }


def next_recommended_guidance_improvement(repo_root: Path | str | None = None) -> dict[str, Any]:
    """Single next recommended improvement: reduce ambiguity or strengthen weakest surface."""
    root = _repo_root(repo_root)
    amb = ambiguity_report(root)
    weak = weak_guidance_report(root)
    if amb.get("ambiguity_count", 0) > 0 and amb.get("most_ambiguous"):
        m = amb["most_ambiguous"]
        return {
            "priority": "ambiguity",
            "message": m.get("message", ""),
            "suggested_action": m.get("suggested_clarification", "Run workflow-dataset mission-control for state."),
        }
    if weak.get("weakest_guidance_surface"):
        w = weak["weakest_guidance_surface"]
        return {
            "priority": "weak_guidance",
            "message": w.get("summary", ""),
            "suggested_action": w.get("improvement", "Gather evidence; run mission-control and act on a specific subsystem."),
        }
    return {
        "priority": "none",
        "message": "No high-priority guidance improvement.",
        "suggested_action": "Run workflow-dataset quality-signals and guidance next-action periodically.",
    }
