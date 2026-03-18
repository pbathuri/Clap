# M42I–M42L — Benchmark Board + Promotion/Rollback Pipeline: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/cli.py` | Added `benchmarks` group: `list`, `compare --baseline --candidate`, `scorecard --id`. Added `models` group: `promote --id --scope`, `rollback --id --prior`, `quarantine --id`, `reject --id`. |
| `src/workflow_dataset/mission_control/state.py` | Added `benchmark_board_state`: top_candidate_awaiting_decision, latest_promoted_id, latest_promoted_scope, quarantined_count, rollback_ready_promoted_id, next_benchmark_review_action; local_sources["benchmark_board"]. |
| `src/workflow_dataset/mission_control/report.py` | Added **[Benchmark board]** section: awaiting, promoted, scope, quarantined, rollback_ready, next action. |

---

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/benchmark_board/models.py` | BenchmarkSlice, BaselineModel, CandidateModel, Scorecard, ComparisonDimension, BenchmarkDisagreementNote, PromotionRecommendation, RollbackRecommendation, BenchmarkBoard; DEFAULT_COMPARISON_DIMENSIONS. |
| `src/workflow_dataset/benchmark_board/slices.py` | BUILTIN_SLICES (ops_reporting, golden_path, single), get_slice, list_slice_ids. |
| `src/workflow_dataset/benchmark_board/store.py` | data/local/benchmark_board/ scorecards, promotion_history, rollback_history, quarantined.json, promoted.json; save/load_scorecard, list_scorecards, get_quarantined, get_latest_promoted, list_promotion_history, list_rollback_history, add/remove_quarantined, set_promoted. |
| `src/workflow_dataset/benchmark_board/compare.py` | run_baseline_vs_candidate(baseline_id, candidate_id, slice_ids, repo_root); uses eval compare_runs, adds run_a_score/run_b_score. |
| `src/workflow_dataset/benchmark_board/scorecard.py` | build_scorecard(comparison_result, …) → Scorecard; dimensions, disagreement_notes, promotion/rollback recommendations. |
| `src/workflow_dataset/benchmark_board/pipeline.py` | reject_candidate, quarantine_candidate, promote_experimental, promote_limited_cohort, promote_production_safe, rollback_to_prior; each persists decision. |
| `src/workflow_dataset/benchmark_board/report.py` | build_benchmark_board_report(repo_root) → top_candidate_awaiting_decision, latest_promoted, quarantined_count, rollback_ready, next_benchmark_review_action. |
| `src/workflow_dataset/benchmark_board/__init__.py` | Package exports. |
| `tests/test_benchmark_board.py` | test_benchmark_slices, test_build_scorecard_from_comparison, test_scorecard_revert_has_rollback_recommendation, test_store_scorecard_and_list, test_pipeline_*, test_report_no_data. |
| `docs/samples/M42_benchmark_scorecard_sample.json` | Sample scorecard. |
| `docs/samples/M42_promotion_decision_sample.json` | Sample promotion decision. |
| `docs/samples/M42_rollback_sample.json` | Sample rollback output. |
| `docs/M42I_M42L_BENCHMARK_BOARD_BEFORE_CODING.md` | Before-coding analysis. |
| `docs/M42I_M42L_BENCHMARK_BOARD_DELIVERABLE.md` | This file. |

---

## 3. Exact CLI usage

```bash
# List slices and recent scorecards
workflow-dataset benchmarks list
workflow-dataset benchmarks list --json

# Compare baseline vs candidate (run ids or aliases: latest, previous)
workflow-dataset benchmarks compare --baseline previous --candidate latest
workflow-dataset benchmarks compare --baseline prod_current --candidate cand_123 --slices ops_reporting
workflow-dataset benchmarks compare -b previous -c latest --repo /path/to/repo --json --no-save

# Show a saved scorecard
workflow-dataset benchmarks scorecard --id sc_xxxx
workflow-dataset benchmarks scorecard -i sc_xxxx --json

# Promotion pipeline (explicit decisions)
workflow-dataset models promote --id cand_123 --scope experimental
workflow-dataset models promote --id cand_123 --scope limited_cohort --reason "Cohort trial passed"
workflow-dataset models promote --id cand_123 --scope production_safe

workflow-dataset models rollback --id cand_123 --prior prod_previous
workflow-dataset models quarantine --id cand_123 --reason "Needs review"
workflow-dataset models reject --id cand_123 --reason "Regressions"
```

---

## 4. Sample benchmark scorecard

See `docs/samples/M42_benchmark_scorecard_sample.json`. Structure: scorecard_id, baseline_id, candidate_id, slice_ids, dimensions (task_success, safety_trust, …), disagreement_notes, promotion_recommendation, rollback_recommendation, recommendation, thresholds_passed, regressions, improvements, at_iso.

---

## 5. Sample promotion decision output

See `docs/samples/M42_promotion_decision_sample.json`. Example: `{"candidate_id": "run_abc123", "decision": "promote_production_safe", "scope": "production_safe", "reason": "Promoted to production-safe"}`.

CLI: `workflow-dataset models promote --id run_abc123 --scope production_safe` prints `Promoted run_abc123  scope=production_safe`.

---

## 6. Sample rollback output

See `docs/samples/M42_rollback_sample.json`. Example: `{"candidate_id": "run_xyz789", "prior_id": "run_prev_stable", "reason": "Rollback by operator"}`.

CLI: `workflow-dataset models rollback --id run_xyz789 --prior run_prev_stable` prints `Rollback run_xyz789 -> run_prev_stable`.

---

## 7. Exact tests run

```bash
cd workflow-llm-dataset && python3 -m pytest tests/test_benchmark_board.py -v
```

**Scope:** 6 tests — benchmark slices (list_slice_ids, get_slice), build_scorecard from comparison (promote case), scorecard revert has rollback_recommendation, store save/load/list scorecard, pipeline (reject, quarantine, promote_experimental, rollback_to_prior), report with no data.

---

## 8. Exact remaining gaps for later refinement

- **Eval run tagging**: Comparison uses existing eval runs; baseline/candidate are run_id or alias. No model_id in run manifest yet; optional future: tag runs with model_id when running suite so scorecards can say “model A vs model B”.
- **Slices driving runs**: compare does not yet run eval suite per slice; it compares two run_ids. Future: run_baseline_vs_candidate could run suite with baseline config then candidate config and compare (requires harness accepting model/runtime config).
- **Council integration**: Scorecard can be passed as subject evidence to council (e.g. subject_type=benchmark_run, ref=scorecard_id); not wired in this block.
- **Runtime mesh**: Promote to “production-safe” does not yet update runtime_mesh model selection; pipeline only records decision; optional later: write promoted candidate to data/local/runtime/current_production_model.json or similar.
- **Unstable/contradictory behavior**: Disagreement notes are recorded in scorecard; no dedicated “unstable outcome” flag or retry logic.
- **No-benchmark / weak-benchmark**: Report next action suggests “run compare” or “run eval run-suite”; no explicit “insufficient data” gate for promote.
