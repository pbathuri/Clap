# M23A-F2 — Validation and Gap Fill

## 1. What already exists (from previous step)

- **Step contracts** — `chain_lab/definition.py`: per-step `expected_inputs`, `expected_outputs`, `failure_conditions`, `resumable`; `get_step_by_id_or_index`. Load/save normalize these.
- **Failure reporting** — `chain_lab/report.py`: `failure_report_section(manifest, chain_definition)` with failing step, why, artifacts already produced, resume possible. Wired into `chain_run_report`. Missing: **recommended next operator command(s)**.
- **Resume / retry** — `chain_lab/runner.py`: `resume_chain(run_id, from_step_index)`, `retry_step(run_id, step_index_or_id)`. CLI: `chain resume --run <id|latest> [--from-step N]`, `chain retry-step --run <id|latest> --step <id|index>`.
- **Variant/run comparison** — `chain_lab/compare.py`: `compare_chain_runs` with `output_inventory_a/b`, `artifact_diff` (only_in_a, only_in_b, common_count), status/step/failure diffs. Missing: **timing differences** (run-level or step-level) in compare output.
- **Report / latest** — `resolve_run_id("latest")`, `get_latest_run_id()`; `chain report` default "latest", `chain report --run latest`.
- **CLI** — `chain report`, `chain resume`, `chain retry-step`, `chain compare` (positional or `--run-a` / `--run-b`), `--artifact-diff`, `chain list-runs`, `chain artifact-tree`.
- **Tests** — `tests/test_chain_lab.py`: F2 tests for contracts, resolve_run_id, failure section, resume, retry, compare with inventory/artifact_diff, report with latest.
- **Docs** — `M23A_F2_READ_FIRST.md`, `M23A_F2_SAMPLES.md`, `M23A_F2_DELIVERY.md`.

## 2. What is reusable

- All of `chain_lab/*` and existing CLI commands — reuse as-is.
- `failure_report_section` — extend by appending recommended next command(s) (retry-step, resume) using run_id and failing step index/id.
- `compare_chain_runs` — extend run_a/run_b dict with `started_at`, `ended_at` from manifest so timing is visible in JSON and can be shown in CLI.

## 3. What this prompt should add

1. **Recommended next operator command(s)** in the failure report: e.g.  
   `workflow-dataset chain retry-step --run <run_id> --step <step_id>`  
   and  
   `workflow-dataset chain resume --run <run_id> --from-step <N>`  
   so the report is actionable.
2. **Timing in compare** — Include run-level `started_at` / `ended_at` in `run_a` and `run_b` in compare output; optionally print timing in CLI when not --json.

## 4. What it must not change

- Step contract schema or validation.
- Resume/retry behavior or CLI signatures.
- Compare API signature or existing keys (only add keys).
- Any non–chain-lab CLI commands or modules.
- Sandbox paths or apply boundaries.

## 5. File plan

| File | Change |
|------|--------|
| `chain_lab/report.py` | In `failure_report_section`, accept optional `run_id: str \| None`; append "Recommended next command(s):" with retry-step and resume commands. Caller must pass run_id when generating the report (we have resolved run_id in `chain_run_report`). |
| `chain_lab/compare.py` | When setting `out["run_a"]` and `out["run_b"]`, add `started_at`, `ended_at` from manifest. |
| `cli.py` | In `chain compare` text output, print run_a/run_b timing when present (e.g. "Run A: ... started ... ended ..."). |
| `tests/test_chain_lab.py` | Assert failure report contains "Recommended" or "retry-step"; assert compare run_a/run_b include started_at/ended_at when manifests have them. |
| `docs/M23A_F2_SAMPLES.md` | Add recommended next command(s) to sample failed-chain report. |

## 6. Risk note

- **report.py**: `failure_report_section` currently does not take run_id; we need run_id to print concrete commands. So add optional parameter `run_id: str | None = None`; when present, append recommended commands. In `chain_run_report` we have `resolved` (the run_id), so pass `resolved` into `failure_report_section(manifest, chain_definition, run_id=resolved)`.
- **compare.py**: Only adding keys to existing dicts; no breaking change.
- **cli.py**: Only adding lines to existing compare output; no rename or removal of commands.
