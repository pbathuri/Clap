"""
M47L.1: Operator-facing summary — what the system knows, what it recommends, what it needs from the user.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workflow_dataset.quality_guidance.models import OperatorFacingSummary
from workflow_dataset.quality_guidance.guidance import (
    next_best_action_guidance,
    blocked_state_guidance,
    resume_guidance,
    support_recovery_guidance,
)
from workflow_dataset.quality_guidance.presets import load_active_preset, apply_preset_to_guidance
from workflow_dataset.quality_guidance.recovery_packs import (
    get_recovery_pack_for_failure_pattern,
    get_recovery_pack_for_vertical,
)


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_operator_summary(
    repo_root: Path | str | None = None,
    failure_pattern: str = "",
    vertical_id: str = "",
) -> OperatorFacingSummary:
    """
    Build operator-facing summary: what the system knows, what it recommends, what it needs from the user.
    Uses active preset to format; uses recovery pack when failure_pattern or vertical_id matches.
    """
    root = _repo_root(repo_root)
    preset = load_active_preset(root)
    knows: list[str] = []
    recommends: list[str] = []
    needs: list[str] = []

    # Recovery pack takes precedence when we have a matching failure or vertical
    pack = None
    if failure_pattern:
        pack = get_recovery_pack_for_failure_pattern(failure_pattern, root)
    if not pack and vertical_id:
        pack = get_recovery_pack_for_vertical(vertical_id, root)
    if pack:
        knows.append(pack.what_we_know)
        recommends.append(pack.what_we_recommend)
        needs.append(pack.what_we_need_from_user)

    # Add from current guidance
    for fn in [resume_guidance, blocked_state_guidance, next_best_action_guidance]:
        try:
            g = fn(repo_root=root)
            if not g:
                continue
            summary, rationale = apply_preset_to_guidance(g, preset)
            knows.append(rationale[:200] if rationale else "")
            recommends.append(summary)
            if g.action_ref:
                recommends.append(g.action_ref[:100])
            if g.quality_signal.confidence.disclaimer:
                needs.append(g.quality_signal.confidence.disclaimer)
            if g.quality_signal.needs_review:
                needs.append(f"Review: {g.quality_signal.needs_review.label}")
        except Exception:
            continue
    try:
        g = support_recovery_guidance(vertical_id=vertical_id or "", repo_root=root)
        if g:
            summary, rationale = apply_preset_to_guidance(g, preset)
            knows.append(rationale[:200] if rationale else "")
            recommends.append(summary)
            if g.action_ref:
                recommends.append(g.action_ref[:100])
            if g.quality_signal.confidence.disclaimer:
                needs.append(g.quality_signal.confidence.disclaimer)
            if g.quality_signal.needs_review:
                needs.append(f"Review: {g.quality_signal.needs_review.label}")
    except Exception:
        pass

    # Dedupe and join
    def _uniq(lines: list[str]) -> str:
        seen: set[str] = set()
        out: list[str] = []
        for s in lines:
            s = (s or "").strip()
            if s and s not in seen:
                seen.add(s)
                out.append(s)
        return " ".join(out)[:500] if out else ""

    return OperatorFacingSummary(
        what_system_knows=_uniq(knows) or "No specific context loaded.",
        what_it_recommends=_uniq(recommends) or "Run workflow-dataset quality-signals or guidance next-action.",
        what_it_needs_from_user=_uniq(needs) or "No specific input required; review guidance and act.",
        evidence_refs=["guidance", "preset", "recovery_pack"],
        preset_id=preset.preset_id,
        recovery_pack_id=pack.pack_id if pack else "",
    )
