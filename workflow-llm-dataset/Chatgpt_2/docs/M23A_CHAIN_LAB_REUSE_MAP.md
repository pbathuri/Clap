# M23A Chain Lab — Reuse Map

Internal chain lab reuses existing workflow entrypoints; it does not reimplement them.

## Reused entrypoints

| Capability | Source | How chain lab uses it |
|------------|--------|------------------------|
| Run ops reporting demo | CLI `workflow-dataset release demo` | Step type `cli` runs subprocess: `python -m workflow_dataset.cli` + step params `args` (e.g. `["release", "demo", "--workflow", "weekly_status", "--save-artifact"]`). |
| Workspace discovery | `release.reporting_workspaces.get_workspace_inventory`, `list_reporting_workspaces` | Not invoked by chain runner directly; operator can inspect workspaces produced by a step via report output paths. |
| Workspace diff | `release.workspace_rerun_diff.diff_workspaces` | Can be used by operator to compare workspace outputs from two chain runs if steps write to workspaces. |
| Review/package | CLI `review approve-artifact`, `review build-package` | Chain steps can invoke these via `params.args` in a step. |
| Run manifest / state | Pattern from `devlab.experiments` (load/save queue, run dirs) | Same pattern: sandbox root, runs subdir, manifest JSON per run. |
| Comparison | Pattern from `eval.board.compare_runs` | compare_chain_runs provides status/step-wise diff between two runs. |
| Dates / hashes | `utils.dates.utc_now_iso`, `utils.hashes.stable_id` | Run timestamps and run_id generation. |

## Not reused (out of scope)

- Pilot session/feedback: chain lab does not start pilot sessions or capture feedback.
- Mission control: chain lab does not aggregate product/eval state.
- Incubator/planner: not used by chain lab.

## Sandbox

- All chain data under `data/local/chain_lab/`.
- Chains: `data/local/chain_lab/chains/<chain_id>.json`.
- Runs: `data/local/chain_lab/runs/<run_id>/run_manifest.json` and `runs/<run_id>/steps/<index>/`.
