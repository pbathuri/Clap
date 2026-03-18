# M23A — Internal Agent Chain Lab (Operator-Controlled)

Local operator-controlled chain runner for internal workflow chaining. Not a user-facing multi-agent platform; no uncontrolled autonomy, no hidden cloud, no auto-apply.

## Delivered

1. **Chain definition** — Local JSON under `data/local/chain_lab/chains/`. Fields: id, description, ordered steps, expected_inputs_per_step, expected_outputs_per_step, stop_conditions, workflow_names, variant_label.
2. **Chain runner** — Run one chain, persist step outputs, stop on first failure (configurable). Steps run via CLI subprocess (`release demo`, `release verify`, etc.).
3. **Step output persistence** — Per-step: input_snapshot.json, stdout.txt, stderr.txt; run_manifest.json with status, timing, failure_summary.
4. **Chain reports** — Per-step report, final summary, artifact tree; `chain report`, `chain artifact-tree`.
5. **Compare** — Compare two chain runs (status, step count, step-wise status, failure summary); `chain compare run_a run_b`.
6. **CLI** — `chain list`, `chain define --id <id> --file <path>`, `chain run <chain_id>`, `chain report <run_id>`, `chain artifact-tree <run_id>`, `chain compare <a> <b>`, `chain list-runs`.

## Files

- **Created:** `src/workflow_dataset/chain_lab/` — config.py, definition.py, manifest.py, runner.py, report.py, compare.py, __init__.py.
- **Modified:** `src/workflow_dataset/cli.py` — added chain_group and commands (one block).
- **Created:** `tests/test_chain_lab.py`, `docs/M23A_CHAIN_LAB_READ_FIRST.md`, `docs/M23A_CHAIN_LAB_REUSE_MAP.md`, `docs/M23A_CHAIN_LAB_SAMPLES.md`.

## Tests

```bash
cd workflow-llm-dataset
python -m pytest tests/test_chain_lab.py -v --tb=short
```

## Remaining weaknesses (this track only)

1. **No programmatic step API** — Steps are executed only via CLI subprocess. Reusing a direct Python API for `release demo` (if one existed) would avoid subprocess and improve capture of output paths.
2. **Output path capture** — Step outputs are stdout/stderr and files written under the step dir; workspace paths (e.g. `data/local/workspaces/weekly_status/<run_id>`) are not automatically linked from the run manifest. Operator can infer from step type and CLI args.
3. **Stop/cancel** — Stop on first failure is supported; interactive cancel (e.g. SIGINT) is not implemented (subprocess runs to completion or timeout).
4. **Rerun** — Rerun is “run the same chain again” (new run_id); no “resume from step N” or “re-run only step N.”
5. **Variant comparison** — Compare is run-to-run; there is no dedicated “run variant A vs variant B” shortcut (operator runs two chains with different variant_label and then compares the two run_ids).
