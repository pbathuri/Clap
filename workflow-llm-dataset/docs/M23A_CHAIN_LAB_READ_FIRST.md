# M23A — Internal Agent Chain Lab: READ FIRST

## 1. Current repo state for this track

- **Release / ops reporting**: `release/` provides workspace discovery (`reporting_workspaces`), review state (`review_state`), package build (`package_builder`), workspace diff/rerun/timeline (`workspace_rerun_diff`), dashboard data (`dashboard_data`). Workspaces live under `data/local/workspaces/<workflow>/<run_id>/` with `manifest.json` or `workspace_manifest.json`.
- **Pilot / cohort**: Referenced in CLI (`pilot start-session`, `capture-feedback`, `aggregate`, etc.) and in `dashboard_data` (pilot_dir, cohort reports). Session/feedback/aggregate logic is documented in M21; pilot Python modules may live in parent repo or be optional for this subproject.
- **Devlab**: `devlab/config.py` (paths), `devlab/experiments.py` (experiment definitions JSON, queue, load/save). Pattern: sandbox root `data/local/devlab`, experiments in `experiments/`, queue in `experiment_queue.json`.
- **Eval**: `eval/board.py`, `eval/trend.py` — run listing, comparison, scoring. Useful pattern for “compare two runs.”
- **Mission control**: `mission_control/state.py` aggregates product/eval/devlab/incubator state from local sources (read-only).
- **CLI**: `release_group` (verify, run, demo, package, report), `review_group` (list-workspaces, show-workspace, diff-workspaces, approve-artifact, build-package, etc.), `pilot_group`, `dashboard_group`. No chain or sequential-run concept today.

## 2. Exact reusable workflow entrypoints

| Entrypoint | Type | Purpose |
|------------|------|---------|
| `workflow-dataset release demo --workflow <w> --save-artifact [--context-file F] [--context-text T] [--input-pack P] [--retrieval] [--rerun-from PATH] [--intake I]` | CLI | Produce workspace under `data/local/workspaces/<workflow>/<run_id>/`. |
| `workflow-dataset review list-workspaces` | CLI | List recent workspaces. |
| `workflow-dataset review show-workspace <path>` | CLI | Show one workspace inventory. |
| `workflow-dataset review diff-workspaces <path_a> <path_b>` | CLI | Compare two workspace runs. |
| `workflow-dataset review approve-artifact <workspace> --artifact <name>` | CLI | Mark artifact approved. |
| `workflow-dataset review build-package <workspace> [--profile P]` | CLI | Build package under `data/local/packages/<ts_id>/`. |
| `get_workspace_inventory(workspace_path)`, `list_reporting_workspaces(root, limit)` | API | release.reporting_workspaces |
| `infer_rerun_args(manifest)`, `diff_workspaces(path_a, path_b)`, `workspace_timeline(root, workflow, limit)` | API | release.workspace_rerun_diff |
| `load_review_state(ws)`, `get_approved_artifacts(ws)`, `set_artifact_state(ws, artifact_name, state)` | API | release.review_state |
| `build_package(workspace_path, repo_root, profile)` | API | release.package_builder |
| `utc_now_iso()`, `stable_id(*parts, prefix)` | API | utils.dates, utils.hashes |

## 3. Exact chain-lab gap

- **No chain definition**: No local, inspectable format for “ordered steps + expected inputs/outputs + stop conditions + workflow names + variant label.”
- **No chain runner**: Cannot “run one chain,” inspect outputs per step, stop/rerun, or run chain variants for comparison.
- **No step output persistence**: No persisted step input snapshot, step output artifacts, step status, step timing, or chain run manifest; no failure summary on step failure.
- **No chain reports**: No per-step report, final run summary, chain artifact tree, or comparison between two chain runs/variants.
- **No internal-only boundary**: Concept is missing; this track adds it as operator-started, local, transparent, no auto-merge/auto-apply.

## 4. Proposed file plan

| Module | Path | Responsibility |
|--------|------|----------------|
| A — definition + reuse | `chain_lab/definition.py` | Chain schema (id, description, steps, expected inputs/outputs, stop_conditions, workflow_names, variant_label). Load/save under `data/local/chain_lab/chains/`. Reuse map doc in `docs/M23A_CHAIN_LAB_REUSE_MAP.md`. |
| B — manifest/state | `chain_lab/manifest.py` | Run manifest (chain_id, run_id, variant_label, started_at, ended_at, step_results[], status, failure_summary). Persist under `data/local/chain_lab/runs/<run_id>/`. |
| C — runner | `chain_lab/runner.py` | Run one chain: execute steps (subprocess CLI or direct API where available), collect step output paths, handle stop/cancel (e.g. stop after first failure), persist manifest and step results. |
| D — persistence + reporting | `chain_lab/persistence.py` | Per-step: input snapshot, output artifact paths, status, timing. `chain_lab/report.py`: per-step report, final summary, artifact tree. |
| E — compare/rerun | `chain_lab/compare.py` | Compare two chain runs (by run_id or variant); optional rerun helper. |
| Config | `chain_lab/config.py` | Sandbox root `data/local/chain_lab`, chains dir, runs dir. |
| CLI | `cli.py` (one block) | New `chain_group`: `chain define`, `chain run`, `chain report`, `chain compare`, `chain list-runs`. |
| F — tests/docs | `tests/test_chain_lab.py`, `docs/M23A_CHAIN_LAB_*.md` | Focused tests; sample chain definition, sample report, sample comparison. |

## 5. Collision-risk note for shared files (e.g. `cli.py`)

- **cli.py**: Add a single new Typer `chain_group` and 4–6 commands in one contiguous block. Do not refactor or move existing release/pilot/review commands. Import chain_lab only inside the new command functions or at the top of the new block to avoid pulling optional deps into every CLI load if needed later.
- **release/** and **review/** and **devlab/** and **eval/** : No changes to existing modules except we **call** them (CLI via subprocess or existing APIs). No new dependencies from those packages on chain_lab.

---

*Next: implement Modules A → B → C → D → E → F in order.*
