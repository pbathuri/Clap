# M23A-F5 — Chain Operator Docs + Example Library + Cleanup: Delivery

## 1. Files modified

- `src/workflow_dataset/cli.py` — Added `chain examples list` / `chain examples install <id>`; `chain runs archive --run <id>`; `chain cleanup --older-than 30d [--dry-run] [--archive]`; `chain list-runs` now shows chain_id, status, started_at (via list_runs_with_meta).
- `tests/test_chain_lab.py` — Added tests for examples list/install, list_runs_with_meta, list_runs_older_than, archive_run, cleanup_older_runs dry_run.

## 2. Files created

- `src/workflow_dataset/chain_lab/examples/demo_verify.json` — Example chain: single release verify step.
- `src/workflow_dataset/chain_lab/examples/ops_reporting_short.json` — Example chain: verify + weekly_status demo with save-artifact.
- `src/workflow_dataset/chain_lab/examples.py` — list_example_chains(), get_example_path(id), install_example(id, repo_root).
- `src/workflow_dataset/chain_lab/cleanup.py` — list_runs_with_meta(), list_runs_older_than(days), archive_run(run_id), cleanup_older_runs(older_than_days, dry_run, archive).
- `docs/M23A_F5_READ_FIRST.md` — File plan and risk note.
- `docs/M23A_CHAIN_OPERATOR_GUIDE.md` — Operator guide: define, run, resume/retry, inspect, manifests, cleanup/archive.
- `docs/M23A_F5_DELIVERY.md` — This file.

## 3. Example / cleanup CLI usage

```bash
# Example library
workflow-dataset chain examples list
workflow-dataset chain examples install demo_verify
workflow-dataset chain examples install ops_reporting_short

# List runs (now with chain, status, started)
workflow-dataset chain list-runs
workflow-dataset chain list-runs --limit 50

# Archive one run
workflow-dataset chain runs archive --run <run_id>

# Cleanup: list runs older than 30 days (dry-run default)
workflow-dataset chain cleanup --older-than 30d
workflow-dataset chain cleanup --older-than 7d

# Actually archive those runs
workflow-dataset chain cleanup --older-than 30d --no-dry-run --archive
```

## 4. Sample chain example

**demo_verify** (minimal):

```json
{
  "id": "demo_verify",
  "description": "Minimal chain: release verify only.",
  "steps": [
    {
      "id": "verify",
      "type": "cli",
      "label": "Release verify",
      "params": { "args": ["release", "verify"], "timeout": 60 },
      "resumable": true
    }
  ],
  "variant_label": "default"
}
```

**ops_reporting_short**: verify + `release demo --workflow weekly_status --save-artifact`.

## 5. Sample cleanup / archive output

**List old runs (dry-run):**

```
$ workflow-dataset chain cleanup --older-than 30d
Runs older than 30.0 days: 3
  abc123def456
  old_run_001
  old_run_002
Dry run. Use --no-dry-run --archive to archive these runs.
```

**Archive one run:**

```
$ workflow-dataset chain runs archive --run abc123def456
Archived: abc123def456 → /path/to/data/local/chain_lab/runs/archive/abc123def456
```

**list-runs (polished):**

```
$ workflow-dataset chain list-runs
  xyz789  chain=demo_verify  status=success  started=2025-03-16T14:00:00Z
  abc123  chain=ops_reporting_short  status=failed  started=2025-03-15T10:00:00Z
```

## 6. Tests run

```bash
cd workflow-llm-dataset && python3 -m pytest tests/test_chain_lab.py::test_list_example_chains tests/test_chain_lab.py::test_get_example_path tests/test_chain_lab.py::test_install_example tests/test_chain_lab.py::test_list_runs_with_meta tests/test_chain_lab.py::test_list_runs_older_than tests/test_chain_lab.py::test_archive_run tests/test_chain_lab.py::test_cleanup_older_runs_dry_run -v
```

Result: **7 passed**.

Full chain lab suite:

```bash
python3 -m pytest tests/test_chain_lab.py -v
```

## 7. Remaining weaknesses (this pane only)

- **Restore from archive**: No CLI to “unarchive” a run (move from archive/ back to runs/). Operators can do so manually if needed.
- **Cleanup temp artifacts**: Only run directories are archived; no separate “clean temporary/intermediate artifacts” step (e.g. pruning step caches). Can be added later.
- **Examples location**: Examples are package-bundled under `chain_lab/examples/`; adding new examples requires codebase change. Optional: allow an external examples dir via env or config.
- **list-runs with --older-than**: list-runs does not support `--older-than`; only `chain cleanup --older-than` does. Could add `chain list-runs --older-than 7d` for consistency.
