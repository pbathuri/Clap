# M23A-F5 — Chain Operator Docs + Example Library + Cleanup: READ FIRST

## 1. Current state

- **Chain lab**: `chain_lab/definition.py` (load_chain, save_chain, list_chains), `manifest.py` (list_run_ids, load_run_manifest, save_run_manifest), `runner.py` (run_chain, resume_chain, retry_step), `report.py` (chain_run_report, chain_artifact_tree, resolve_run_id), `compare.py`, `config.py` (get_chains_dir, get_runs_dir). Chains under `data/local/chain_lab/chains/*.json`, runs under `data/local/chain_lab/runs/<run_id>/`.
- **CLI**: `chain list`, `chain define`, `chain run`, `chain report`, `chain resume`, `chain retry-step`, `chain compare`, `chain list-runs`, `chain artifact-tree`. No examples subcommand, no cleanup/archive.
- **Docs**: M23A_CHAIN_LAB_READ_FIRST, SUMMARY, M23A_F2_SAMPLES (report/compare samples), validation/F6 docs. No single operator-focused “how to use” guide.

## 2. Reuse

- `get_chains_dir`, `get_runs_dir`, `list_run_ids`, `load_run_manifest`, `load_chain`, `save_chain`; report and compare as-is.

## 3. What F5 adds

1. **Example chain library**: Ship 1–2 example chain JSONs (e.g. under `chain_lab/examples/` in repo). CLI: `chain examples list`, `chain examples install <id>` (copy example into chains dir).
2. **Operator docs**: One guide: how to define a chain, run one, resume/retry, inspect run history, interpret manifests and step outputs.
3. **Cleanup/archive**: `list_runs_older_than(repo_root, days)`; `archive_run(run_id, repo_root)` (move run dir to `runs/archive/<run_id>`). CLI: `chain runs archive --run <id>`, `chain cleanup --older-than 30d [--dry-run] [--archive]`. Never delete chain definitions or “current” run.
4. **Readability**: list-runs shows status, chain_id, started_at when available; optional table-style output.

## 4. What not to change

- Chain definition schema or runner behavior. No changes to release/pilot/review. Sandbox-only; no cloud, no auto-scheduler.

## 5. File plan

| Module | File(s) | Action |
|--------|---------|--------|
| A | chain_lab/examples/*.json | Add 1–2 example chain definitions. |
| A | chain_lab/examples.py | list_example_chains(), get_example_path(id), install_example(id, repo_root). |
| A | cli.py | chain examples list, chain examples install <id>. |
| B | docs/M23A_CHAIN_OPERATOR_GUIDE.md | New operator guide. |
| C | chain_lab/cleanup.py | list_runs_older_than(), archive_run(), cleanup_older_runs(older_than_days, dry_run, archive). |
| C | cli.py | chain runs archive --run <id>, chain cleanup --older-than 30d [--dry-run] [--archive]. |
| D | manifest.py or report | Optional: list_run_ids_with_meta() for list-runs table. |
| D | cli.py | list-runs: load manifest per run, print status/chain_id/started_at. |
| E | tests/test_chain_lab.py | Tests for examples list/install, archive, cleanup (dry-run). |
| E | docs/M23A_F5_DELIVERY.md | Samples and commands. |

## 6. Risk note

- Archive moves run dirs; operators can restore from archive/ if needed. Cleanup with --older-than only affects runs, not chain definitions. Dry-run by default for cleanup to avoid accidental archive.
