# M42I–M42L — Benchmark Board + Promotion/Rollback Pipeline: Before Coding

## 1. What benchmarking/promotion/rollback structures already exist

- **Eval** (`eval/`): `list_runs`, `get_run`, `compare_runs`, `compare_latest_vs_best`, `board_report`; recommendation promote/hold/refine/revert; `reconcile_run` (verdict: promote|hold|refine|revert); thresholds; runs under `data/local/eval/runs/<run_id>/run_manifest.json`. Single-suite benchmark; runs are workflow runs (no explicit baseline vs candidate *model* in manifest).
- **Council** (`council/`): `CouncilReview`, `CouncilSubject`, `CriterionScore`, `DisagreementNote`, `PromotionRecommendation` (scope: full|limited_cohort|experimental_only), `QuarantineRecommendation`, `SynthesisDecision` (promote, promote_in_limited_cohort, quarantine, reject, needs_more_evidence, safe_only_in_experimental_surfaces). Perspectives: product_value, safety_trust, supportability, reliability, vertical_fit, operator_burden, adaptation_risk. `run_council_review(subject_id, subject_type)`, `synthesize_decision`, reviews under `data/local/council/reviews/`. Subject-based; not model-run comparison.
- **Safe adaptation** (`safe_adaptation/`): `AdaptationCandidate`, `quarantine_candidate`, `accept_candidate`, `reject_candidate`, `apply_within_boundaries`; `list_quarantined`. Evidence/candidate-based; not benchmark-score based.
- **Runtime mesh** (`runtime_mesh/`): `model_catalog` (ModelEntry: model_id, capability_classes), `backend_registry`, policy by task_class. No “promote model to production route” today.
- **Production cut** (`production_cut/`): Freeze with included/excluded/quarantined *surfaces*; no model selection.
- **Release** (`release/`, `install_upgrade/`): Rollback checkpoints, upgrade/rollback; deployment-level, not model-level.
- **Incubator** (`incubator/`): Candidates by stage (idea → benchmarked → cohort_tested → promoted), `evaluate_gates`, `promotion_report`; lightweight gates.
- **Desktop benchmark** (`desktop_bench/`): Cases, run_benchmark, board, trust status; task-level, not model comparison.

---

## 2. What useful repo patterns fit this layer

- **Eval compare_runs**: Already produces regressions, improvements, recommendation. Reuse as the *core comparison*; extend with explicit dimensions (task success, safety, supportability, reliability, latency, operator burden, cohort compatibility) and a *scorecard* view.
- **Council perspectives**: Same dimension set (product_value, safety_trust, supportability, reliability, vertical_fit, operator_burden, adaptation_risk). Benchmark scorecard can align with these; council can consume scorecard as evidence for a subject.
- **Reconciliation verdict**: promote/hold/refine/revert maps to pipeline actions: promote (if thresholds pass), quarantine (hold), reject (revert), refine (needs more evidence).
- **Karpathy-style (reference only)**: Staged pipeline (run baseline run → run candidate run → compare → scorecard); result logging; explicit recommendation. We adopt the *discipline* (compare two runs, record dimensions, explicit recommendation) without vendoring; no cloud, no auto-promotion.

---

## 3. Which do not fit and why

- **Cloud leaderboards / external benchmark zoo**: Local-first only; no external dependency chains.
- **Automatic production promotion**: Every promotion step must be explicit and operator/review triggered.
- **Replacing council or safe_adaptation**: Council stays the multi-perspective decision layer; safe_adaptation stays the adaptation-candidate layer. Benchmark board *feeds* council (e.g. subject_type=benchmark_run, ref=scorecard_id) and can *reference* runtime model selection without replacing it.
- **Replacing eval harness/board**: Eval remains the run/compare engine; we add a *model-centric* board (baseline vs candidate) and *scorecard + pipeline* on top.
- **Blurring stable vs experimental**: Production-cut boundaries and cohort-limited vs production-safe remain clear; pipeline actions (promote_experimental_only, promote_limited_cohort, promote_production_safe) reflect that.

