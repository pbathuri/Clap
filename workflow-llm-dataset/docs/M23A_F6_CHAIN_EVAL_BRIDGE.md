# M23A-F6 — Chain Hooks into Eval/Benchmark Layer

How chain runs are exposed for the local eval/benchmark harness. Internal and advisory; no change to the eval harness contract.

## Eval-ready chain metadata

Every chain run manifest (`data/local/chain_lab/runs/<run_id>/run_manifest.json`) now includes:

| Field | Description |
|-------|-------------|
| `chain_template_id` | Same as `chain_id`; for eval to reference the template. |
| `variant_id` | Same as `variant_label`; variant used for this run. |
| `final_artifacts` | Flattened list of all step output paths (eval-consumable). |
| `duration_seconds` | Run duration from `started_at` to `ended_at`. |

Existing fields (`run_id`, `chain_id`, `variant_label`, `status`, `step_results`, `started_at`, `ended_at`, `failure_summary`) are unchanged.

## Chain benchmark hooks

The eval layer can reference chain runs or templates without depending on chain_lab internals:

- **`list_chain_runs_for_eval(limit, repo_root)`** — Returns a list of runs in eval shape: `run_id`, `chain_template_id`, `chain_id`, `variant_id`, `variant_label`, `status`, `final_artifacts`, `started_at`, `ended_at`, `duration_seconds`, `run_path`.
- **`get_chain_run_for_eval(run_id, repo_root)`** — Returns one run in the same shape, or `None`. `run_id` may be `"latest"` (resolved to the most recent run).

Use these from the eval harness to enumerate chain runs or load a single run for scoring/comparison.

## Compare benchmark view

For benchmark/review contexts, use a short summary instead of the full diff:

- **CLI:** `workflow-dataset chain compare <id_a> <id_b> --benchmark-view`
- **API:** `compare_chain_runs(run_id_a, run_id_b, ..., benchmark_view=True)` adds a `benchmark_summary` key with:
  - `run_id_a`, `run_id_b`
  - `status_a`, `status_b`
  - `duration_seconds_a`, `duration_seconds_b`
  - `artifact_count_a`, `artifact_count_b`
  - `summary_line` — one-line summary (e.g. `A=success B=success | dur A=10.0s B=20.0s | artifacts A=1 B=2`).

## How chain runs feed into evaluation

1. **Run chains** — `workflow-dataset chain run <chain_id>` (and optional resume/retry) produces runs under `data/local/chain_lab/runs/`.
2. **Manifests are self-contained** — Each run’s `run_manifest.json` has template id, variant, status, final artifacts, and timings so the eval harness can consume it without loading chain definitions.
3. **List or fetch** — Use `list_chain_runs_for_eval()` to discover runs or `get_chain_run_for_eval(run_id)` to load one (e.g. for scoring or comparison with another run).
4. **Compare variants** — Use `chain compare --benchmark-view` to get a concise status/duration/artifact summary for two runs (e.g. baseline vs variant).

The eval harness (e.g. `data/local/eval/`) remains separate; this bridge only exposes chain runs in a stable, eval-friendly shape. No autonomous optimization or end-user agent orchestration.
