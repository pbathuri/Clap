# M23A-F6 — Chain Hooks into Eval/Benchmark: READ FIRST (state check)

## 1. Current state

- **Manifest** (`chain_lab/manifest.py`): `save_run_manifest` already writes eval-ready fields: `chain_template_id`, `variant_id`, `final_artifacts`, `duration_seconds`. No change needed.
- **Eval bridge** (`chain_lab/eval_bridge.py`): `list_chain_runs_for_eval(limit, repo_root)` and `get_chain_run_for_eval(run_id, repo_root)` exist and return eval-consumable shape. Exported from `chain_lab/__init__.py`.
- **Compare** (`chain_lab/compare.py`): `compare_chain_runs(..., benchmark_view=True)` adds `benchmark_summary` with run_id_a/b, status_a/b, duration_seconds_a/b, artifact_count_a/b, summary_line.
- **CLI**: `workflow-dataset chain compare <a> <b> --benchmark-view` prints benchmark summary. Implemented.
- **Docs**: `docs/M23A_F6_CHAIN_EVAL_BRIDGE.md` documents the bridge, manifest fields, and how chain runs feed into evaluation.

## 2. Reuse

- Manifest payload, eval_bridge API, compare benchmark_summary, existing tests (test_manifest_has_eval_ready_fields, test_list_chain_runs_for_eval, test_get_chain_run_for_eval, test_compare_benchmark_view).

## 3. What this pass adds (minimal)

1. **Operator guide** — Add a short "Chain runs and evaluation" section in `M23A_CHAIN_OPERATOR_GUIDE.md` that points to the eval bridge doc and the API/CLI surface.
2. **Compare summary text** — Optional helper `benchmark_summary_text(diff)` in compare.py for a single string suitable for logs/reports; CLI can use it for a cleaner benchmark block when `--benchmark-view` is set.
3. **Delivery doc** — `M23A_F6_DELIVERY.md` with files modified/created, interface summary, sample manifest excerpt, sample compare output, tests run, weaknesses.

## 4. What not to change

- Manifest schema or save_run_manifest contract. Eval harness internals. Runner or definition behavior.

## 5. File plan

| Item | File | Action |
|------|------|--------|
| A | docs/M23A_F6_EVAL_READ_FIRST.md | This state check. |
| B | docs/M23A_CHAIN_OPERATOR_GUIDE.md | Add "Chain runs and evaluation" section. |
| C | chain_lab/compare.py | Add `benchmark_summary_text(diff)`; keep existing benchmark_summary dict. |
| D | cli.py | When benchmark_view: use benchmark_summary_text for the summary block if present. |
| E | docs/M23A_F6_DELIVERY.md | Delivery summary, samples, tests, weaknesses. |

## 6. Risk note

- Additive only. No change to eval harness or chain run format. Existing F6 tests remain the acceptance proof.
