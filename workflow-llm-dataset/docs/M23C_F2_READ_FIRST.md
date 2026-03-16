# M23C-F2 — Local File/Folder + Notes Adapter — Read First

## 1. What exists (from F1)

- **desktop_adapters package:** `contracts.py` (ActionSpec, AdapterContract, BUILTIN_ADAPTERS), `registry.py` (register/list/get/check_availability), `simulate.py` (run_simulate → SimulateResult, preview-only; no real I/O).
- **file_ops adapter:** Contract only — actions read_file, list_dir, write_file; simulate prints "Would read/list/write"; no real execution.
- **notes_document adapter:** Contract only — actions create_note, append_to_note; simulate preview only.
- **CLI:** `adapters list`, `adapters show --id`, `adapters simulate --id --action --param`.
- **Tests:** test_desktop_adapters.py (registry, simulate success/fail).

## 2. What is reusable

- **AdapterContract / ActionSpec** — Extend file_ops and notes_document with new F2 actions; keep existing F1 actions for backward compatibility.
- **Registry** — No change; same list/get/register.
- **run_simulate()** — Keep as-is for preview; extend preview strings for new actions. Simulate remains the default; real read-only execution is explicit via a new path (run_execute).
- **Sandbox pattern** — `data/local/...` (edge/profile.py SANDBOX_PATHS, chain_lab, devlab); add `data/local/desktop_adapters/sandbox` for snapshot_to_sandbox.
- **Settings** — paths, agent.sandbox_enabled; optional repo_root for sandbox resolution.
- **Apply pattern** — Copy only after confirm; we do copy only into sandbox (no apply to user paths) and never mutate originals.

## 3. What F2 adds

- **File/folder adapter (file_ops):** New actions with real read-only/sandbox-only execution:
  - **inspect_path** — Read metadata (exists, is_file, is_dir, size, mtime); no content read.
  - **list_directory** — List directory entries (names + basic type); no recursion by default.
  - **snapshot_to_sandbox** — Copy file or directory from source path into sandbox; originals unchanged.
- **Notes/text adapter (notes_document):** New actions with real read-only execution:
  - **read_text** — Read text file content (UTF-8); return content string.
  - **summarize_text_for_workflow** — Read and produce a short summary (e.g. first/last lines or length); for workflow context.
  - **propose_status_from_notes** — Read notes and return suggested status lines (e.g. bullet points); simulate-first “suggested actions”, no write.
- **Provenance/report hooks** — Structured result from execute (adapter_id, action_id, path, timestamp, outcome) for reporting/audit.
- **Execute layer** — run_execute(adapter_id, action_id, params, sandbox_root) for file_ops and notes_document only; returns result + provenance; no writes to originals.
- **CLI** — `adapters run` (or `adapters execute`) with --id, --action, --param, optional --sandbox; prints result and provenance.
- **Tests and docs** — Tests for file/notes runners and run_execute; delivery doc with samples and CLI usage.

## 4. What must not change

- **No real file edits to originals** — Only read and copy-into-sandbox; no write, move, or delete on user paths.
- **No broad filesystem watcher** — No continuous scanning or watcher process.
- **No hidden ingestion** — All reads explicit (inspect, list, read, snapshot) via adapter actions and CLI/API.
- **browser_open and app_launch** — Remain simulate-only; no new execution in F2.
- **F1 simulate behavior** — run_simulate unchanged for unknown adapters/actions; new actions get preview text only in simulate.
- **Existing execution_modes and apply confirmation** — Unchanged.

## 5. File plan

| Item | Path | Content |
|------|------|--------|
| Pre-coding doc | docs/M23C_F2_READ_FIRST.md | This file. |
| Contracts | desktop_adapters/contracts.py | Add ActionSpecs to file_ops: inspect_path, list_directory, snapshot_to_sandbox. Add to notes_document: read_text, summarize_text_for_workflow, propose_status_from_notes. Update capability text for F2. |
| Sandbox config | desktop_adapters/sandbox_config.py | get_sandbox_root(repo_root?) → data/local/desktop_adapters/sandbox. |
| File runner | desktop_adapters/file_runner.py | run_inspect_path(path), run_list_directory(path), run_snapshot_to_sandbox(source_path, sandbox_root, subdir?). Read-only + copy to sandbox only. |
| Notes runner | desktop_adapters/notes_runner.py | run_read_text(path), run_summarize_text_for_workflow(path), run_propose_status_from_notes(path). Read-only; no writes. |
| Execute layer | desktop_adapters/execute.py | run_execute(adapter_id, action_id, params, sandbox_root?) → ExecuteResult (output, provenance list). Dispatch to file_runner / notes_runner. |
| Simulate | desktop_adapters/simulate.py | Add preview branches for new actions (inspect_path, list_directory, snapshot_to_sandbox, read_text, summarize_text_for_workflow, propose_status_from_notes). |
| Package init | desktop_adapters/__init__.py | Export execute.run_execute, ExecuteResult, provenance types; get_sandbox_root. |
| CLI | cli.py | adapters run --id --action --param [--sandbox] [--repo-root]; call run_execute; print result and provenance. |
| Tests | tests/test_desktop_adapters.py | Tests for file_runner, notes_runner, run_execute (tmp_path); no write to originals; snapshot copies into sandbox only. |
| Delivery doc | docs/M23C_F2_DELIVERY.md | Modified/created files, CLI usage, sample outputs, tests, remaining weaknesses. |

## 6. Safety note

- **Read-only and sandbox-only writes:** All file_ops and notes_document execution in F2 is either (1) read-only (inspect, list, read_text, summarize, propose_status) or (2) copy into sandbox only (snapshot_to_sandbox). No write, move, or delete to paths outside the sandbox.
- **Sandbox under repo:** Snapshot target is `data/local/desktop_adapters/sandbox` (or override via --sandbox); no writing outside repo/local.
- **Explicit run:** Real execution only via `adapters run` (or `adapters execute`); simulate remains default and unchanged.
- **Provenance:** Each execution records adapter_id, action_id, path(s), outcome for audit; no hidden ingestion.
- **No watchers, no cloud:** No filesystem watcher; no cloud APIs; local-first only.
