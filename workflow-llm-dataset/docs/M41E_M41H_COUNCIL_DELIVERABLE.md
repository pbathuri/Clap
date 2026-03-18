# M41E–M41H Council-Based Evaluation — Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `council` group: `list`, `review --id --type`, `report --id`, `decision --id`, `disagreement --id`. |
| `src/workflow_dataset/mission_control/state.py` | Added `council` block: `active_reviews_count`, `highest_risk_pending_subject_id`, `disagreement_heavy_candidate_id`, `latest_promoted_subject_id`, `latest_quarantined_subject_id`. |
| `src/workflow_dataset/mission_control/report.py` | Added `[Council]` section: reviews count, high_risk, promoted, quarantined. |

## 2. Files created

| File | Purpose |
|------|--------|
| `docs/M41E_M41H_COUNCIL_BEFORE_CODING.md` | Before-coding: existing structures, llm-council patterns, fit/not fit, file plan, safety, will NOT do. |
| `src/workflow_dataset/council/__init__.py` | Package exports. |
| `src/workflow_dataset/council/models.py` | EvaluationCouncil, EvaluationPerspective, CouncilMember, CriterionScore, DisagreementNote, UncertaintyNote, PromotionRecommendation, QuarantineRecommendation, EvidenceSummary, CouncilSubject, CouncilReview, SynthesisDecision. |
| `src/workflow_dataset/council/perspectives.py` | Default council, get_perspective, score_subject_from_perspective (adaptation + generic; uses safe_adaptation, reliability, release_readiness, trust, vertical_selection). |
| `src/workflow_dataset/council/review.py` | run_council_review(subject_id, subject_type, ref, …), build_disagreement_report. |
| `src/workflow_dataset/council/synthesis.py` | synthesize_decision(review) → promote / promote_limited / quarantine / reject / needs_more_evidence / safe_experimental_only; disagreement and uncertainty notes added. |
| `src/workflow_dataset/council/store.py` | save_review, load_review, list_reviews, get_review_by_subject; persistence under data/local/council/reviews/. |
| `tests/test_council.py` | 8 tests: default_council, get_perspective, score_subject_generic, run_council_review_persist, load_and_list, disagreement_report, synthesis_low_evidence, synthesis_conflicting_perspectives. |
| `docs/M41E_M41H_COUNCIL_DELIVERABLE.md` | This deliverable. |

## 3. Exact mapping from llm-council ideas to the current product

| llm-council idea | Our implementation |
|------------------|--------------------|
| Multiple “judges” give opinions | **Perspectives** (product_value, safety_trust, supportability, reliability, vertical_fit, operator_burden, adaptation_risk): each scores 0–1 with detail; no LLM judges, scores from existing local subsystems. |
| Stage 1 first opinions | **CriterionScore** per perspective via `score_subject_from_perspective()`; adaptation uses boundary + evidence; generic uses reliability, release_readiness, trust, vertical. |
| Stage 2 peer review / ranking | **DisagreementNote** and **UncertaintyNote** when perspectives disagree or evidence is low; synthesis step detects safety/adaptation_risk below threshold and mixed pass/fail. |
| Stage 3 Chairman synthesis | **synthesize_decision()** produces one of: promote, promote_in_limited_cohort, quarantine, reject, needs_more_evidence, safe_only_in_experimental_surfaces; reason + promotion/quarantine recommendations. |
| Anonymization to reduce bias | Not used (we have fixed perspectives, not LLM identities). **Disagreement is visible** in reports and in `council disagreement --id`. |
| Stored state | **data/local/council/reviews/<review_id>.json**; list_reviews, get_review_by_subject. |
| Cloud (OpenRouter) | **Not used**; council is local-first, no external API. |

## 4. Sample council review

