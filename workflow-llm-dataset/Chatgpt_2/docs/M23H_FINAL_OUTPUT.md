# M23H — Desktop Bridge Validation + Gated Activation — Final Output

## 1. Files modified

| File | Change |
|------|--------|
| `src/workflow_dataset/desktop_adapters/execute.py` | Added `repo_root` parameter to `run_execute`; import and call `check_execution_allowed` before running real execution; on refusal return `ExecuteResult(success=False, message=refusal_msg)`. |
| `src/workflow_dataset/cli.py` | `adapters run`: resolve `repo_root_path` from `--repo-root` and pass `repo_root=repo_root_path` into `run_execute`. |
| `src/workflow_dataset/mission_control/state.py` | Added block 6: **desktop_bridge** (adapters_count, adapter_ids, approvals_path, approvals_file_exists, approved_paths_count, approved_action_scopes_count, tasks_count, coordination_nodes, coordination_edges); local_sources["approval_registry"]. |
| `src/workflow_dataset/mission_control/report.py` | Added **[Desktop bridge]** section: adapters count and ids, approvals present/missing, path, task_demos count, graph nodes/edges, approved_paths/scopes counts when present. |
| `src/workflow_dataset/mission_control/next_action.py` | Added `replay_task` to ACTIONS; added branch: when `coordination_graph_summary.tasks_count > 0` and no higher-priority signal, return action `replay_task` with rationale and detail. |
| `tests/test_desktop_adapters.py` | Added M23H tests: `test_run_execute_allowed_when_registry_missing`, `test_run_execute_refused_when_action_not_in_approved_scopes`, `test_run_execute_allowed_when_action_in_approved_scopes`, `test_run_execute_refused_when_path_not_in_approved_paths`. |
| `tests/test_mission_control.py` | Added `test_mission_control_state_includes_desktop_bridge`; extended `test_format_report` state with `coordination_graph_summary` and `desktop_bridge`, assert "[Desktop bridge]" in report; added `test_recommend_replay_task_when_tasks_available`. |
| `docs/PILOT_OPERATOR_GUIDE.md` | Added **§10. Desktop bridge (M23H)**: verify commands, simulate-only vs real, enabling safe approved execution, pointer to M23H_DESKTOP_BRIDGE_OPERATOR.md. |

## 2. Files created

| File | Purpose |
|------|--------|
| `src/workflow_dataset/capability_discovery/approval_check.py` | `check_execution_allowed(adapter_id, action_id, params, repo_root, registry)` — when registry file exists enforces approved_action_scopes (if non-empty) and approved_paths for path-using actions; returns (allowed, message). |
| `tests/test_m23h_approval_check.py` | Unit tests for approval_check: registry missing → allow; scope not listed / executable false → refuse; scope listed → allow; path not under approved → refuse; path under approved → allow. |
| `docs/M23H_DESKTOP_BRIDGE_OPERATOR.md` | Operator reference: verify bridge commands, simulate-only vs real table, how to enable approved real execution, example approvals.yaml, safety summary. |
| `docs/M23H_FINAL_OUTPUT.md` | This file. |

## 3. Exact commands used to validate the current bridge

Run from project root (or with `--repo-root <path>` where supported):

```bash
workflow-dataset adapters list
workflow-dataset capabilities scan
workflow-dataset approvals list
workflow-dataset tasks list
workflow-dataset graph summary
workflow-dataset mission-control
```

Validation (e.g. via CliRunner): exit code 0; output includes adapter list, capability scan (adapters, approved_paths/apps/scopes), approvals path, tasks list, graph summary, and mission-control report including **[Desktop bridge]** (adapters=4, approvals present/missing, task_demos, graph nodes/edges).

## 4. What was already present vs what was added

| Area | Already present | Added in M23H |
|------|-----------------|---------------|
| Desktop adapters (list/show/simulate/run) | Full implementation | Approval gating in `run_execute` when registry exists; `repo_root` passed from CLI. |
| Capability discovery / approvals | Scan, report, approvals list, load/save registry | `approval_check.check_execution_allowed` and wiring into `run_execute`. |
| Task demos / coordination graph | define, replay (simulate), list, show; graph from-task, summary, export, inspect | No change; mission control now surfaces desktop_bridge and replay_task recommendation. |
| Mission control | state (product, eval, dev, incubator, coordination_graph_summary), report, next_action | desktop_bridge in state; [Desktop bridge] in report; replay_task in next_action when tasks exist. |
| Real execution | file_ops + notes_document real actions (read-only/sandbox) | Gated by approval registry when file exists; clear refusal message when not approved. |

## 5. Exact approval gating behavior

- **Registry file absent** (`data/local/capability_discovery/approvals.yaml` does not exist): No checks; all real-execution actions allowed (backward compatible).
- **Registry file exists:**
  - **approved_action_scopes** non-empty: `(adapter_id, action_id)` must appear in the list with `executable: true`. Otherwise: refuse with message *"Action &lt;adapter_id&gt;.&lt;action_id&gt; not in approved_action_scopes with executable=true. Add it to data/local/capability_discovery/approvals.yaml approved_action_scopes or remove the registry file."*
  - **approved_paths** non-empty: For path-using actions (inspect_path, list_directory, snapshot_to_sandbox, read_text, summarize_text_for_workflow, propose_status_from_notes), the `path` param must resolve to a path under one of the approved_paths (prefix match). Otherwise: refuse with *"Path not in approved_paths. Add path to data/local/capability_discovery/approvals.yaml approved_paths or clear approved_paths to allow all paths."*
- Refusal is returned as `ExecuteResult(success=False, message=...)`; CLI prints the message and exits non-zero. No silent bypass.

## 6. Exact real-execution actions now allowed (when approved or no registry)

Unchanged from pre-M23H; all are read-only or sandbox-only:

- **file_ops:** inspect_path, list_directory, snapshot_to_sandbox  
- **notes_document:** read_text, summarize_text_for_workflow, propose_status_from_notes  

No new real-execution actions were added. browser_open and app_launch remain simulate-only.

## 7. Exact tests run

```bash
pytest tests/test_m23h_approval_check.py -v
pytest tests/test_desktop_adapters.py -k "approval or run_execute_refused or run_execute_allowed_when" -v
pytest tests/test_mission_control.py -v
```

All passed. Coverage includes: approval_check (registry missing, scope listed/not listed, executable false, path under/not under approved); run_execute (allowed when registry missing, refused when action not in scopes, allowed when in scopes, refused when path not in approved_paths); mission control (state has desktop_bridge, report has [Desktop bridge], replay_task recommended when tasks_count > 0 and no higher-priority signal).

## 8. Remaining simulate-only areas

- **browser_open**, **app_launch:** Real execution not implemented; simulate only.
- **Task replay** (`tasks replay`): Uses only `run_simulate()` per step; no `run_execute()` in replay path.
- **write_file, create_note, append_to_note:** Contract-only; supports_real=False; simulate preview only.

## 9. Recommended next phase after M23H

- **Optional:** Add an explicit “replay for real” path that runs steps through `run_execute` when each step’s adapter/action is approved and path (if any) is under approved_paths; keep it off by default and document in operator doc.
- **Optional:** Enrich mission control desktop_bridge with “last replay result” or “recommended task id” when task demos exist.
- **Continue:** Use the desktop bridge in operator workflows (verify → approvals → adapters run / tasks replay) and gather feedback; keep approval registry as the single gate for any future real-execution expansion.
