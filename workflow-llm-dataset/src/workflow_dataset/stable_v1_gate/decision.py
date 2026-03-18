"""
M50I–M50L: Final stable-v1 decision — map evidence + gate to approved / narrow / repair / reject.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from workflow_dataset.stable_v1_gate.models import (
    FinalEvidenceBundle,
    StableV1ReadinessGate,
    StableV1Decision,
    StableV1Recommendation,
    ConfidenceSummary,
)
from workflow_dataset.stable_v1_gate.gate import evaluate_stable_v1_gate
from workflow_dataset.stable_v1_gate.evidence import build_final_evidence_bundle


def _root(repo_root: Path | str | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).resolve()
    try:
        from workflow_dataset.path_utils import get_repo_root
        return Path(get_repo_root()).resolve()
    except Exception:
        return Path.cwd().resolve()


def build_stable_v1_decision(
    evidence: FinalEvidenceBundle | None = None,
    gate: StableV1ReadinessGate | None = None,
    repo_root: Path | str | None = None,
) -> StableV1Decision:
    """
    Produce final stable-v1 release decision from evidence and gate.
    Returns one of: stable_v1_approved, stable_v1_approved_narrow, not_yet_repair_required, not_yet_scope_narrow.
    """
    root = _root(repo_root)
    if evidence is None:
        evidence = build_final_evidence_bundle(root)
    if gate is None:
        gate = evaluate_stable_v1_gate(evidence=evidence, repo_root=root)

    now = datetime.now(timezone.utc)
    at_iso = now.isoformat()[:19] + "Z"

    evidence_refs = [
        "production_cut",
        "release_readiness",
        "launch_decision_pack",
        "stability_decision_pack",
        "v1_ops",
        "continuity_confidence",
        "deploy_health",
        "vertical_value",
    ]

    # Strongest evidence for: gate passed + launch/stability go
    strongest_for = ""
    if gate.passed:
        strongest_for = "Gate passed; production cut frozen; launch and stability decisions support go."
    elif evidence.production_cut_frozen and evidence.launch_recommended_decision in ("launch", "launch_narrowly"):
        strongest_for = "Production cut frozen and launch decision is go; resolve stability/readiness blockers."

    # Strongest evidence against: top blocker or decision
    strongest_against = ""
    if gate.blockers:
        strongest_against = gate.blockers[0].summary[:150]
    elif gate.warnings:
        strongest_against = f"{len(gate.warnings)} warning(s): " + (gate.warnings[0].summary[:100] if gate.warnings else "")

    if gate.passed and not gate.warnings:
        return StableV1Decision(
            recommendation=StableV1Recommendation.APPROVED.value,
            recommendation_label="Stable v1 approved",
            confidence_summary=ConfidenceSummary(
                confidence="high",
                rationale="All gate checks passed; no blockers or warnings. Product state meets v1 contract.",
                evidence_refs=evidence_refs,
                strongest_evidence_for=strongest_for or "All evidence supports stable v1.",
                strongest_evidence_against=strongest_against or "None.",
            ),
            narrow_condition="",
            next_required_action="Proceed with stable v1 release per runbook; run workflow-dataset v1-ops maintenance-pack for ongoing discipline.",
            generated_at_iso=at_iso,
        )

    if gate.passed and gate.warnings:
        narrow_condition = "; ".join(w.summary[:80] for w in gate.warnings[:3])
        return StableV1Decision(
            recommendation=StableV1Recommendation.APPROVED_NARROW.value,
            recommendation_label="Stable v1 approved with narrow conditions",
            confidence_summary=ConfidenceSummary(
                confidence="medium",
                rationale="Gate passed but warnings present; approve with narrow conditions and monitor.",
                evidence_refs=evidence_refs,
                strongest_evidence_for=strongest_for or "Gate passed.",
                strongest_evidence_against=narrow_condition[:200],
            ),
            narrow_condition=narrow_condition,
            next_required_action="Resolve or accept narrow conditions; run workflow-dataset stable-v1 report and v1-ops maintenance-pack.",
            generated_at_iso=at_iso,
        )

    # Not passed: distinguish repair vs scope narrow
    launch_ok = (evidence.launch_recommended_decision or "").strip().lower() in ("launch", "launch_narrowly")
    stability_ok = (evidence.stability_recommended_decision or "").strip().lower() in ("continue", "continue_with_watch", "narrow")

    if not evidence.production_cut_frozen:
        return StableV1Decision(
            recommendation=StableV1Recommendation.SCOPE_NARROW.value,
            recommendation_label="Not yet stable v1 — scope must narrow further",
            confidence_summary=ConfidenceSummary(
                confidence="high",
                rationale="Production cut is not frozen; lock scope and vertical before declaring stable v1.",
                evidence_refs=evidence_refs,
                strongest_evidence_for=strongest_for,
                strongest_evidence_against=strongest_against or "Production cut not frozen.",
            ),
            narrow_condition="Lock production cut for chosen vertical.",
            next_required_action="workflow-dataset production-cut lock; then re-run workflow-dataset stable-v1 gate.",
            generated_at_iso=at_iso,
        )

    # Repair required: blockers from launch or stability or release readiness
    return StableV1Decision(
        recommendation=StableV1Recommendation.REPAIR_REQUIRED.value,
        recommendation_label="Not yet stable v1 — repair required",
        confidence_summary=ConfidenceSummary(
            confidence="high",
            rationale="One or more gate blockers must be resolved before stable v1 can be approved.",
            evidence_refs=evidence_refs,
            strongest_evidence_for=strongest_for,
            strongest_evidence_against=strongest_against,
        ),
        narrow_condition="",
        next_required_action="Resolve blockers (workflow-dataset stable-v1 blockers); then re-run workflow-dataset stable-v1 gate.",
        generated_at_iso=at_iso,
    )
