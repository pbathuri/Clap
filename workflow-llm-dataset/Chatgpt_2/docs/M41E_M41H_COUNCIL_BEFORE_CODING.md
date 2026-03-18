# M41E–M41H Council-Based Evaluation — Before Coding

## 1. What evaluation/review structures already exist

- **Eval** (`eval/`): Runs (run_manifest.json), board_report (latest vs best), compare_runs, thresholds, recommendation (promote/hold/refine/revert), reconciliation. Single-suite benchmark scoring; no multi-perspective.
- **Reliability** (`reliability/`): Golden-path runs, outcomes (pass/degraded/blocked/fail), save_run, suggest_recovery. Harness for first-value path health; not council-style.
- **Safe adaptation** (`safe_adaptation/`): AdaptationCandidate, CohortBoundaryCheck, ReviewDecision (accept/reject/quarantine), QuarantineState, inspect_candidate, apply_within_boundaries. Single-operator review; boundary checks by cohort/surface; no multi-perspective scores.
- **Release readiness** (`release_readiness/`): Blockers, warnings, supportability, gates. Pre-launch; not improvement decisions.
- **Triage** (`triage/`): Issues, severity, cohort health, mitigation playbooks. Incident-side; not improvement-candidate evaluation.
- **Trust** (`trust/`): Cockpit, contracts, tiers, approval registry. Policy/approval; not scoring improvements.
- **Teaching/corrections** (`teaching/`, `corrections/`): Skills, corrections propose/apply. Feedback loop; no council.
- **Desktop bench / acceptance**: Run benchmark cases, acceptance journeys. Single-outcome runs.

## 2. Useful council-style patterns from llm-council (reference)

- **Multi-perspective first**: Multiple “judges” (in our case: perspectives like product_value, safety_trust, supportability, reliability, vertical_fit, operator_burden, adaptation_risk) each give an opinion/score.
- **Explicit ranking/synthesis**: A “Chairman” step synthesizes into one final answer. We map to: synthesis step that produces promote / promote_limited / quarantine / reject / needs_more_evidence / safe_experimental_only, with disagreement visible.
- **Anonymization for bias**: llm-council anonymizes model identity when peers rank. We don’t use LLM judges; our perspectives are fixed dimensions, so no anonymization. We *do* keep disagreement explicit (which perspective disagreed and why).
- **Stored conversations/state**: llm-council stores JSON. We store council reviews and decisions in `data/local/council/` (local-first).

## 3. Which council ideas fit safely

- **Multiple perspectives**: Fit. Separate scores for quality, safety/trust, supportability, reliability, vertical-value, operator burden, adaptation risk. Each perspective is a “member” with a criterion score and optional note.
- **Disagreement visible**: Fit. Disagreement notes and uncertainty notes as first-class; not collapsed.
- **Synthesis to a single recommendation**: Fit. One recommended decision per council review, with reason and list of disagreements/uncertainties.
- **Local-first, no cloud**: Fit. All inputs from existing local state (reliability, triage, safe_adaptation, trust, release_readiness); no OpenRouter or external judges.
- **Review flow for candidates**: Fit. Council can review adaptation candidates, eval runs, or generic “subjects” (experiment id, queue tuning, trusted-routine change, vertical workflow change, production-cut refinement).

## 4. Which do not fit and why

- **LLM-as-judge**: Not used. We do not call multiple LLMs to score; we use rule/evidence-based scoring from existing subsystems (reliability outcome, triage health, boundary check, trust posture, etc.).
- **OpenRouter/cloud API**: Not used. No cloud dependency for council operation.
- **Real-time chat UI**: Not used. Council is CLI + stored reviews + mission control visibility.
- **Replacing safe_adaptation or eval**: Not done. Council adds a layer that can *inform* adaptation review or eval interpretation; it does not replace accept/reject/quarantine or board recommendation.

## 5. Exact file plan

| Action | Path | Purpose |
|--------|------|--------|
| Create | `src/workflow_dataset/council/__init__.py` | Exports |
| Create | `src/workflow_dataset/council/models.py` | EvaluationCouncil, EvaluationPerspective, CouncilMember, CriterionScore, DisagreementNote, UncertaintyNote, PromotionRecommendation, QuarantineRecommendation, EvidenceSummary, CouncilSubject, CouncilReview, SynthesisDecision |
| Create | `src/workflow_dataset/council/perspectives.py` | Perspective registry (product_value, safety_trust, supportability, reliability, vertical_fit, operator_burden, adaptation_risk); score_subject_from_perspective(subject, perspective_id, repo_root) → CriterionScore + optional notes |
| Create | `src/workflow_dataset/council/review.py` | run_council_review(subject_id, subject_type, repo_root) → CouncilReview (all perspective scores, disagreement/uncertainty notes, evidence summary); persist to data/local/council/reviews/ |
| Create | `src/workflow_dataset/council/synthesis.py` | synthesize_decision(review) → promotion/quarantine/reject/limited/needs_evidence/safe_experimental; disagreement visible in output |
| Create | `src/workflow_dataset/council/store.py` | save_review, load_review, list_reviews, get_review_by_subject |
| Modify | `src/workflow_dataset/cli.py` | council_group: list, review --id, report --id, decision --id, disagreement --id |
| Modify | `src/workflow_dataset/mission_control/state.py` | council_state: active_reviews_count, highest_risk_pending, disagreement_heavy_candidate, latest_promoted, latest_quarantined |
| Modify | `src/workflow_dataset/mission_control/report.py` | [Council] section |
| Create | `tests/test_council.py` | Model creation, perspective scoring, disagreement, synthesis, low-evidence, conflicting outcomes |
| Create | `docs/M41E_M41H_COUNCIL_DELIVERABLE.md` | Files, mapping from llm-council, samples, tests, gaps |

## 6. Safety/risk note

- Council output is **advisory**. It does not auto-accept or auto-quarantine adaptations; the operator (or existing safe_adaptation flow) still decides. Council reduces single-metric mistakes by surfacing multiple perspectives and disagreement.
- Disagreement and uncertainty are **never hidden** in reports or decisions.
- No cloud or LLM calls in the default council path; all inputs from local state. Optional future: allow pluggable “scorer” that could call a local model, but not required for M41.

## 7. What this block will NOT do

- Will not replace the current evaluation stack (eval board, reliability harness, acceptance).
- Will not replace safe_adaptation accept/reject/quarantine; will add a council review that can be run for an adaptation and inform the operator.
- Will not add cloud judge orchestration or OpenRouter.
- Will not assume multi-judge is always better; we surface disagreement so operators can weigh it.
- Will not hide low evidence or conflicting perspectives; “needs_more_evidence” and “safe_experimental_only” are first-class outcomes.