---

## 4. Exact file plan

| Action | Path |
|--------|------|
| Create | `src/workflow_dataset/benchmark_board/models.py` — BenchmarkBoard, BenchmarkSlice, BaselineModel, CandidateModel, Scorecard, ComparisonDimension, DisagreementNote, PromotionRecommendation, RollbackRecommendation. |
| Create | `src/workflow_dataset/benchmark_board/slices.py` — Built-in slices (e.g. ops_reporting, golden_path); map to eval suites / reliability path ids. |
| Create | `src/workflow_dataset/benchmark_board/compare.py` — run_baseline_vs_candidate(baseline_id, candidate_id, slice_ids, repo_root); uses eval compare_runs + optional council-style dimension aggregation. |
| Create | `src/workflow_dataset/benchmark_board/scorecard.py` — build_scorecard(comparison_result, dimensions) → compact promotion-ready scorecard; record disagreements. |
| Create | `src/workflow_dataset/benchmark_board/pipeline.py` — reject_candidate, quarantine_candidate, promote_experimental, promote_limited_cohort, promote_production_safe, rollback_to_prior; each persists decision and optional link to council/runtime. |
| Create | `src/workflow_dataset/benchmark_board/store.py` — data/local/benchmark_board/ scorecards, comparisons, promotion/rollback history. |
| Create | `src/workflow_dataset/benchmark_board/report.py` — next_candidate_awaiting_decision, latest_promoted, quarantined_count, rollback_ready_promoted, next_benchmark_review_action. |
| Create | `src/workflow_dataset/benchmark_board/__init__.py` — Exports. |
| Modify | `src/workflow_dataset/cli.py` — benchmarks list, compare, scorecard; models promote, rollback (or under benchmarks group). |
| Modify | `src/workflow_dataset/mission_control/state.py` — benchmark_board_state block. |
| Modify | `src/workflow_dataset/mission_control/report.py` — [Benchmark board] section. |
| Create | `tests/test_benchmark_board.py` — Models, compare, scorecard, pipeline, report. |
| Create | `docs/samples/M42_benchmark_scorecard_sample.json`, `M42_promotion_decision_sample.json`, `M42_rollback_sample.json`. |
| Create | `docs/M42I_M42L_BENCHMARK_BOARD_DELIVERABLE.md` — Files, CLI, samples, tests, gaps. |

---

## 5. Safety/risk note

- No automatic promotion; every promote/quarantine/rollback is an explicit CLI or API call with persisted decision.
- Benchmark comparisons use existing eval runs and compare_runs; no new execution sandbox. Optional future: run suite with baseline vs candidate model config (harness would need model_config); first-draft uses existing run_id pairs.
- Production-cut and council boundaries are unchanged; pipeline only records decisions and can suggest “run council review” or “update runtime selection” without performing them unattended.
- Disagreement and unstable outcomes are recorded in scorecards and surfaced in reports, not hidden.

---

## 6. Benchmark/promotion principles

- **Local-first**: All data under `data/local/benchmark_board/`; no cloud benchmarks or external APIs for comparison.
- **Explicit decisions**: Reject, quarantine, promote (experimental / limited / production), rollback — each step is a recorded decision with optional rationale.
- **Reversible**: Rollback is a first-class action; rollback history is stored.
- **Dimension-aligned**: Scorecard dimensions align with council perspectives (task success/vertical value, safety/trust, supportability, reliability, latency/runtime burden, operator burden, cohort compatibility) so scorecards can feed council or stand alone.
- **No hidden rollout**: No promotion into production without an explicit promote_production_safe (or equivalent) step.

---

## 7. What this block will NOT do

- Will not replace eval board, council, safe_adaptation, release, or trust/policy.
- Will not add cloud benchmarks or external leaderboards.
- Will not auto-promote candidates to production.
- Will not execute model inference; it compares existing runs or triggers runs via existing harness (with optional model tagging in a later refinement).
- Will not enforce hard rollout gates (e.g. block deploy); it records and reports promotion/rollback state for operator and mission control.
