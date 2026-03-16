# M23A-F6 — Chain Hooks into Eval/Benchmark: Delivery

## 1. Files modified

- `src/workflow_dataset/chain_lab/compare.py` — Added `benchmark_summary_text(diff)` for a short, benchmark/review-friendly text summary.
- `src/workflow_dataset/cli.py` — When `chain compare --benchmark-view` is used, the benchmark block now uses `benchmark_summary_text(diff)` for consistent multi-line output.
- `docs/M23A_CHAIN_OPERATOR_GUIDE.md` — Added section **7. Chain runs and evaluation** (eval-ready metadata, eval API, compare for benchmark, link to M23A_F6_CHAIN_EVAL_BRIDGE.md); renumbered Quick reference to **8**; added table row for `chain compare --benchmark-view`.

## 2. Files created

- `docs/M23A_F6_EVAL_READ_FIRST.md` — State check and file plan for this pass.
- `docs/M23A_F6_DELIVERY.md` — This file.

**Unchanged (already F6-ready):** `chain_lab/manifest.py` (eval fields in payload), `chain_lab/eval_bridge.py`, `chain_lab/__init__.py` (exports), `docs/M23A_F6_CHAIN_EVAL_BRIDGE.md`.

## 3. Interface changes

| Where | Change |
|-------|--------|
| `chain_lab.compare` | New: `benchmark_summary_text(diff: dict) -> str`. Returns 3-line summary when `diff` contains `benchmark_summary`; otherwise `""`. |
| CLI `chain compare` | When `--benchmark-view` is set, prints the result of `benchmark_summary_text(diff)` (fallback to previous 2-line print if empty). |
| Operator guide | New section 7 and quick-reference row for benchmark compare. |

No changes to manifest schema, `save_run_manifest`, `list_chain_runs_for_eval`, or `get_chain_run_for_eval`.

## 4. Sample eval-ready chain manifest excerpt

```json
{
  "run_id": "a1b2c3d4e5f6",
  "chain_id": "ops_reporting_short",
  "variant_label": "default",
  "status": "success",
  "started_at": "2025-03-16T14:00:00Z",
  "ended_at": "2025-03-16T14:02:30Z",
  "chain_template_id": "ops_reporting_short",
  "variant_id": "default",
  "final_artifacts": [
    "/path/to/runs/a1b2c3d4e5f6/steps/0/stdout.txt",
    "/path/to/runs/a1b2c3d4e5f6/steps/0/stderr.txt",
    "/path/to/runs/a1b2c3d4e5f6/steps/1/stdout.txt",
    "/path/to/runs/a1b2c3d4e5f6/steps/1/stderr.txt"
  ],
  "duration_seconds": 150.0,
  "step_results": [...]
}
```

## 5. Sample compare output (benchmark view)

**CLI:** `workflow-dataset chain compare run_a run_b --benchmark-view`

```
Benchmark summary
  Run A: run_a  status=success  duration=10.0s  artifacts=2
  Run B: run_b  status=success  duration=20.0s  artifacts=3
  A=success B=success | dur A=10.0s B=20.0s | artifacts A=2 B=3

Run A: run_a  {'chain_id': 'demo_verify', 'variant': 'default', 'status': 'success', ...}
Run B: run_b  {'chain_id': 'demo_verify', 'variant': 'v2', 'status': 'success', ...}
  ...
```

**API:** `compare_chain_runs("run_a", "run_b", benchmark_view=True)["benchmark_summary"]`:

```python
{
  "run_id_a": "run_a", "run_id_b": "run_b",
  "status_a": "success", "status_b": "success",
  "duration_seconds_a": 10.0, "duration_seconds_b": 20.0,
  "artifact_count_a": 2, "artifact_count_b": 3,
  "summary_line": "A=success B=success | dur A=10.0s B=20.0s | artifacts A=2 B=3"
}
```

## 6. Tests run

```bash
cd workflow-llm-dataset && python3 -m pytest tests/test_chain_lab.py::test_benchmark_summary_text tests/test_chain_lab.py::test_manifest_has_eval_ready_fields tests/test_chain_lab.py::test_list_chain_runs_for_eval tests/test_chain_lab.py::test_get_chain_run_for_eval tests/test_chain_lab.py::test_compare_benchmark_view -v
```

Result: **5 passed.** Covers eval-ready manifest fields, `list_chain_runs_for_eval`, `get_chain_run_for_eval`, compare benchmark view, and `benchmark_summary_text`.

## 7. Remaining weaknesses (this pane only)

- **Eval harness integration** — The eval layer (`eval/`) does not yet call `list_chain_runs_for_eval` or `get_chain_run_for_eval`; the bridge is in place for when that integration is added.
- **Scoring** — No chain-specific scoring logic in this repo; comparison is status/duration/artifact counts only. Actual scoring remains in the eval harness.
- **benchmark_summary_text** — Only used when `benchmark_summary` is present; not exported from `chain_lab/__init__.py` (optional for external use).
