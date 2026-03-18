# M23C-F2 — Local File/Folder + Notes Adapter — Delivery

## 1. Files modified

| File | Change |
|------|--------|
| `workflow-llm-dataset/src/workflow_dataset/desktop_adapters/contracts.py` | file_ops: added actions inspect_path, list_directory, snapshot_to_sandbox; supports_real_execution=True. notes_document: added read_text, summarize_text_for_workflow, propose_status_from_notes; supports_real_execution=True. Updated capability descriptions. |
| `workflow-llm-dataset/src/workflow_dataset/desktop_adapters/simulate.py` | Added preview branches for inspect_path, list_directory, snapshot_to_sandbox, read_text, summarize_text_for_workflow, propose_status_from_notes. |
| `workflow-llm-dataset/src/workflow_dataset/desktop_adapters/__init__.py` | Exported run_execute, ExecuteResult, ProvenanceEntry, get_sandbox_root. |
| `workflow-llm-dataset/src/workflow_dataset/cli.py` | adapters_group help updated; added `adapters run` command (--id, --action, --param, --sandbox, --repo-root). |
| `workflow-llm-dataset/tests/test_desktop_adapters.py` | test_check_availability_file_ops expects supports_real_execution=True; added F2 tests for file_runner, notes_runner, run_execute. |

## 2. Files created

| File | Purpose |
|------|--------|
| `docs/M23C_F2_READ_FIRST.md` | Pre-coding: what exists, reusable, F2 adds, must not change, file plan, safety note. |
| `docs/M23C_F2_DELIVERY.md` | This file. |
| `src/workflow_dataset/desktop_adapters/sandbox_config.py` | get_sandbox_root(repo_root?) → data/local/desktop_adapters/sandbox. |
| `src/workflow_dataset/desktop_adapters/file_runner.py` | run_inspect_path, run_list_directory, run_snapshot_to_sandbox (read-only + copy to sandbox only). |
| `src/workflow_dataset/desktop_adapters/notes_runner.py` | run_read_text, run_summarize_text_for_workflow, run_propose_status_from_notes (read-only). |
| `src/workflow_dataset/desktop_adapters/execute.py` | run_execute(adapter_id, action_id, params, sandbox_root?) → ExecuteResult (output, provenance). ProvenanceEntry for reporting. |

## 3. CLI usage

```bash
# List adapters (file_ops, notes_document now show real_execution=True for F2 actions)
workflow-dataset adapters list

# Show file_ops contract (includes inspect_path, list_directory, snapshot_to_sandbox)
workflow-dataset adapters show --id file_ops

# Simulate (preview only)
workflow-dataset adapters simulate --id file_ops --action inspect_path --param path=/tmp
workflow-dataset adapters simulate --id notes_document --action read_text --param path=./notes.txt

# Run (read-only or copy to sandbox only)
workflow-dataset adapters run --id file_ops --action inspect_path --param path=/tmp
workflow-dataset adapters run --id file_ops --action list_directory --param path=/tmp
workflow-dataset adapters run --id file_ops --action snapshot_to_sandbox --param path=./my_folder --param subdir=backup
workflow-dataset adapters run --id notes_document --action read_text --param path=./notes.txt
workflow-dataset adapters run --id notes_document --action summarize_text_for_workflow --param path=./notes.txt
workflow-dataset adapters run --id notes_document --action propose_status_from_notes --param path=./notes.txt

# Optional: override sandbox or repo root
workflow-dataset adapters run -i file_ops -a snapshot_to_sandbox -p path=./src --sandbox ./data/local/desktop_adapters/sandbox
workflow-dataset adapters run -i file_ops -a list_directory -p path=. --repo-root /path/to/repo
```

## 4. Sample outputs

### adapters run --id file_ops --action inspect_path --param path=/tmp

```
Run OK
  exists: True
  is_file: False
  is_dir: True
  size_bytes: None
  mtime_iso: 2025-03-15T12:00:00+00:00
Provenance:
  file_ops/inspect_path ok /tmp
```

### adapters run --id file_ops --action list_directory --param path=.

```
Run OK
  entries: 12 entries
    {'name': 'configs', 'is_file': False, 'is_dir': True}
    {'name': 'docs', 'is_file': False, 'is_dir': True}
    ...
Provenance:
  file_ops/list_directory ok .
```

### adapters run --id notes_document --action read_text --param path=./README.md

```
Run OK
  content: # Project ... (truncated if >500 chars in CLI)
Provenance:
  notes_document/read_text ok ./README.md
```

### adapters run --id file_ops --action snapshot_to_sandbox --param path=./docs --param subdir=docs_backup

```
Run OK
  sandbox_path: /path/to/repo/data/local/desktop_adapters/sandbox/docs_backup/docs
  copied_count: 42
Provenance:
  file_ops/snapshot_to_sandbox ok ./docs
```

## 5. Tests run

```bash
cd workflow-llm-dataset
pytest tests/test_desktop_adapters.py -v
```

**25 tests:** F1 registry/simulate tests (10) + F2 file_runner (5), notes_runner (3), run_execute (6), run_execute failure (2). All pass.

- **File runner:** inspect_path (file, dir, missing), list_directory (entries), snapshot_to_sandbox (copy to sandbox; original unchanged).
- **Notes runner:** read_text, summarize_text_for_workflow, propose_status_from_notes.
- **Execute:** file_ops inspect_path, list_directory, snapshot_to_sandbox; notes_document read_text, propose_status_from_notes; unknown adapter and unsupported action return success=False.

## 6. Remaining weaknesses (F2 only)

- **No recursion in list_directory** — Single directory only; no recursive listing option.
- **Snapshot overwrites** — If sandbox subdir already exists with same name, copytree may fail (dirs_exist_ok=False); no merge semantics.
- **Text encoding** — read_text uses UTF-8 with errors=replace; no encoding param.
- **Propose status** — Heuristic is simple (first 20 non-empty lines as bullets); no LLM or structured extraction.
- **Provenance in memory only** — ExecuteResult carries provenance for the call; no persistent audit log yet.
- **browser_open / app_launch** — Still simulate-only; no change in F2.
