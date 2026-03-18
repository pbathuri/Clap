"""
M50I–M50L: Evaluate stable-v1 gate from final evidence — blockers, warnings, passed.
"""

from __future__ import annotations

from pathlib import Path

from workflow_dataset.stable_v1_gate.models import (
    FinalEvidenceBundle,
    StableV1ReadinessGate,
    GateBlocker,
    GateWarning,
)
from workflow_dataset.stable_v1_gate.evidence import build_final_evidence_bundle


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def evaluate_stable_v1_gate(
    evidence: FinalEvidenceBundle | None = None,
    repo_root: Path | str | None = None,
) -> StableV1ReadinessGate:
    """
    Evaluate the stable-v1 gate from evidence. Produces blockers and warnings.
    Gate passes only when there are no blockers.
    """
    if evidence is None:
        evidence = build_final_evidence_bundle(repo_root)

    blockers: list[GateBlocker] = []
    warnings: list[GateWarning] = []

    # Blockers: conditions that must be true for stable v1
    if not evidence.production_cut_frozen:
        blockers.append(GateBlocker(
            id="production_cut_not_frozen",
            summary="Production cut is not frozen; no vertical locked.",
            source="production_cut",
            remediation_hint="Lock production cut for chosen vertical: workflow-dataset production-cut lock.",
            severity="blocker",
        ))

    if evidence.release_readiness_status == "blocked":
        blockers.append(GateBlocker(
            id="release_readiness_blocked",
            summary="Release readiness is blocked.",
            source="release_readiness",
            remediation_hint="Resolve release blockers: workflow-dataset release readiness.",
            severity="blocker",
        ))

    launch_decision = (evidence.launch_recommended_decision or "").strip().lower()
    if launch_decision in ("pause", "repair_and_review"):
        blockers.append(GateBlocker(
            id="launch_decision_not_go",
            summary=f"Launch decision is {evidence.launch_recommended_decision}; must be launch or launch_narrowly for stable v1.",
            source="launch_decision_pack",
            remediation_hint="Address launch-decision-pack blockers; run workflow-dataset launch-decision-pack.",
            severity="blocker",
        ))

    stability_decision = (evidence.stability_recommended_decision or "").strip().lower()
    if stability_decision in ("pause", "rollback", "repair"):
        blockers.append(GateBlocker(
            id="stability_decision_not_go",
            summary=f"Stability decision is {evidence.stability_recommended_decision}; must be continue or narrow for stable v1.",
            source="stability_reviews",
            remediation_hint="Address stability pack; run workflow-dataset stability-reviews generate and stability-decision.",
            severity="blocker",
        ))

    # Warnings: may lead to narrow or repair
    if evidence.release_readiness_status == "degraded":
        warnings.append(GateWarning(
            id="release_readiness_degraded",
            summary="Release readiness is degraded (warnings present).",
            source="release_readiness",
        ))

    if launch_decision == "launch_narrowly":
        warnings.append(GateWarning(
            id="launch_narrowly",
            summary="Launch decision is launch_narrowly; stable v1 may be approved with narrow conditions.",
            source="launch_decision_pack",
        ))

    if stability_decision in ("narrow", "continue_with_watch"):
        warnings.append(GateWarning(
            id="stability_narrow_or_watch",
            summary=f"Stability decision is {evidence.stability_recommended_decision}; consider narrow or watch conditions.",
            source="stability_reviews",
        ))

    if not evidence.v1_ops_posture_summary or "error" in evidence.v1_ops_posture_summary:
        warnings.append(GateWarning(
            id="v1_ops_posture_unknown",
            summary="V1 ops posture could not be determined.",
            source="v1_ops",
        ))

    if "error" in (evidence.migration_continuity_readiness or ""):
        warnings.append(GateWarning(
            id="continuity_guidance_error",
            summary="Migration/continuity guidance could not be built.",
            source="continuity_confidence",
        ))

    passed = len(blockers) == 0
    summary = "Stable v1 gate passed; no blockers." if passed else f"Stable v1 gate not passed: {len(blockers)} blocker(s), {len(warnings)} warning(s)."

    return StableV1ReadinessGate(
        passed=passed,
        blockers=blockers,
        warnings=warnings,
        summary=summary,
    )
