# Local operator — repeatable first-run (Phase 1.5)

End-to-end path on **macOS** with **no manual JSON edits**. Uses the approval registry at `data/local/capability_discovery/approvals.yaml` and operator state at `data/local/operator/state.json`.

## 1. Clean slate (optional)

From the repo root:

```bash
rm -f data/local/capability_discovery/approvals.yaml
rm -f data/local/operator/state.json
```

A fresh clone typically has neither file; you start with **zero** approved folders until you add one.

## 2. Inspect setup

```bash
export PYTHONPATH=src   # if not using an installed package
workflow-dataset local setup-status --repo-root .
```

You should see **Machine** (platform, registry, osascript) and **Operator** next steps.

## 3. Register an approved folder

Use a **real** directory (absolute or relative to repo root):

```bash
workflow-dataset local approved-folders add --path ./my-workspace --ops read --repo-root .
workflow-dataset local approved-folders list --repo-root .
```

`path_exists=true` means the folder is reachable from the current machine.

## 4. Ingest → tools → proposals

```bash
workflow-dataset local ingest --repo-root .
workflow-dataset local discover-tools --repo-root .
workflow-dataset local propose-actions --repo-root .
```

Copy a proposal id from the output (e.g. Finder: **Open … in Finder**).

## 5. Execute (Finder)

Dry-run (no real Finder UI):

```bash
export WORKFLOW_DATASET_FINDER_DRY_RUN=1
workflow-dataset local execute-action --action-id '<finder_action_id>' --approved --repo-root .
```

Real open (requires Automation for Terminal/your runner):

```bash
unset WORKFLOW_DATASET_FINDER_DRY_RUN
workflow-dataset local execute-action --action-id '<finder_action_id>' --approved --repo-root .
```

Ensure `approvals.yaml` includes scopes for `finder_open.open_folder` (and paths) if you use a strict registry; use `workflow-dataset approvals add-path` / scope tooling as needed.

## 6. Summary & shell snapshot

```bash
workflow-dataset local summary --repo-root .
workflow-dataset local summary --json --repo-root .
workflow-dataset local validate-surfaces --repo-root .
```

Edge-desktop / live adapter snapshots include `local_operator_summary` with the same shaped fields.

`local summary --json` also includes **`task_runs`**: `total_stored` plus **`recent`** (newest-first summaries: `run_id`, `status`, `workflow_pattern`, `artifact_path`, timestamps, prompt preview).

### Supervised task runs (plan → approve → run)

Requires an approved folder with **`write`** so artifacts can be written under `<approved-folder>/task-runs/`.

```bash
workflow-dataset local plan-task --prompt "Inspect folder and create a structured status report" --repo-root .
workflow-dataset local plan-task --prompt "..." --json --repo-root .   # structured plan or failure payload
workflow-dataset local approve-task --plan-id '<plan_id>' --repo-root .
workflow-dataset local approve-task --plan-id '<plan_id>' --json --repo-root .
workflow-dataset local run-task --plan-id '<plan_id>' --approved --repo-root .
workflow-dataset local run-task --plan-id '<plan_id>' --approved --json --repo-root .
workflow-dataset local task-status --repo-root .
workflow-dataset local list-task-runs --limit 10 --repo-root .
workflow-dataset local list-task-runs --json --limit 20 --repo-root .
workflow-dataset local task-status --run-id '<run_id>' --json --repo-root .
```

If `plan-task` exits with `unsupported`, read **`supported_workflow_patterns=`** and the **`hint=`** line (approved folders, write scope, or prompt wording).

### Snapshot JSON (strict)

`workflow-dataset demo edge-desktop-snapshot` emits **strict JSON** (safe for `python -m json.tool`). Use `-o file.json` or pipe stdout directly — avoid copying from Rich-styled logs.

Documentation paths like `/path/to/folder` in `approvals.yaml` are **ignored** for local ingest/proposals/tools/readiness counts; add a real path via `local approved-folders add`.

## 7. Revoke access

```bash
workflow-dataset local approved-folders revoke --path ./my-workspace --repo-root .
```

Re-run `ingest` and `propose-actions` so operator state matches revoked registry entries.
