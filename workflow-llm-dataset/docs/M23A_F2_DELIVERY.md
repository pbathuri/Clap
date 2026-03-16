# M23A-F2 — Chain Variants + Failure Recovery + Step Contracts

Delivery summary for the F2 layer: step contracts, failure reports, resume/retry, variant comparison.

## Delivered

1. **Step contracts** — Per-step fields in definition: `expected_inputs`, `expected_outputs`, `failure_conditions`, `resumable`. Normalized in `_step_sanitize`; optional display in report. `get_step_by_id_or_index(definition, step_id_or_index)` for lookup.
2. **Failure reports** — `failure_report_section(manifest, chain_definition)` and in `chain_run_report`: failing step, why it failed, artifacts already produced, resume possible (from step’s `resumable`).
3. **Resume / retry** — `resume_chain(run_id, from_step_index, repo_root)` (re-runs from step to end, keeps prior results); `retry_step(run_id, step_index_or_id, repo_root)` (re-runs one step, updates manifest). Rerun from scratch = existing `run_chain` (new run_id).
4. **Variant comparison** — `compare_chain_runs(..., include_output_inventory=True, include_artifact_diff=False)`: `output_inventory_a/b` (step_id + output_paths per step), optional `artifact_diff` (only_in_a, only_in_b, common_count). **Timing:** `run_a` and `run_b` include `started_at`, `ended_at` from manifests; CLI prints them when not `--json`. CLI: `compare <a> <b>` or `--run-a A --run-b B`, plus `--artifact-diff`.
5. **Report / latest** — `resolve_run_id(run_id, repo_root)` so `run_id="latest"` resolves to `get_latest_run_id()`. Report and artifact-tree accept `latest`. CLI: `chain report` (default latest), `chain report --run latest`, `chain resume --run latest`, `chain retry-step --run latest --step <id>`.

## Files modified

- `chain_lab/definition.py` — Step contract fields; `get_step_by_id_or_index`.
- `chain_lab/manifest.py` — `get_latest_run_id`.
- `chain_lab/runner.py` — `resume_chain`, `retry_step`.
- `chain_lab/report.py` — `resolve_run_id`, `failure_report_section`, report takes `latest` and includes failure section and step contract.
- `chain_lab/compare.py` — `resolve_run_id` for `latest`; `output_inventory_a/b`; `include_artifact_diff` → `artifact_diff`.
- `chain_lab/__init__.py` — Exports for F2.
- `cli.py` — `chain report` (default/--run latest), `chain resume`, `chain retry-step`, `chain compare` (--run-a, --run-b, --artifact-diff).
- `tests/test_chain_lab.py` — F2 tests.

## Files created

- `docs/M23A_F2_READ_FIRST.md` — Current state, reuse map, gap, file plan.
- `docs/M23A_F2_SAMPLES.md` — CLI usage, sample failed report, resumed report, variant compare.
- `docs/M23A_F2_DELIVERY.md` — This file.

## Tests run

```bash
cd workflow-llm-dataset
python3 -m pytest tests/test_chain_lab.py -v --tb=short
```

Expected: 20 passed, 2 skipped (CLI tests when yaml missing).

## Remaining weaknesses (F2 pane only)

1. **Resume does not re-use prior step outputs** — Steps after `from_step_index` are re-executed; we do not pass prior step output paths as “inputs” to the next step (no automatic wiring).
2. **Retry step runs real CLI** — `retry_step` invokes the same subprocess again; no “dry run” or “replay from saved stdout” for comparison.
3. **Artifact diff is path-only** — `artifact_diff` compares path sets; no content diff (e.g. workspace artifact .md files) or checksum.
4. **Resumable is advisory** — Report shows “Resume possible: Yes/No” from step contract but CLI does not block `resume` when the failing step has `resumable: false`.
5. **Compare --run-a/--run-b** — Two separate options; task asked for `--run A --run B` (single option used twice); Typer does not support multiple values for one option, so we use `--run-a` and `--run-b`.
