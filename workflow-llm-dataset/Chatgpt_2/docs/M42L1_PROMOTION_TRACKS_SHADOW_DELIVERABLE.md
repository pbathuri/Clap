# M42L.1 — Promotion Tracks + Shadow-Mode Evaluation: Deliverable

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/benchmark_board/models.py` | Added `PromotionTrack` dataclass (track_id, name, description, order_index, required_previous_track_id, gates_description). |
| `src/workflow_dataset/benchmark_board/store.py` | Added `SHADOW_RUNS_FILE`, `append_shadow_run`, `list_shadow_runs`. |
| `src/workflow_dataset/benchmark_board/report.py` | Added `build_production_vs_candidate_comparison(candidate_id=None, repo_root=None)` — production route vs candidate, scorecard summary, shadow summary, operator_summary_text. |
| `src/workflow_dataset/benchmark_board/__init__.py` | Exported PromotionTrack, get_track, list_track_ids, scope_to_track_id, BUILTIN_PROMOTION_TRACKS, append_shadow_run, list_shadow_runs, build_shadow_report, record_shadow_run, build_production_vs_candidate_comparison. |
| `src/workflow_dataset/cli.py` | Added `benchmarks tracks`, `benchmarks shadow-report --candidate`, `benchmarks production-vs-candidate [--candidate]`. |
| `tests/test_benchmark_board.py` | Added test_promotion_tracks, test_shadow_report_empty, test_shadow_report_with_runs, test_production_vs_candidate_comparison. |

---

## 2. Files created

| File | Purpose |
|------|---------|
| `src/workflow_dataset/benchmark_board/tracks.py` | BUILTIN_PROMOTION_TRACKS (experimental_only, limited_cohort, production_candidate), get_track, list_track_ids, scope_to_track_id. |
| `src/workflow_dataset/benchmark_board/shadow.py` | build_shadow_report(candidate_id, repo_root), record_shadow_run(...); aggregate shadow runs into counts and operator summary. |
| `docs/samples/M42L1_promotion_track_sample.json` | Sample promotion track (limited_cohort). |
| `docs/samples/M42L1_shadow_report_sample.json` | Sample shadow-mode report. |
| `docs/M42L1_PROMOTION_TRACKS_SHADOW_DELIVERABLE.md` | This file. |

---

## 3. Sample promotion track

See `docs/samples/M42L1_promotion_track_sample.json`. Structure: track_id, name, description, order_index, required_previous_track_id, gates_description.

**Built-in tracks:** experimental_only (0), limited_cohort (1, requires experimental_only), production_candidate (2, requires limited_cohort).

CLI: `workflow-dataset benchmarks tracks` or `workflow-dataset benchmarks tracks --json`.

---

## 4. Sample shadow-mode report

See `docs/samples/M42L1_shadow_report_sample.json`. Structure: candidate_id, total_runs, match_count, candidate_better_count, production_better_count, avg_production_score, avg_candidate_score, operator_summary, recent_runs.

CLI: `workflow-dataset benchmarks shadow-report --candidate run_cand_abc` (or `--json`). Record shadow runs via `append_shadow_run` / `record_shadow_run` when running candidate alongside production.

---

## 5. Exact tests run

```bash
cd workflow-llm-dataset && python3 -m pytest tests/test_benchmark_board.py -v
```

**Scope:** 10 tests total; M42L.1 adds: test_promotion_tracks (list_track_ids, get_track, required_previous), test_shadow_report_empty, test_shadow_report_with_runs (append_shadow_run + build_shadow_report), test_production_vs_candidate_comparison.

---

## 6. Next recommended step for the pane

- **Wire shadow recording into compare flow:** When comparing baseline (production) vs candidate, optionally call `record_shadow_run` so that each comparison run is also recorded as a shadow run for the candidate. That way `benchmarks compare --baseline prod --candidate cand` can auto-populate shadow report.
- **Track advancement check:** Add a small helper that, given a candidate’s current scope (e.g. experimental_only), returns the next track and whether gates are satisfied (e.g. shadow report acceptable, scorecard recommend promote/hold); surface in `benchmarks production-vs-candidate` or a new `benchmarks next-track --candidate`.
- **Mission control:** Add a one-line shadow summary to the benchmark_board_state or report (e.g. “candidate X: N shadow runs, candidate_better=M”) so operators see shadow status at a glance.
