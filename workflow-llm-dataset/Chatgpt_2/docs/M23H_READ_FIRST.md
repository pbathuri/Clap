# M23H — Desktop Bridge Validation + Gated Activation — Read First

## 1. What already exists for M23C–M23F

| Area | Implemented |
|------|-------------|
| **desktop_adapters** | contracts.py (file_ops, notes_document, browser_open, app_launch); registry.py; simulate.py; execute.py (file_ops: inspect_path, list_directory, snapshot_to_sandbox; notes_document: read_text, summarize_text_for_workflow, propose_status_from_notes); file_runner, notes_runner, sandbox_config, url_validation, app_allowlist. CLI: adapters list, show, simulate, run. |
| **capability_discovery** | models (CapabilityProfile, ApprovalRegistry); approval_registry (load/save data/local/capability_discovery/approvals.yaml); discovery.run_scan; report.format_profile_report. CLI: capabilities scan, report, approvals; approvals list. |
| **task_demos** | models (TaskDefinition, TaskStep); store (list_tasks, get_task, save_task); replay (replay_task_simulate — simulate only); report. CLI: tasks define, replay, list, show. |
| **coordination_graph** | models, build (task_definition_to_graph), report, export. CLI: graph from-task, summary, export, inspect. |
| **mission_control** | state.py includes coordination_graph_summary (tasks_count, total_nodes, total_edges); report.py shows [Coordination graph] line. next_action.py does not consider desktop bridge. |

## 2. Fully implemented vs partially wired

- **Fully implemented:** All CLI commands work; run_execute performs real read-only/sandbox-only actions for file_ops and notes_document; task replay runs steps via run_simulate only; graph is built from tasks; capability scan merges adapter registry + approval registry for reporting.
- **Partially wired:** (1) **Approval registry is not used to gate execution.** run_execute() does not load or check the approval registry; adapters run proceeds without approved_paths or approved_action_scopes checks. (2) **Mission control** shows coordination graph summary only; it does not show adapters available, approvals present/missing, task demo list, or a desktop-bridge-specific next action.

## 3. What is still simulate-only

- **browser_open, app_launch:** supports_real_execution=False; only simulate (URL validation and app allowlist for preview).
- **Task replay:** Uses only run_simulate(); no run_execute() in replay path.
- **write_file, create_note, append_to_note:** Contract-only; supports_real=False; simulate preview only.

## 4. What can safely become gated-real now

- **Current real execution** (inspect_path, list_directory, snapshot_to_sandbox, read_text, summarize_text_for_workflow, propose_status_from_notes) is already safe (read-only or copy-to-sandbox only). It does not need to be removed; it needs to be **gated** by the approval registry so that:
  - When the registry file exists and approved_paths is non-empty: path-using actions require the path to be under an approved path (prefix match).
  - When the registry file exists and approved_action_scopes is non-empty: (adapter_id, action_id) must appear with executable=True.
  - When the registry file is missing: allow current behavior (backward compatible).
  - When approval is missing: refuse with a clear message (e.g. "Path not in approved_paths" or "Action not in approved_action_scopes").
- **No new real-execution actions** in M23H; only add the gate. Optional: keep browser_open and app_launch simulate-only and document why.

## 5. File plan

| Phase | Item | Action |
|-------|------|--------|
| 1 | Validation | Run exact CLI commands; document in M23H_VALIDATION.md or script. Fix any partially wired CLI if needed. |
| 2 | Approval gate | Add approval_check in capability_discovery (e.g. check_path_approved, check_action_scope_approved). Call from run_execute (or a wrapper) when repo_root/registry available; pass repo_root into run_execute. Refuse with clear message when not approved. |
| 3 | Gated real-execution | No new actions. Document that only file_ops/notes_document real actions are gated; snapshot_to_sandbox and read flows remain the only real execution. |
| 4 | Mission control | state.py: add desktop_bridge (adapters_count, approvals_path, approvals_present, tasks_count, coordination summary). report.py: add [Desktop bridge] section. next_action: optional "replay task" or "define task" when tasks exist. |
| 5 | Tests + operator doc | Tests: run_execute refused when path not in approved_paths (when registry has paths); run_execute allowed when approved or registry empty. Doc: how to verify bridge, what is simulate-only, how to enable approved actions. |

## 6. Safety/risk note

- **Approval gate:** Reduces risk by requiring explicit approved_paths and/or approved_action_scopes before real execution. Refusing when approval is missing is safer than silent allow.
- **Backward compatibility:** When approvals.yaml is absent, keep current behavior (allow) so existing use is unchanged.
- **No new automation:** No background loops; no new real actions for browser/app; task replay stays simulate-only unless we add an explicit gated "replay for real" later.
- **Sandbox unchanged:** snapshot_to_sandbox still writes only under data/local/desktop_adapters/sandbox; apply/sandbox semantics elsewhere unchanged.
