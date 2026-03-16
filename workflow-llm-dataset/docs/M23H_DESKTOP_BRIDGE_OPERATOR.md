# M23H — Desktop bridge operator reference

How to verify the desktop bridge, what is simulate-only, and how to enable safe approved real execution.

---

## 1. Verify the desktop bridge

Run from project root (or pass `--repo-root <path>` where the CLI supports it).

| Command | Purpose |
|--------|--------|
| `workflow-dataset adapters list` | List adapters and simulate/real_execution support |
| `workflow-dataset adapters show <id>` | Show one adapter’s actions and params |
| `workflow-dataset adapters simulate -i <id> -a <action> -p path=...` | Run action in simulate mode (no real execution) |
| `workflow-dataset capabilities scan` | Adapter count, approved_paths/apps/action_scopes (from registry) |
| `workflow-dataset capabilities report` | Full capability report |
| `workflow-dataset approvals list` | Path to approvals.yaml and current approved_paths / approved_action_scopes |
| `workflow-dataset tasks list` | List task demo IDs |
| `workflow-dataset tasks show <id>` | Show task definition and steps |
| `workflow-dataset tasks replay <id>` | Replay task in **simulate only** (no real execution) |
| `workflow-dataset graph summary` | Coordination graph: tasks count, nodes, edges |
| `workflow-dataset graph from-task <id>` | Build graph from one task |
| `workflow-dataset mission-control` | Full mission-control report including **[Desktop bridge]** |

**Expected:** All commands exit 0. Mission-control report shows a **[Desktop bridge]** line with adapters count, approvals present/missing, task_demos count, graph nodes/edges. When task demos exist, recommended next action may be **replay_task**.

---

## 2. What is simulate-only vs real execution

| Area | Mode | Notes |
|------|------|--------|
| **browser_open**, **app_launch** | Simulate only | No real browser open or app launch; preview/validation only |
| **Task replay** (`tasks replay`) | Simulate only | Each step runs via simulate; no run_execute in replay path |
| **file_ops** (inspect_path, list_directory, snapshot_to_sandbox) | Real when allowed | Read-only or copy to sandbox; gated by approval registry when file exists |
| **notes_document** (read_text, summarize_text_for_workflow, propose_status_from_notes) | Real when allowed | Read-only; gated by approval registry when file exists |

**Real execution** is only for the file_ops and notes_document actions above. All other adapter actions are simulate-only.

---

## 3. How to enable safe approved real execution

### When there is no approval registry

If `data/local/capability_discovery/approvals.yaml` **does not exist**:

- All real-execution actions (file_ops, notes_document above) are **allowed** (backward compatible).
- No path or scope checks are applied.

### When the approval registry exists

If `data/local/capability_discovery/approvals.yaml` **exists**:

1. **approved_action_scopes** (if non-empty): Only actions listed with `executable: true` may run. Any other action is **refused** with a message like:  
   `Action <adapter_id>.<action_id> not in approved_action_scopes with executable=true. Add it to data/local/capability_discovery/approvals.yaml ...`
2. **approved_paths** (if non-empty): For path-using actions (inspect_path, list_directory, snapshot_to_sandbox, read_text, etc.), the `path` parameter must resolve to a location **under** one of the approved path prefixes. Otherwise execution is **refused** with:  
   `Path not in approved_paths. Add path to data/local/capability_discovery/approvals.yaml approved_paths ...`

### Example approvals.yaml

```yaml
approved_paths:
  - /tmp/safe
  - data/local
approved_apps: []   # used for reporting / future app-launch allowlist
approved_action_scopes:
  - adapter_id: file_ops
    action_id: inspect_path
    executable: true
  - adapter_id: file_ops
    action_id: list_directory
    executable: true
  - adapter_id: notes_document
    action_id: read_text
    executable: true
```

### Running real actions

- **Simulate (always safe):**  
  `workflow-dataset adapters simulate -i file_ops -a inspect_path -p path=/some/path`
- **Real (gated):**  
  `workflow-dataset adapters run -i file_ops -a inspect_path -p path=/tmp/safe/foo [--repo-root .]`  
  If the registry exists and path is not under an approved_path (or action not in approved_action_scopes), the CLI prints the refusal message and exits non-zero.

---

## 4. Safety summary

- **Local-first, privacy-first:** No hidden cloud calls; all discovery and execution are local.
- **Simulate-first:** Task replay and browser/app actions are simulate-only.
- **Approval-gated:** When the registry file exists, real execution respects approved_paths and approved_action_scopes; missing approval produces a clear refusal.
- **Sandbox-only by default:** `snapshot_to_sandbox` writes only under the configured sandbox root (e.g. `data/local/desktop_adapters/sandbox`); it does not mutate the source path.
