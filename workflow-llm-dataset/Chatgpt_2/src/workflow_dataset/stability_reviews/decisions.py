"""
M46I–M46L: Decision outputs — continue/narrow/repair/pause/rollback with rationale and evidence links.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.stability_reviews.models import (
    StabilityDecision,
    StabilityDecisionPack,
)


def build_decision_output(pack: StabilityDecisionPack) -> dict[str, Any]:
    """
    Produce first-draft decision output: decision, label, rationale, evidence_links, recommended_actions.
    """
    decision = pack.recommended_decision or StabilityDecision.PAUSE.value
    evidence_links = list(pack.evidence_refs or [])
    if pack.evidence_bundle:
        evidence_links.append("evidence_bundle")

    if decision == StabilityDecision.CONTINUE.value:
        label = "Continue as-is"
        actions = [
            "Schedule next sustained deployment review (e.g. workflow-dataset stability-reviews generate).",
            "Run production-runbook review-cycle and sustained-use checkpoint per runbook.",
        ]
        rec = pack.continue_rec
        rationale = rec.rationale if rec else pack.rationale

    elif decision == StabilityDecision.CONTINUE_WITH_WATCH.value:
        label = "Continue with watch state"
        actions = [
            "Do not expand scope until evidence strengthens.",
            "Run workflow-dataset stability-reviews generate on next window.",
            "Monitor triage and reliability; re-run stability-decision-pack if conditions change.",
        ]
        rec = pack.continue_rec
        rationale = rec.rationale if rec else pack.rationale

    elif decision == StabilityDecision.NARROW.value:
        label = "Narrow supported scope"
        actions = [
            "Restrict to current cohort/scope; do not add new users or expand until issues resolved.",
            "Run workflow-dataset release triage; address high-severity issues.",
            "Re-run stability-reviews generate after narrowing.",
        ]
        rec = pack.narrow_rec
        rationale = rec.rationale if rec else pack.rationale
        if rec and rec.suggested_scope_note:
            actions.insert(0, rec.suggested_scope_note)

    elif decision == StabilityDecision.REPAIR.value:
        label = "Run repair bundle"
        actions = [
            "Execute repair bundle (workflow-dataset launch-decision pack; address blockers).",
            "Re-run production gates and post-deployment guidance after repair.",
            "Run workflow-dataset stability-reviews generate to re-evaluate.",
        ]
        rec = pack.repair_rec
        rationale = rec.rationale if rec else pack.rationale
        if rec and rec.repair_bundle_ref:
            actions[0] = f"Execute repair: {rec.repair_bundle_ref}"

    elif decision == StabilityDecision.PAUSE.value:
        label = "Pause deployment"
        actions = [
            "Do not promote or expand deployment until blockers resolved.",
            "Resolve blockers; re-run launch-decision pack and stability-reviews generate.",
        ]
        rec = pack.pause_rec
        rationale = rec.rationale if rec else pack.rationale
        if rec and rec.resume_condition:
            actions.append(f"Resume when: {rec.resume_condition}")

    elif decision == StabilityDecision.ROLLBACK.value:
        label = "Rollback to prior stable state"
        actions = [
            "Evaluate prior stable state (review_id or checkpoint); execute rollback per runbook.",
            "Do not rely on this layer to execute rollback—operator decision required.",
            "After rollback, run workflow-dataset stability-reviews generate.",
        ]
        rec = pack.rollback_rec
        rationale = rec.rationale if rec else pack.rationale
        if rec and rec.prior_stable_ref:
            actions[0] = f"Prior stable ref: {rec.prior_stable_ref}. " + actions[0]
    else:
        label = "Unknown"
        actions = ["Run workflow-dataset stability-decision explain for details."]
        rationale = pack.rationale

    return {
        "decision": decision,
        "label": label,
        "rationale": rationale,
        "evidence_links": evidence_links,
        "recommended_actions": actions,
        "generated_at_iso": pack.generated_at_iso,
        "vertical_id": pack.vertical_id,
    }


def explain_stability_decision(
    pack: StabilityDecisionPack | None = None,
    repo_root: str | None = None,
) -> str:
    """Human-readable explanation of the stability decision (why continue/narrow/repair/pause/rollback)."""
    if pack is None:
        from workflow_dataset.stability_reviews.pack_builder import build_stability_decision_pack
        pack = build_stability_decision_pack(repo_root)
    out = build_decision_output(pack)
    lines = [
        f"Stability decision: {out['decision']} — {out['label']}",
        "",
        f"Rationale: {out['rationale']}",
        "",
        "Evidence links: " + ", ".join(out["evidence_links"]),
        "",
        "Recommended actions:",
    ]
    for a in out["recommended_actions"]:
        lines.append(f"  - {a}")
    if pack.evidence_bundle:
        lines.append("")
        lines.append("Evidence summary: " + (pack.evidence_bundle.health_summary or "—")[:200])
    return "\n".join(lines)
