# M24D–M24G Local Capability Activation Block — Before Coding

## 1. Current repo state summary

- **Runtime mesh:** backend_registry (ollama, repo_local, llama_cpp), model_catalog, integration_registry (openclaw, coding_agent, ide_editor, notebook_rag) with load + **set_integration_enabled**; policy (task-class recommendation, rejection).
- **External capability (M24A/M24D):** schema (ExternalCapabilitySource: source_id, category, local, optional_remote, install_prerequisites, license/usage/security/approval/trust notes, supported_task_classes, supported_domain_pack_ids, supported_tiers, estimated_resource, activation_status, enabled); registry (load from integrations + backends + model catalog, override file); policy (apply_rejection_policy); planner (plan_activations); plans (build_activation_plan, steps only); activation_models (ActivationRequest); activation_store (save/load request, history); preview (build_preview); executor (create_activation_request, execute_activation, disable_source).
- **CLI:** capabilities external list | recommend | plan | request | preview | execute | disable | history.
- **Mission control:** external_capabilities (recommended, blocked, plans_pending_review); activation_executor (pending_activation_requests, blocked_activation_requests, enabled_external_capabilities, failed_activations, rollback_history_count).
- **Trust:** build_trust_cockpit (safe_to_expand, approval_registry_exists).
- **Onboarding, local_deployment, value_packs, acceptance:** present. **external_wrappers:** not present.

## 2. What external capability planning already exists

- Unified source registry (integrations + backends + model catalog); optional override file.
- Rejection policy (license, resource, tier, trust, domain/task).
- Activation planner (recommended, blocked, prerequisite_steps, resource_estimate).
- Activation plan steps (no execution) per source.
- Activation request model and store; preview (what would change, approval_required, blocked, safe_to_proceed).
- Safe execution: enable/disable integration manifests; verify backend; instructions_only for ollama_model.
- Disable and history; mission control visibility for pending/blocked/enabled/failed/rollback.

## 3. What is missing for a working first-draft activation subsystem

- **Source registry hardening (Phase A):** rollback/deactivation notes, explicit machine/resource requirements field, supported value packs (we have supported_domain_pack_ids), and stable/inspectable representation of lifecycle (installed vs configured vs active vs blocked vs failed).
- **Lifecycle + health (Phase C):** No single place that defines installed/configured/active/blocked/failed or runs prerequisite checks and produces a **capability health report**. Missing: failed activation diagnostics, prerequisite check status, deactivation path summary, and a `health` command/report.
- **Mission control (Phase D):** No **recommended_next_capability_action** (e.g. "run capabilities external execute --id X --approved" or "run capabilities external health").
- **CLI (Phase E):** No `capabilities external health`; no `list-requests` (optional but useful).
- **Tests/docs (Phase F):** Health and lifecycle not covered; docs not consolidated for the full block.

## 4. Exact file plan

| Phase | Action | Path |
|-------|--------|------|
| A | Modify | `external_capability/schema.py` — Add rollback_notes, machine_requirements (list[str]), supported_value_pack_ids (alias or use supported_domain_pack_ids). Extend ACTIVATION_STATUSES to include active, failed where useful. |
| A | Modify | `external_capability/registry.py` — When building sources, set activation_status from lifecycle (e.g. enabled → active; from integration manifest enabled + status). Populate rollback_notes for integrations from a constant or manifest. |
| B | (Done) | request/preview/execute/disable/history; add list-requests CLI. |
| C | Create | `external_capability/health.py` — build_capability_health(repo_root): per-source lifecycle (installed/configured/active/blocked/failed), prerequisite_checks (list of {source_id, check, passed}), failed_activations (from store), deactivation_path_available, summary counts. format_health_report(). |
| C | Create | `external_capability/lifecycle.py` — LIFECYCLE_STATES; source_lifecycle_state(source, repo_root) → installed | configured | active | blocked | failed | unknown; derive from backend status, integration enabled, activation_history. |
| D | Modify | `mission_control/state.py` — In activation_executor add recommended_next_capability_action (string). |
| D | Modify | `mission_control/report.py` — Print recommended_next_capability_action when present. |
| E | Modify | `cli.py` — capabilities external health [--repo-root] [--output]; capabilities external list-requests [--status]. |
| F | Create | `tests/test_capability_activation_block.py` — health build, lifecycle state, list_requests, health report format, mission_control recommended action. |
| F | Create | `docs/M24D_M24G_ACTIVATION_BLOCK.md` — Full block description, CLI, samples, health report sample, tests, remaining gaps. |

## 5. Safety/risk note

- No auto-download of models; executor remains instructions_only for ollama_model.
- Execution only for local manifest toggles and verify; approval required when preview says so.
- Health/lifecycle are read-only aggregates; no new execution paths that bypass policy.
- All state under data/local/activations and data/local/runtime; inspectable.

## 6. What this block will NOT do

- Auto-download large models or run ollama pull.
- Auto-enable cloud or remote behavior.
- Bypass approval/trust policy.
- Rewrite runtime mesh.
- Implement full install of Ollama or system deps (only verify presence and record state).
