"""
M41E–M41H: Council decision synthesis — promote / quarantine / reject / limited / needs evidence / safe experimental.
M41H.1: Preset thresholds and policy overrides for clearer limited vs quarantine vs reject.
Disagreement is visible, not collapsed.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.council.models import (
    CouncilReview,
    CouncilPreset,
    CriterionScore,
    DisagreementNote,
    UncertaintyNote,
    SynthesisDecision,
    PromotionRecommendation,
    QuarantineRecommendation,
    EvidenceSummary,
)
from workflow_dataset.council.presets import get_default_preset


def synthesize_decision(
    review: CouncilReview,
    preset: CouncilPreset | None = None,
    policy_outcome_override: str | None = None,
) -> CouncilReview:
    """
    Set synthesis_decision, synthesis_reason, promotion/quarantine recommendations.
    If preset is provided, use its thresholds and rules. If policy_outcome_override is set
    (quarantine, reject, limited_rollout, experimental_only), apply it for clearer rules.
    """
    preset = preset or get_default_preset()
    scores = review.criterion_scores
    min_promote = preset.min_score_to_promote
    pass_count = sum(1 for s in scores if s.pass_threshold)
    fail_count = len(scores) - pass_count
    avg_score = sum(s.score for s in scores) / len(scores) if scores else 0.0

    disagreements = list(review.disagreement_notes)
    uncertainties = list(review.uncertainty_notes)

    # Detect disagreement: large spread or fail on safety/trust/adaptation_risk
    low_scores = [s for s in scores if s.score < 0.5]
    safety_trust_score = next((s for s in scores if s.perspective_id == "safety_trust"), None)
    adaptation_risk_score = next((s for s in scores if s.perspective_id == "adaptation_risk"), None)
    if safety_trust_score and safety_trust_score.score < 0.5 and not any(d.description.startswith("Safety/trust") for d in disagreements):
        disagreements.append(DisagreementNote(
            note_id="safety_low",
            description="Safety/trust perspective scores below threshold.",
            perspective_ids=["safety_trust"],
            severity="high",
        ))
    if adaptation_risk_score and adaptation_risk_score.score < 0.5 and not any(d.description.startswith("Adaptation risk") for d in disagreements):
        disagreements.append(DisagreementNote(
            note_id="adaptation_risk_low",
            description="Adaptation risk perspective scores below threshold.",
            perspective_ids=["adaptation_risk"],
            severity="high",
        ))
    if fail_count >= 2 and pass_count >= 2 and not any("mixed" in d.description.lower() for d in disagreements):
        disagreements.append(DisagreementNote(
            note_id="mixed_scores",
            description="Mixed pass/fail across perspectives; review each dimension.",
            perspective_ids=[s.perspective_id for s in scores if not s.pass_threshold],
            severity="medium",
        ))

    # Low evidence uncertainty
    ev_count = review.evidence_summary.evidence_count
    min_evidence = preset.min_evidence_to_promote
    if ev_count < min_evidence and preset.needs_evidence_if_low_evidence and not any("evidence" in u.description.lower() for u in uncertainties):
        uncertainties.append(UncertaintyNote(
            note_id="low_evidence",
            description=f"Evidence count {ev_count} below preset minimum {min_evidence}; consider gathering more before promote.",
            suggested_action="needs_more_evidence",
        ))

    # Policy override: apply first for clearer limited vs quarantine vs reject
    if policy_outcome_override == "reject":
        decision = SynthesisDecision.REJECT
        reason = "Promotion policy: reject (e.g. trust change or high risk)."
        promotion = PromotionRecommendation(recommend=False)
        quarantine = QuarantineRecommendation(recommend=False)
        review.disagreement_notes = disagreements
        review.uncertainty_notes = uncertainties
        review.synthesis_decision = decision.value
        review.synthesis_reason = reason
        review.promotion_recommendation = promotion
        review.quarantine_recommendation = quarantine
        return review
    if policy_outcome_override == "quarantine":
        decision = SynthesisDecision.QUARANTINE
        reason = "Promotion policy: quarantine for review."
        promotion = PromotionRecommendation(recommend=False)
        quarantine = QuarantineRecommendation(recommend=True, reason=reason, review_by_hint="Address policy condition then re-run council.")
        review.disagreement_notes = disagreements
        review.uncertainty_notes = uncertainties
        review.synthesis_decision = decision.value
        review.synthesis_reason = reason
        review.promotion_recommendation = promotion
        review.quarantine_recommendation = quarantine
        return review
    if policy_outcome_override == "limited_rollout" and preset.allow_limited_rollout:
        decision = SynthesisDecision.PROMOTE_LIMITED_COHORT
        reason = "Promotion policy: limited rollout only."
        promotion = PromotionRecommendation(recommend=True, scope="limited_cohort", reason=reason)
        quarantine = QuarantineRecommendation(recommend=False)
        review.disagreement_notes = disagreements
        review.uncertainty_notes = uncertainties
        review.synthesis_decision = decision.value
        review.synthesis_reason = reason
        review.promotion_recommendation = promotion
        review.quarantine_recommendation = quarantine
        return review
    if policy_outcome_override == "experimental_only" and preset.allow_safe_experimental_only:
        decision = SynthesisDecision.SAFE_EXPERIMENTAL_ONLY
        reason = "Promotion policy: safe only in experimental surfaces."
        promotion = PromotionRecommendation(recommend=True, scope="experimental_only", reason=reason)
        quarantine = QuarantineRecommendation(recommend=False)
        review.disagreement_notes = disagreements
        review.uncertainty_notes = uncertainties
        review.synthesis_decision = decision.value
        review.synthesis_reason = reason
        review.promotion_recommendation = promotion
        review.quarantine_recommendation = quarantine
        return review

    # Required perspectives (preset)
    required = preset.required_perspectives_pass
    if required:
        for pid in required:
            s = next((x for x in scores if x.perspective_id == pid), None)
            if s and not s.pass_threshold:
                if pid == "safety_trust" and s.score < preset.reject_if_safety_below:
                    decision = SynthesisDecision.REJECT
                    reason = f"Preset requires safety_trust; score {s.score} below reject threshold."
                    promotion = PromotionRecommendation(recommend=False)
                    quarantine = QuarantineRecommendation(recommend=False)
                    review.disagreement_notes = disagreements
                    review.uncertainty_notes = uncertainties
                    review.synthesis_decision = decision.value
                    review.synthesis_reason = reason
                    review.promotion_recommendation = promotion
                    review.quarantine_recommendation = quarantine
                    return review
                if pid == "adaptation_risk" and s.score < preset.quarantine_if_adaptation_risk_below:
                    decision = SynthesisDecision.QUARANTINE
                    reason = f"Preset: adaptation_risk below quarantine threshold."
                    promotion = PromotionRecommendation(recommend=False)
                    quarantine = QuarantineRecommendation(recommend=True, reason=reason)
                    review.disagreement_notes = disagreements
                    review.uncertainty_notes = uncertainties
                    review.synthesis_decision = decision.value
                    review.synthesis_reason = reason
                    review.promotion_recommendation = promotion
                    review.quarantine_recommendation = quarantine
                    return review

    # Decide (original logic with preset thresholds)
    if fail_count == 0 and ev_count >= min_evidence and not disagreements:
        decision = SynthesisDecision.PROMOTE
        reason = "All perspectives pass; sufficient evidence."
        promotion = PromotionRecommendation(recommend=True, scope="full", reason=reason)
        quarantine = QuarantineRecommendation(recommend=False)
    elif fail_count == 0 and (ev_count < min_evidence or disagreements):
        if preset.quarantine_if_any_high_severity_disagreement and any(d.severity == "high" for d in disagreements):
            decision = SynthesisDecision.QUARANTINE
            reason = "Disagreement or uncertainty; quarantine for review."
            promotion = PromotionRecommendation(recommend=False)
            quarantine = QuarantineRecommendation(recommend=True, reason=reason, review_by_hint="Resolve disagreement then re-run council.")
        else:
            decision = SynthesisDecision.NEEDS_MORE_EVIDENCE
            reason = "Pass but low evidence or minor disagreement; gather more evidence."
            promotion = PromotionRecommendation(recommend=False)
            quarantine = QuarantineRecommendation(recommend=False)
    elif safety_trust_score and safety_trust_score.score < preset.reject_if_safety_below:
        decision = SynthesisDecision.REJECT
        reason = f"Safety/trust below preset threshold ({preset.reject_if_safety_below}); reject."
        promotion = PromotionRecommendation(recommend=False)
        quarantine = QuarantineRecommendation(recommend=False)
    elif adaptation_risk_score and adaptation_risk_score.score < preset.quarantine_if_adaptation_risk_below:
        decision = SynthesisDecision.QUARANTINE
        reason = "Adaptation risk high; quarantine."
        promotion = PromotionRecommendation(recommend=False)
        quarantine = QuarantineRecommendation(recommend=True, reason=reason)
    elif fail_count <= 1 and avg_score >= min_promote and preset.allow_limited_rollout:
        decision = SynthesisDecision.PROMOTE_LIMITED_COHORT
        reason = "Mostly pass; promote in limited cohort only (preset allows limited rollout)."
        promotion = PromotionRecommendation(recommend=True, scope="limited_cohort", reason=reason)
        quarantine = QuarantineRecommendation(recommend=False)
    elif fail_count >= 1 and all(s.perspective_id in ("vertical_fit", "operator_burden") for s in low_scores) and preset.allow_safe_experimental_only:
        decision = SynthesisDecision.SAFE_EXPERIMENTAL_ONLY
        reason = "Safe only in experimental surfaces (preset allows safe experimental)."
        promotion = PromotionRecommendation(recommend=True, scope="experimental_only", reason=reason)
        quarantine = QuarantineRecommendation(recommend=False)
    else:
        decision = SynthesisDecision.QUARANTINE
        reason = f"Fail count={fail_count}; quarantine for review."
        promotion = PromotionRecommendation(recommend=False)
        quarantine = QuarantineRecommendation(recommend=True, reason=reason)

    review.disagreement_notes = disagreements
    review.uncertainty_notes = uncertainties
    review.synthesis_decision = decision.value
    review.synthesis_reason = reason
    review.promotion_recommendation = promotion
    review.quarantine_recommendation = quarantine
    return review
