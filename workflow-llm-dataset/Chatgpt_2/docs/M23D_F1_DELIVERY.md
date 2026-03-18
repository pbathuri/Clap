# M23D-F1 — Capability Discovery + Approval Registry — Delivery

## 1. Files modified

| File | Change |
|------|--------|
| `workflow-llm-dataset/src/workflow_dataset/cli.py` | Added capabilities_group (capabilities scan, capabilities report, capabilities approvals); approvals_group (approvals list). _approvals_list_impl shared. |

## 2. Files created

| File | Purpose |
|------|--------|
| `docs/M23D_F1_READ_FIRST.md` | Pre-coding: adapter layer summary, reusable pieces, file plan, risk note. |
| `docs/M23D_F1_DELIVERY.md` | This file. |
| `src/workflow_dataset/capability_discovery/__init__.py` | Package exports. |
| `src/workflow_dataset/capability_discovery/models.py` | CapabilityProfile, AdapterCapability, ActionScope. |
| `src/workflow_dataset/capability_discovery/approval_registry.py` | ApprovalRegistry; load_approval_registry, save_approval_registry, get_registry_path (data/local/capability_discovery/approvals.yaml). |
| `src/workflow_dataset/capability_discovery/discovery.py` | run_scan(repo_root?, config_path?, approval_registry?) → CapabilityProfile (adapters + approval registry only; no heavy scan). |
| `src/workflow_dataset/capability_discovery/report.py` | format_profile_report(profile) → text report. |
| `tests/test_capability_discovery.py` | Tests for run_scan, report, approval registry load/save, get_registry_path. |

## 3. Sample capability report

Output of `workflow-dataset capabilities report` (excerpt):

```markdown
# Capability profile

## Adapters available
- **file_ops** (file_ops)  available=True  simulate=yes  real_execution=yes  actions=6
  executable_actions: inspect_path, list_directory, snapshot_to_sandbox
- **notes_document** (notes_document)  available=True  simulate=yes  real_execution=yes  actions=5
  executable_actions: read_text, summarize_text_for_workflow, propose_status_from_notes
- **browser_open** (browser_open)  available=True  simulate=yes  real_execution=no  actions=1
- **app_launch** (app_launch)  available=True  simulate=yes  real_execution=no  actions=1

## Approved paths
- (none in registry)

## Approved apps
- Notes
- Safari
- Terminal
...

## Action scopes (simulate vs executable)
- file_ops.read_file  simulate_only
- file_ops.inspect_path  executable
...
```

## 4. Sample approval registry

File: `data/local/capability_discovery/approvals.yaml` (optional; created by user or tooling).

```yaml
approved_paths:
  - /tmp/readonly
  - data/docs
approved_apps:
  - Notes
  - Safari
  - Terminal
approved_action_scopes:
  - adapter_id: file_ops
    action_id: inspect_path
    executable: true
```

If the file is missing, load_approval_registry returns empty lists; run_scan still reports adapters and uses built-in APPROVED_APP_NAMES for approved_apps in the profile.

## 5. CLI usage

```bash
workflow-dataset capabilities scan
workflow-dataset capabilities scan --repo-root /path/to/repo

workflow-dataset capabilities report
workflow-dataset capabilities report --output capability_report.md

workflow-dataset capabilities approvals

workflow-dataset approvals list
workflow-dataset approvals list --repo-root /path/to/repo
```

## 6. Tests run

```bash
cd workflow-llm-dataset
pytest tests/test_capability_discovery.py -v
```

**8 tests:** run_scan returns profile with ≥4 adapters; file_ops has executable_actions; browser_open simulate-only; format_profile_report contains adapters/paths/apps/scopes; approval registry load empty when missing; save and load round-trip; get_registry_path; run_scan uses provided approval registry. All passed.

## 7. Remaining weaknesses (F1 only)

- **Approval registry not wired to execution:** approved_paths and approved_action_scopes are for reporting only; adapters do not yet check the registry before running.
- **No config seed for approved_paths:** Optional future: seed approved_paths from settings (e.g. paths.*, materialization_workspace_root) if registry is empty.
- **Single file store:** Approvals are one YAML file; no versioning or audit log of changes.
