# M24D — External Capability Activation Executor (before coding)

## 1. What planning/registry layers already exist

- **external_capability/schema.py:** ExternalCapabilitySource (source_id, category, local, optional_remote, install_prerequisites, license/usage/security/approval/trust notes, supported_task_classes, supported_tiers, estimated_resource, activation_status, enabled).
- **external_capability/registry.py:** load_external_sources(), list_external_sources(), get_external_source(). Builds unified list from integration_registry, backend_registry, model_catalog; optional override file `data/local/runtime/external_capability_sources.json`.
- **external_capability/policy.py:** apply_rejection_policy(source, machine_profile, trust_posture, domain_pack_id?, task_class?) → (allowed, reason). Rejection codes: unsupported_license, resource_too_high, not_useful_for_profile, unsafe_trust_posture, incompatible_machine, remote_only_local_first, missing_approvals.
- **external_capability/planner.py:** ActivationPlanner.plan() → PlannerResult (recommended, rejected_by_policy, not_worth_it, prerequisite_steps, resource_estimate). plan_activations() convenience.
- **external_capability/plans.py:** build_activation_plan(source_id, repo_root) → list of steps (action, detail, safe_local). Plan-only; no execution.
- **runtime_mesh/integration_registry.py:** load_integration_registry(), list_integrations(), get_integration(). Reads from data/local/runtime/integration_manifests.json (or built-in). IntegrationManifest has integration_id, enabled, install_status, etc. **No save/write** in current code — file can be written by creating/updating JSON.
- **runtime_mesh/backend_registry.py:** get_backend_status(backend_id, repo_root) for available/configured/missing/unsupported (Ollama check is read-only HTTP).
- **trust/cockpit.py:** build_trust_cockpit() → safe_to_expand, approval_registry_exists, etc.
- **mission_control:** state includes external_capabilities (recommended, blocked, plans_pending_review). No pending activation requests or execution history yet.
- **CLI:** capabilities external list | recommend | plan | blocked | explain. No request | preview | execute | disable | history.

**external_wrappers:** Not present in repo (no such package).

## 2. What is missing for real activation execution

- **Activation request model:** Structured record with activation_id, source_id, source_category, requested_action (install | enable | disable | remove | verify), prerequisites, approvals_required, expected_resource_cost, reversible, status, notes/risks. Not represented today.
- **Activation preview:** Given a request, show what would be installed/configured, which local files/configs would change, whether operator approval is required, whether the action is blocked, whether it is safe to proceed. Plan steps exist; no “preview” object or approval-gating summary.
- **Safe local executor:** No code that performs enable/disable. Integration manifests are read-only (no write path). Need: (1) enable/disable integration manifest entries (write integration_manifests.json or merge into override); (2) verify Ollama/backend availability (read-only); (3) for ollama_model sources, do not auto-pull — generate explicit instructions only.
- **Deactivation/rollback:** No disable path, no “revert config toggles,” no “mark source inactive,” no rollback history.
- **Audit/visibility:** No store for activation requests, previews, approvals checked, execution results, files/configs touched, rollback history.
- **CLI:** No request, preview, execute, disable, history commands.
- **Mission control:** No visibility for pending activation requests, blocked requests, enabled external capabilities, failed activations, rollback history.

## 3. Exact file plan

| Action | Path |
|--------|------|
| Create | `src/workflow_dataset/external_capability/activation_models.py` — ActivationRequest dataclass (activation_id, source_id, source_category, requested_action, prerequisites, approvals_required, expected_resource_cost, reversible, status, notes, risks, created_at). Requested actions: install, enable, disable, remove, verify. Status: pending, approved, blocked, executed, failed, rolled_back. |
| Create | `src/workflow_dataset/external_capability/activation_store.py` — Persist under data/local/activations/: requests (by activation_id), history (append-only log). save_request(), load_request(), list_requests(), save_execution_result(), load_history(). |
| Create | `src/workflow_dataset/external_capability/preview.py` — build_preview(request, repo_root) → what would change, files/configs affected, approval_required, blocked, safe_to_proceed, steps_summary. |
| Create | `src/workflow_dataset/external_capability/executor.py` — execute_activation(activation_id, repo_root, approved=True) → only for enable/disable of integration manifests + verify steps; for ollama_model only emit instructions. Integration manifest: add set_integration_enabled() in runtime_mesh or write integration_manifests.json from executor. disable_source(source_id) → set integration enabled=False or mark inactive in override. Rollback = disable. |
| Modify | `src/workflow_dataset/runtime_mesh/integration_registry.py` — add set_integration_enabled(integration_id, enabled, repo_root) to load, toggle, write back integration_manifests.json. |
| Create | `src/workflow_dataset/external_capability/audit.py` — record_activation_request(), record_preview(), record_execution(), record_rollback(); query pending/blocked/enabled/failed/rollback for mission_control. |
| Modify | `src/workflow_dataset/cli.py` — capabilities external request | preview | execute | disable | history. |
| Modify | `src/workflow_dataset/mission_control/state.py` — additive: pending_activation_requests, blocked_activation_requests, enabled_external_capabilities, failed_activations, rollback_history (from activation_store/audit). |
| Create | `tests/test_external_capability_executor.py` — request creation, preview generation, blocked execution, safe enable/disable, disable/rollback, audit/history. |
| Create | `docs/M24D_EXTERNAL_CAPABILITY_EXECUTOR.md` — CLI, request/preview/execute/disable/history samples, safety, what we do not do. |

## 4. Safety/risk note

- **No auto-pull:** Executor will not run `ollama pull` or any model download. For ollama_model sources, execution result will be “instructions_only” and emit the same steps as plan.
- **Approval-gated:** execute_activation() should require explicit approved=True; preview shows approval_required when applicable. Trust cockpit and approval registry remain unchanged; we only read them for preview/blocking.
- **Local config only:** Safe execution is limited to writing integration_manifests.json (enable/disable flags) and optionally external_capability_sources.json overrides. No third-party installers, no network for installs.
- **Inspectable:** All requests and results stored under data/local/activations/ with activation_id and timestamps; operator can audit.

## 5. What this phase will NOT do

- Auto-download models or run ollama pull.
- Silently enable remote/cloud behavior or any integration without an explicit request + preview + execute flow.
- Bypass trust or approval policy (executor checks policy and approval_required; execution can be blocked).
- Rewrite runtime_mesh (only additive: optional set_integration_enabled for persistence).
- Implement install of Ollama or system deps; only verify availability and toggle local manifest state.
