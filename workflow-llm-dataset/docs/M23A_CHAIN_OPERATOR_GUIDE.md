# M23A Chain Lab — Operator Guide

How to define, run, inspect, and maintain chain runs locally. All under `data/local/chain_lab/`; no cloud, no auto-apply.

---

## 1. Defining a chain

A chain is a JSON file with:

- **id** — unique identifier
- **description** — short summary (optional)
- **steps** — list of step objects. Each step has:
  - **id** — step id (e.g. `verify`, `demo_weekly`)
  - **type** — `cli` (run workflow-dataset CLI subprocess)
  - **label** — display label (optional)
  - **params** — for `cli`: `args` (list of CLI args), optional `timeout` (seconds)
  - **expected_inputs** / **expected_outputs** — optional contract
  - **resumable** — optional, default true
- **variant_label** — optional variant name
- **stop_conditions** / **workflow_names** — optional metadata

**Ways to get a chain:**

1. **Install an example**  
   `workflow-dataset chain examples list`  
   `workflow-dataset chain examples install demo_verify`

2. **Define from file**  
   `workflow-dataset chain define --id my_chain --file /path/to/chain.json`

Chains are stored under `data/local/chain_lab/chains/<id>.json`.

---

## 2. Running a chain

- **Run once**  
  `workflow-dataset chain run <chain_id>`  
  Optional: `--variant <label>`, `--no-stop-on-failure`.

- **Where output goes**  
  Each run gets a directory: `data/local/chain_lab/runs/<run_id>/`.  
  - `run_manifest.json` — run metadata, status, step results.  
  - `steps/0/`, `steps/1/`, … — per-step dirs with `stdout.txt`, `stderr.txt`, `input_snapshot.json`, and any step-produced outputs.

- **Run id**  
  Printed when the run finishes. Use it for report, resume, retry, compare, archive.

---

## 3. Resume and retry

- **Resume from a step**  
  Keeps results for earlier steps, re-runs from the given step to the end.  
  `workflow-dataset chain resume --run <run_id> --from-step <index>`

- **Retry one step**  
  Re-runs a single step and updates the run manifest.  
  `workflow-dataset chain retry-step --run <run_id> --step <step_id_or_index>`

- **Resolve “latest”**  
  Use `latest` where a run id is expected (e.g. `chain report latest`, `chain resume --run latest`).

---

## 4. Inspecting run history

- **List runs**  
  `workflow-dataset chain list-runs [--limit N]`  
  Shows run_id, chain_id, status, started_at (newest first).

- **Per-run report**  
  `workflow-dataset chain report <run_id>` or `chain report latest`  
  Markdown report: run id, chain, status, timestamps, failure summary (if failed), per-step status and outputs. On failure, includes recommended retry/resume commands.

- **Artifact tree**  
  `workflow-dataset chain artifact-tree <run_id> [--json]`  
  Run dir, steps, and output paths.

- **Compare two runs**  
  `workflow-dataset chain compare <id_a> <id_b>`  
  Optional: `--artifact-diff`, `--benchmark-view`, `--json`.

---

## 5. Manifests and step outputs

- **run_manifest.json** (per run)  
  - `run_id`, `chain_id`, `variant_label`  
  - `status`: `success`, `failed`, `running`  
  - `started_at`, `ended_at`, `failure_summary`  
  - `step_results`: list of `{ step_index, step_id, status, started_at, ended_at, output_paths, error }`  
  - Eval-oriented: `chain_template_id`, `variant_id`, `final_artifacts`, `duration_seconds`

- **Per-step directory**  
  - `input_snapshot.json` — step definition and params at run time.  
  - `stdout.txt`, `stderr.txt` — CLI stdout/stderr.  
  - Other files produced by the step (if any).

---

## 6. Cleanup and archive

- **List old runs**  
  `workflow-dataset chain cleanup --older-than 30d`  
  Default is dry-run: only lists runs older than the threshold.

- **Archive specific run**  
  `workflow-dataset chain runs archive --run <run_id>`  
  Moves the run directory to `data/local/chain_lab/runs/archive/<run_id>/`.

- **Archive all runs older than N days**  
  `workflow-dataset chain cleanup --older-than 30d --no-dry-run --archive`  
  Archives (moves) those runs into `runs/archive/`. Chain definitions are never deleted.

---

## 7. Chain runs and evaluation

Chain runs are **eval-ready**: each run’s manifest includes `chain_template_id`, `variant_id`, `final_artifacts`, and `duration_seconds` so the local eval/benchmark layer can consume them without loading chain definitions.

- **Eval API** — Use `list_chain_runs_for_eval(limit, repo_root)` to list runs in eval shape, or `get_chain_run_for_eval(run_id, repo_root)` to load one (e.g. for scoring). Both are in `workflow_dataset.chain_lab.eval_bridge` (and exported from `chain_lab`).
- **Compare for benchmark** — Use `workflow-dataset chain compare <id_a> <id_b> --benchmark-view` for a concise status/duration/artifact summary suitable for benchmark or review.
- **Full bridge doc** — See `docs/M23A_F6_CHAIN_EVAL_BRIDGE.md` for manifest fields, API details, and how chain runs feed into evaluation. The chain lab remains internal and advisory; the eval harness stays separate.

---

## 8. Quick reference

| Task              | Command |
|-------------------|--------|
| List examples     | `chain examples list` |
| Install example   | `chain examples install <id>` |
| List definitions  | `chain list` |
| Define from file  | `chain define --id <id> --file <path>` |
| Run chain         | `chain run <chain_id>` |
| List runs         | `chain list-runs` |
| Report            | `chain report <run_id \| latest>` |
| Resume            | `chain resume --run <id> --from-step N` |
| Retry step        | `chain retry-step --run <id> --step <id \| index>` |
| Artifact tree     | `chain artifact-tree <run_id>` |
| Compare runs      | `chain compare <id_a> <id_b>` |
| Compare (benchmark)| `chain compare <id_a> <id_b> --benchmark-view` |
| Archive run       | `chain runs archive --run <id>` |
| Cleanup (dry-run) | `chain cleanup --older-than 30d` |
| Cleanup (archive) | `chain cleanup --older-than 30d --no-dry-run --archive` |
