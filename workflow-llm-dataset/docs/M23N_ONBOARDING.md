# M23N — First-Run Onboarding + Capability / Approval Bootstrap

Local-first onboarding wizard and bootstrap layer. No hidden scans, no auto-grant.

## CLI usage

```bash
# Show onboarding status (default when no subcommand)
workflow-dataset onboard
workflow-dataset onboard --config configs/settings.yaml

# Status only (profile, env readiness, approvals, blocked, next steps)
workflow-dataset onboard status

# Create or refresh bootstrap profile and first-run summary (persists to data/local/onboarding/)
workflow-dataset onboard bootstrap

# Review and apply approval choices (paths, scopes). No auto-grant.
workflow-dataset onboard approve
workflow-dataset onboard approve --paths "data/local,data/local/workspaces"
workflow-dataset onboard approve --approve-all-suggested
workflow-dataset onboard approve --refuse-paths "data/local/workspaces"
```

## Bootstrap profile

- **Path:** `data/local/onboarding/bootstrap_profile.yaml`
- **Contents:** machine_id, repo_root, adapters, capabilities summary, approval counts, trusted real actions, simulate-only list, recommended job packs/routines, edge readiness, setup session if any.
- **Inspect:** `workflow-dataset onboard status` or open the file.

## Sample bootstrap profile (excerpt)

```yaml
machine_id: "a1b2c3d4e5f6..."
repo_root: "/path/to/workflow-llm-dataset"
created_at: "2025-03-16T12:00:00..."
adapter_ids: ["file_ops", "notes_document", "browser_open", ...]
approval_registry_exists: false
approved_paths_count: 0
approved_action_scopes_count: 0
trusted_real_actions: []
ready_for_real: false
simulate_only_adapters: ["browser_open", ...]
recommended_job_packs: []
edge_ready: false
edge_checks_passed: 3
edge_checks_total: 5
setup_session_id: ""
setup_stage: ""
```

## Sample approval bootstrap summary

- **Suggested paths:** data/local, data/local/workspaces, data/local/pilot, data/local/notes
- **Suggested action scopes:** file_ops.inspect_path, file_ops.list_directory, notes_document.read_text, …
- **If you refuse:** Real execution for path-using and scope-listed actions remains blocked until you add approvals to `data/local/capability_discovery/approvals.yaml`.
- **If you approve:** Approved paths and scopes are written to the registry; `run_execute` will allow real execution only for those.

## Sample first-run product summary

- **What the product can do safely now:** Run all adapters in simulate mode; use console and dashboard; run job packs in simulate or real (if approved).
- **Trusted / benchmarked:** file_ops.inspect_path, notes_document.read_text, … (when approved).
- **Simulate-only:** browser_open, app_launch, and actions not in the trusted subset.
- **Recommended first workflow:** `workflow-dataset onboard bootstrap` or `workflow-dataset console`.

## Safety

- **No hidden scans:** Uses existing capability discovery (adapters + approval registry) and edge checks. No new filesystem crawling.
- **No auto-grant:** Approvals are written only when the user explicitly approves via `onboard approve` or by editing the registry file.
- **Local-only:** All data under `data/local/onboarding/` and `data/local/capability_discovery/`. No cloud or telemetry.
- **Gates unchanged:** `approval_check.check_execution_allowed` still gates real execution; this milestone only makes approval setup easier.

## Tests

```bash
pytest tests/test_onboarding.py -v
```

Covers: bootstrap profile build/save/load, onboarding status, first-run summary, approval request collection, approval bootstrap summary, apply approval choices (create, refuse, scopes), and safe first-run messaging.