```json
{
  "review_id": "cr_abc123def456",
  "subject": {
    "subject_id": "exp_123",
    "subject_type": "experiment",
    "ref": "exp_123",
    "summary": "experiment exp_123"
  },
  "at_iso": "2025-03-16T15:00:00Z",
  "criterion_scores": [
    {"perspective_id": "product_value", "score": 0.5, "label": "Product value", "detail": "generic; run eval board or adaptation for value signal", "pass_threshold": true},
    {"perspective_id": "safety_trust", "score": 0.8, "label": "Safety / trust", "detail": "registry_exists", "pass_threshold": true},
    {"perspective_id": "supportability", "score": 0.5, "label": "Supportability", "detail": "readiness degraded", "pass_threshold": true},
    {"perspective_id": "reliability", "score": 0.9, "label": "Reliability", "detail": "reliability pass", "pass_threshold": true},
    {"perspective_id": "vertical_fit", "score": 0.7, "label": "Vertical fit", "detail": "vertical=founder_operator_core", "pass_threshold": true},
    {"perspective_id": "operator_burden", "score": 0.6, "label": "Operator burden", "detail": "generic; no specific burden signal", "pass_threshold": true},
    {"perspective_id": "adaptation_risk", "score": 0.5, "label": "Adaptation risk", "detail": "no specific signal", "pass_threshold": true}
  ],
  "disagreement_notes": [],
  "uncertainty_notes": [{"note_id": "low_evidence", "description": "Evidence count low; consider gathering more before promote.", "suggested_action": "needs_more_evidence"}],
  "evidence_summary": {"source_ids": ["exp_123"], "summary": "subject_type=experiment ref=exp_123", "evidence_count": 1},
  "synthesis_decision": "needs_more_evidence",
  "synthesis_reason": "Pass but low evidence or minor disagreement; gather more evidence.",
  "promotion_recommendation": {"recommend": false, "scope": "full", "reason": ""},
  "quarantine_recommendation": {"recommend": false, "reason": "", "review_by_hint": ""}
}
```

## 5. Sample disagreement report

```json
{
  "review_id": "cr_abc123",
  "subject_id": "adapt_xyz",
  "synthesis_decision": "quarantine",
  "synthesis_reason": "Adaptation risk high; quarantine.",
  "disagreement_notes": [
    {"note_id": "adaptation_risk_low", "description": "Adaptation risk perspective scores below threshold.", "perspective_ids": ["adaptation_risk"], "severity": "high"}
  ],
  "uncertainty_notes": [],
  "scores_below_threshold": [
    {"perspective_id": "adaptation_risk", "score": 0.2, "detail": "must_quarantine true"}
  ]
}
```

## 6. Sample final decision output

```
Subject: adapt_xyz (adaptation)
Decision: quarantine
Reason: Adaptation risk high; quarantine.
Quarantine: Adaptation risk high; quarantine.
```

CLI: `workflow-dataset council decision --id adapt_xyz`

## 7. Exact tests run

```bash
python3 -m pytest tests/test_council.py -v
```

- test_default_council  
- test_get_perspective  
- test_score_subject_generic  
- test_run_council_review_persist  
- test_load_and_list_reviews  
- test_disagreement_report  
- test_synthesis_low_evidence  
- test_synthesis_conflicting_perspectives  

**8 passed.**

## 8. Exact remaining gaps for later refinement

- **Learning-lab / experiment IDs**: Council accepts subject_type=experiment and ref=id; no dedicated learning-lab store yet. When learning-lab experiments are persisted, wire subject_id/ref to that store for evidence_summary.
- **Eval-run subject type**: score_subject_from_perspective for subject_type=eval_run could load run manifest and use board/thresholds for product_value and reliability; currently generic.
- **Queue/calmness and trusted-routine subjects**: No dedicated scorers yet; they use generic repo signals. Add light-weight scorers when those flows expose structured state.
- **Weighted synthesis**: Council members have weight=1.0; synthesis could use weights for “safety_trust and adaptation_risk count more”.
- **Operator override**: Council output is advisory; no explicit “operator overrode council to promote” audit trail in council store.
- **Mission control “disagreement-heavy”**: Currently uses quarantine/reject as proxy; could compute from stored review’s disagreement_notes count when loading full review.
