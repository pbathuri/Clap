# M23A-F2 — Chain Variants + Failure Recovery + Step Contracts: READ FIRST

## 1. Current chain-lab state

- **Definition** (`definition.py`): Chain JSON has `id`, `description`, `steps` (each: `id`, `type`, `label`, `params`, `workflow_name`), `expected_inputs_per_step`, `expected_outputs_per_step`, `stop_conditions`, `workflow_names`, `variant_label`. The per-step expected inputs/outputs exist at chain level but are not enforced or surfaced per step; no `failure_conditions` or `resumable` on steps.
- **Manifest** (`manifest.py`): Run dir `runs/<run_id>/`, `run_manifest.json` with `run_id`, `chain_id`, `variant_label`, `status`, `step_results[]`, `started_at`, `ended_at`, `failure_summary`. Step result: `step_index`, `step_id`, `label`, `status`, `started_at`, `ended_at`, `output_paths`, `stdout_path`, `stderr_path`, `error`. No `artifacts_produced` or `resumable` in manifest. `list_run_ids(limit)` returns newest first.
- **Runner** (`runner.py`): `run_chain(chain_id, variant_label, stop_on_first_failure, repo_root, run_id)` runs steps via CLI subprocess, persists step dirs with `input_snapshot.json`, stdout/stderr; on failure sets `failure_summary` and stops. No resume/retry; no “run from step N.”
- **Report** (`report.py`): `chain_run_report(run_id)` — markdown with run meta, failure_summary, per-step status/times/error/outputs. `chain_artifact_tree(run_id)` — dict with run_dir, steps and output_paths. No “failure report” section (failing step, artifacts already produced, resume possible).
- **Compare** (`compare.py`): `compare_chain_runs(run_id_a, run_id_b)` — status_diff, step_count_diff, step_status_diff, failure_diff. No output-inventory or artifact-diff; no `--run A --run B` style.
- **CLI**: `chain list`, `chain define`, `chain run`, `chain report <run_id>`, `chain compare <run_id_a> <run_id_b>`, `chain list-runs`, `chain artifact-tree <run_id>`. No `--run latest`, no `resume`, no `retry-step`, no `compare --run A --run B`.

## 2. Exact reuse map

| Existing piece | F2 use |
|----------------|--------|
| `load_chain`, `load_run_manifest`, `save_run_manifest`, `run_dir_for`, `step_result_dir` | Resume/retry load same chain and manifest; append or overwrite step results; reuse step dir for retry. |
| `run_chain` | Extend with `from_step_index` and optional `run_id` (existing run) for resume; add `retry_step_index` path. |
| `_run_cli_step` | Called for each step in run_chain; also from retry_step and resume_from_step. |
| `chain_run_report` | Extend with failure section: failing step, artifacts produced, resume possible; support `run_id="latest"` via `list_run_ids(limit=1)[0]`. |
| `compare_chain_runs` | Keep; add CLI `--run A --run B`; extend return with `output_inventory_a/b`, `artifact_diff` (optional, from artifact tree). |
| `list_run_ids` | Used for `--run latest` and for listing runs in compare. |
| Definition `expected_inputs_per_step`, `expected_outputs_per_step` | Formalize in step schema; add `failure_conditions` (list of strings), `resumable` (bool) per step; validate in definition. |

## 3. Exact gap

1. **Step contracts** — Per-step `expected_inputs`, `expected_outputs`, `failure_conditions`, `resumable` not in step schema; not validated; not shown in report.
2. **Failure reports** — Report does not highlight failing step, “artifacts already produced” list, or “resume possible” (based on step resumable + next step index).
3. **Resume/retry** — No “resume from step N” (re-run steps N..end for existing run_id), no “retry failed step” (re-run one step, update manifest), no “rerun from scratch” (existing: new run_id).
4. **Variant comparison** — No `compare --run A --run B`; no output inventory or artifact diff in compare output.
5. **Report/CLI** — No `chain report --run latest`; no `chain resume --run latest`; no `chain retry-step --run latest --step <step_id>`.

## 4. File plan

| File | Changes |
|------|--------|
| `chain_lab/definition.py` | Add step fields: `expected_inputs`, `expected_outputs`, `failure_conditions`, `resumable` in `_step_sanitize` and schema; optional validation that step_ids in expected_inputs_per_step/expected_outputs_per_step exist. |
| `chain_lab/manifest.py` | Add `get_latest_run_id(repo_root, limit=1)` returning first of `list_run_ids(limit=1)` or None. Optionally add `artifacts_produced` per step in step_results when we persist (runner can append paths). |
| `chain_lab/runner.py` | Add `resume_chain(run_id, from_step_index, repo_root)` (load manifest + chain, run steps from index, merge step_results, save manifest). Add `retry_step(run_id, step_index_or_id, repo_root)` (load manifest + chain, re-run one step, update that step in step_results, set status to success/failed, save). Keep `run_chain` for “from scratch.” |
| `chain_lab/report.py` | Add `failure_report_section(manifest, chain_definition)` → lines for failing step, artifacts produced, resume possible. Add `run_id_or_latest(run_id, repo_root)` using `get_latest_run_id` when run_id == "latest". Use in `chain_run_report`. Include step contract (expected inputs/outputs, resumable) in per-step block when definition available. |
| `chain_lab/compare.py` | Add optional `output_inventory` for each run (list of step_id + output_paths from manifest); add `compare_chain_runs(..., include_artifact_diff=False)` to optionally add artifact tree diff. Support same interface. |
| `cli.py` | Add `chain report --run <run_id\|latest>` (positional or --run), `chain resume --run <run_id\|latest> [--from-step N]`, `chain retry-step --run <run_id\|latest> --step <step_id_or_index>`, `chain compare --run A --run B` (two optional --run args; fallback to two positionals). |
| `tests/test_chain_lab.py` | Tests for: step contract (resumable, expected_inputs); failure report section; get_latest_run_id; resume_chain (partial); retry_step; compare with --run A --run B style; report --run latest. |
| `docs/M23A_F2_*.md` | Sample failed-chain report, resumed-chain report, variant compare output; CLI usage. |

No new top-level modules; keep all in existing chain_lab and CLI block.
